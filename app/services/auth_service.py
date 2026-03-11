from sqlalchemy.orm import Session
from app.core.security import create_access_token, verify_password
from app.crud.usuario import get_by_email


def login(db: Session, email: str, senha: str):
    usuario = get_by_email(db, email)
    if not usuario or not verify_password(senha, usuario.senha_hash):
        return None
    token = create_access_token(str(usuario.id))
    return {"access_token": token}