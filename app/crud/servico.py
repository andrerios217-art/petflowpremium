from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.servico import Servico
from app.schemas.servico import ServicoCreate


def create(db: Session, data: ServicoCreate) -> Servico:
    servico = Servico(
        empresa_id=data.empresa_id,
        nome=data.nome,
        tipo_servico=data.tipo_servico,
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


def list_all(
    db: Session,
    q: str | None = None,
    tipo_servico: str | None = None,
):
    query = db.query(Servico).order_by(Servico.id.desc())

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Servico.nome.ilike(like),
                Servico.porte_referencia.ilike(like),
                Servico.tipo_servico.ilike(like),
            )
        )

    if tipo_servico:
        query = query.filter(Servico.tipo_servico == tipo_servico)

    return query.all()


def list_petshop(db: Session, q: str | None = None):
    return list_all(db=db, q=q, tipo_servico="PETSHOP")


def list_veterinario(db: Session, q: str | None = None):
    return list_all(db=db, q=q, tipo_servico="VETERINARIO")


def update(db: Session, servico: Servico, data: dict):
    if "nome" in data:
        servico.nome = data.get("nome")

    if "tipo_servico" in data:
        servico.tipo_servico = data.get("tipo_servico")

    if "porte_referencia" in data:
        servico.porte_referencia = data.get("porte_referencia")

    if "custo" in data:
        servico.custo = data.get("custo")

    if "venda" in data:
        servico.venda = data.get("venda")

    if "tempo_minutos" in data:
        servico.tempo_minutos = data.get("tempo_minutos")

    if "ativo" in data:
        servico.ativo = data.get("ativo")

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