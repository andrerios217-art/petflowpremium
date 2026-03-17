from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.funcionario import Funcionario
from app.schemas.funcionario import FuncionarioCreate


def create(db: Session, data: FuncionarioCreate) -> Funcionario:
    funcionario = Funcionario(
        empresa_id=data.empresa_id,
        nome=data.nome,
        cpf=data.cpf,
        email=data.email,
        telefone=data.telefone,
        funcao=data.funcao,
        crmv=data.crmv if data.funcao == "Veterinário" else None,
        senha_hash=hash_password(data.senha),
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
    )

    db.add(funcionario)
    db.commit()
    db.refresh(funcionario)
    return funcionario


def get_by_id(db: Session, funcionario_id: int):
    return db.query(Funcionario).filter(Funcionario.id == funcionario_id).first()


def get_by_email(db: Session, email: str):
    return db.query(Funcionario).filter(Funcionario.email == email).first()


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
    funcionario.email = data.get("email")
    funcionario.telefone = data.get("telefone")
    funcionario.funcao = data.get("funcao")
    funcionario.crmv = (
        (data.get("crmv") or "").strip() or None
        if data.get("funcao") == "Veterinário"
        else None
    )

    if data.get("senha"):
        funcionario.senha_hash = hash_password(data.get("senha"))

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

    db.commit()
    db.refresh(funcionario)
    return funcionario


def toggle_ativo(db: Session, funcionario: Funcionario):
    funcionario.ativo = not funcionario.ativo
    db.commit()
    db.refresh(funcionario)
    return funcionario