from sqlalchemy.orm import Session

from app.models.empresa import Empresa
from app.schemas.empresa import EmpresaCreate


def list_all(db: Session) -> list[Empresa]:
    return db.query(Empresa).order_by(Empresa.id.asc()).all()


def get_by_id(db: Session, empresa_id: int) -> Empresa | None:
    return db.query(Empresa).filter(Empresa.id == empresa_id).first()


def create(db: Session, payload: EmpresaCreate) -> Empresa:
    empresa = Empresa(
        nome=payload.nome,
        cnpj=payload.cnpj,
        logo_url=payload.logo_url,
        ativa=True,
    )
    db.add(empresa)
    db.commit()
    db.refresh(empresa)
    return empresa


def update(db: Session, empresa: Empresa, payload: EmpresaCreate) -> Empresa:
    empresa.nome = payload.nome
    empresa.cnpj = payload.cnpj
    empresa.logo_url = payload.logo_url
    db.commit()
    db.refresh(empresa)
    return empresa


def update_logo_url(db: Session, empresa: Empresa, logo_url: str | None) -> Empresa:
    empresa.logo_url = logo_url
    db.commit()
    db.refresh(empresa)
    return empresa