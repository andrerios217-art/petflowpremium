from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.funcionario import Funcionario
from app.models.usuario import Usuario
from app.schemas.funcionario import FuncionarioCreate


def _normalizar_email(email: str | None) -> str:
    return (email or "").strip().lower()


def _tipo_usuario_por_funcao(funcao: str) -> str:
    if funcao == "Gerente":
        return "gerente"
    return "funcionario"


def _sync_usuario_from_funcionario(
    db: Session,
    *,
    empresa_id: int,
    nome: str,
    email: str,
    senha_hash: str | None,
    funcao: str,
    ativo: bool,
    acesso_pdv: bool,
):
    email_normalizado = _normalizar_email(email)

    usuario = db.query(Usuario).filter(func.lower(Usuario.email) == email_normalizado).first()

    if usuario:
        usuario.empresa_id = empresa_id
        usuario.nome = nome
        usuario.email = email_normalizado
        usuario.tipo = _tipo_usuario_por_funcao(funcao)
        usuario.ativo = ativo
        usuario.pode_pdv = acesso_pdv

        if senha_hash:
            usuario.senha_hash = senha_hash

        return usuario

    usuario = Usuario(
        empresa_id=empresa_id,
        nome=nome,
        email=email_normalizado,
        senha_hash=senha_hash or hash_password("1234"),
        tipo=_tipo_usuario_por_funcao(funcao),
        ativo=ativo,
        pode_pdv=acesso_pdv,
    )
    db.add(usuario)
    return usuario


def create(db: Session, data: FuncionarioCreate) -> Funcionario:
    senha_hash = hash_password(data.senha)
    email_normalizado = _normalizar_email(data.email)

    funcionario = Funcionario(
        empresa_id=data.empresa_id,
        nome=data.nome,
        cpf=data.cpf,
        email=email_normalizado,
        telefone=data.telefone,
        funcao=data.funcao,
        crmv=data.crmv if data.funcao == "Veterinário" else None,
        senha_hash=senha_hash,
        acesso_dashboard=data.acesso_dashboard,
        acesso_clientes=data.acesso_clientes,
        acesso_pets=data.acesso_pets,
        acesso_servicos=data.acesso_servicos,
        acesso_funcionarios=data.acesso_funcionarios,
        acesso_agenda=data.acesso_agenda,
        acesso_producao=data.acesso_producao,
        acesso_estoque=data.acesso_estoque,
        acesso_financeiro=data.acesso_financeiro,
        acesso_crm=data.acesso_crm,
        acesso_relatorios=data.acesso_relatorios,
        acesso_configuracoes=data.acesso_configuracoes,
        acesso_pdv=data.acesso_pdv,
    )

    db.add(funcionario)

    _sync_usuario_from_funcionario(
        db,
        empresa_id=data.empresa_id,
        nome=data.nome,
        email=email_normalizado,
        senha_hash=senha_hash,
        funcao=data.funcao,
        ativo=True,
        acesso_pdv=data.acesso_pdv,
    )

    db.commit()
    db.refresh(funcionario)
    return funcionario


def get_by_id(db: Session, funcionario_id: int):
    return db.query(Funcionario).filter(Funcionario.id == funcionario_id).first()


def get_by_email(db: Session, email: str):
    email = _normalizar_email(email)
    return db.query(Funcionario).filter(func.lower(Funcionario.email) == email).first()


def list_all(db: Session, q: str | None = None):
    query = db.query(Funcionario).order_by(Funcionario.id.desc())

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Funcionario.nome.ilike(like),
                Funcionario.cpf.ilike(like),
                Funcionario.email.ilike(like),
                Funcionario.telefone.ilike(like),
                Funcionario.funcao.ilike(like),
                Funcionario.crmv.ilike(like),
            )
        )

    return query.all()


def update(db: Session, funcionario: Funcionario, data: dict):
    funcionario.nome = data.get("nome")
    funcionario.cpf = data.get("cpf", funcionario.cpf)
    funcionario.email = _normalizar_email(data.get("email"))
    funcionario.telefone = data.get("telefone")
    funcionario.funcao = data.get("funcao")
    funcionario.crmv = (
        (data.get("crmv") or "").strip() or None
        if data.get("funcao") == "Veterinário"
        else None
    )

    nova_senha_hash = None
    if data.get("senha"):
        nova_senha_hash = hash_password(data.get("senha"))
        funcionario.senha_hash = nova_senha_hash

    funcionario.acesso_dashboard = data.get("acesso_dashboard", False)
    funcionario.acesso_clientes = data.get("acesso_clientes", False)
    funcionario.acesso_pets = data.get("acesso_pets", False)
    funcionario.acesso_servicos = data.get("acesso_servicos", False)
    funcionario.acesso_funcionarios = data.get("acesso_funcionarios", False)
    funcionario.acesso_agenda = data.get("acesso_agenda", False)
    funcionario.acesso_producao = data.get("acesso_producao", False)
    funcionario.acesso_estoque = data.get("acesso_estoque", False)
    funcionario.acesso_financeiro = data.get("acesso_financeiro", False)
    funcionario.acesso_crm = data.get("acesso_crm", False)
    funcionario.acesso_relatorios = data.get("acesso_relatorios", False)
    funcionario.acesso_configuracoes = data.get("acesso_configuracoes", False)
    funcionario.acesso_pdv = data.get("acesso_pdv", False)

    _sync_usuario_from_funcionario(
        db,
        empresa_id=funcionario.empresa_id,
        nome=funcionario.nome,
        email=funcionario.email,
        senha_hash=nova_senha_hash,
        funcao=funcionario.funcao,
        ativo=funcionario.ativo,
        acesso_pdv=funcionario.acesso_pdv,
    )

    db.commit()
    db.refresh(funcionario)
    return funcionario


def toggle_ativo(db: Session, funcionario: Funcionario):
    funcionario.ativo = not funcionario.ativo

    _sync_usuario_from_funcionario(
        db,
        empresa_id=funcionario.empresa_id,
        nome=funcionario.nome,
        email=funcionario.email,
        senha_hash=None,
        funcao=funcionario.funcao,
        ativo=funcionario.ativo,
        acesso_pdv=funcionario.acesso_pdv,
    )

    db.commit()
    db.refresh(funcionario)
    return funcionario