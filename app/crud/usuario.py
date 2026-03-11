from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate


def create(db: Session, data: UsuarioCreate) -> Usuario:
    usuario = Usuario(
        empresa_id=data.empresa_id,
        nome=data.nome,
        email=data.email,
        senha_hash=hash_password(data.senha),
        tipo=data.tipo,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def get_by_email(db: Session, email: str) -> Usuario | None:
    return db.query(Usuario).filter(Usuario.email == email).first()


def list_all(db: Session):
    return db.query(Usuario).order_by(Usuario.id.desc()).all()