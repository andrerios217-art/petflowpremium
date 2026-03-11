from sqlalchemy.orm import Session
from app.models.configuracao import Configuracao


def upsert(db: Session, empresa_id: int, chave: str, valor: str):
    item = (
        db.query(Configuracao)
        .filter(Configuracao.empresa_id == empresa_id, Configuracao.chave == chave)
        .first()
    )
    if item:
        item.valor = valor
    else:
        item = Configuracao(empresa_id=empresa_id, chave=chave, valor=valor)
        db.add(item)
    db.commit()
    db.refresh(item)
    return item