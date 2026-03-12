from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.servico import Servico
from app.schemas.servico import ServicoCreate


def create(db: Session, data: ServicoCreate) -> Servico:
    servico = Servico(
        empresa_id=data.empresa_id,
        nome=data.nome,
        porte_referencia=data.porte_referencia,
        custo=data.custo,
        venda=data.venda,
        tempo_minutos=data.tempo_minutos,
    )
    db.add(servico)
    db.commit()
    db.refresh(servico)
    return servico


def get_by_id(db: Session, servico_id: int):
    return db.query(Servico).filter(Servico.id == servico_id).first()


def list_all(db: Session, q: str | None = None):
    query = db.query(Servico).order_by(Servico.id.desc())

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Servico.nome.ilike(like),
                Servico.porte_referencia.ilike(like),
            )
        )

    return query.all()


def update(db: Session, servico: Servico, data: dict):
    servico.nome = data.get("nome")
    servico.porte_referencia = data.get("porte_referencia")
    servico.custo = data.get("custo")
    servico.venda = data.get("venda")
    servico.tempo_minutos = data.get("tempo_minutos")
    db.commit()
    db.refresh(servico)
    return servico


def toggle_ativo(db: Session, servico: Servico):
    servico.ativo = not servico.ativo
    db.commit()
    db.refresh(servico)
    return servico


def delete(db: Session, servico: Servico):
    db.delete(servico)
    db.commit()