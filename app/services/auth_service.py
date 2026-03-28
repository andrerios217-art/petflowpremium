from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.crud.usuario import get_by_email as get_usuario_by_email
from app.crud.funcionario import get_by_email as get_funcionario_by_email


def login(db: Session, email: str, senha: str):
    email = (email or "").strip().lower()
    senha = senha or ""

    usuario = get_usuario_by_email(db, email)
    if usuario and getattr(usuario, "senha_hash", None) and verify_password(senha, usuario.senha_hash):
        token = create_access_token(str(usuario.id))
        return {
            "access_token": token,
            "tipo_usuario": "admin",
            "nome": usuario.nome
        }

    funcionario = get_funcionario_by_email(db, email)
    if (
        funcionario
        and funcionario.ativo
        and getattr(funcionario, "senha_hash", None)
        and verify_password(senha, funcionario.senha_hash)
    ):
        token = create_access_token(f"funcionario:{funcionario.id}")
        return {
            "access_token": token,
            "tipo_usuario": "funcionario",
            "nome": funcionario.nome,
            "permissoes": {
                "dashboard": funcionario.acesso_dashboard,
                "clientes": funcionario.acesso_clientes,
                "pets": funcionario.acesso_pets,
                "servicos": funcionario.acesso_servicos,
                "funcionarios": funcionario.acesso_funcionarios,
                "agenda": funcionario.acesso_agenda,
                "producao": funcionario.acesso_producao,
                "estoque": funcionario.acesso_estoque,
                "financeiro": funcionario.acesso_financeiro,
                "crm": funcionario.acesso_crm,
                "relatorios": funcionario.acesso_relatorios,
                "configuracoes": funcionario.acesso_configuracoes,
            }
        }

    return None