from sqlalchemy.orm import Session
from app.models.configuracao import Configuracao


def get_by_chave(db: Session, empresa_id: int, chave: str):
    return (
        db.query(Configuracao)
        .filter(
            Configuracao.empresa_id == empresa_id,
            Configuracao.chave == chave,
        )
        .first()
    )


def get_valor(db: Session, empresa_id: int, chave: str, default=None):
    item = get_by_chave(db, empresa_id, chave)
    if not item:
        return default
    return item.valor


def upsert(db: Session, empresa_id: int, chave: str, valor: str):
    item = get_by_chave(db, empresa_id, chave)

    if item:
        item.valor = valor
    else:
        item = Configuracao(
            empresa_id=empresa_id,
            chave=chave,
            valor=valor,
        )
        db.add(item)

    db.commit()
    db.refresh(item)
    return item