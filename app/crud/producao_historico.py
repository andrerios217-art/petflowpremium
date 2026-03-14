from datetime import datetime

from sqlalchemy.orm import Session

from app.models.producao_historico import ProducaoHistorico
from app.schemas.producao_historico import (
    ProducaoHistoricoCreate,
    ProducaoHistoricoUpdate,
)


def criar_historico(db: Session, historico_in: ProducaoHistoricoCreate) -> ProducaoHistorico:
    db_historico = ProducaoHistorico(**historico_in.model_dump(exclude_unset=True))

    if not db_historico.iniciado_em:
        db_historico.iniciado_em = datetime.utcnow()

    db.add(db_historico)
    db.commit()
    db.refresh(db_historico)
    return db_historico


def listar_por_producao(db: Session, producao_id: int):
    return (
        db.query(ProducaoHistorico)
        .filter(ProducaoHistorico.producao_id == producao_id)
        .order_by(ProducaoHistorico.iniciado_em.asc(), ProducaoHistorico.id.asc())
        .all()
    )


def buscar_por_id(db: Session, historico_id: int):
    return (
        db.query(ProducaoHistorico)
        .filter(ProducaoHistorico.id == historico_id)
        .first()
    )


def buscar_etapa_aberta(db: Session, producao_id: int, etapa: str):
    return (
        db.query(ProducaoHistorico)
        .filter(
            ProducaoHistorico.producao_id == producao_id,
            ProducaoHistorico.etapa == etapa,
            ProducaoHistorico.finalizado_em.is_(None),
        )
        .order_by(ProducaoHistorico.iniciado_em.desc(), ProducaoHistorico.id.desc())
        .first()
    )


def atualizar_historico(
    db: Session,
    db_historico: ProducaoHistorico,
    historico_in: ProducaoHistoricoUpdate,
) -> ProducaoHistorico:
    dados_update = historico_in.model_dump(exclude_unset=True)

    for campo, valor in dados_update.items():
        setattr(db_historico, campo, valor)

    if db_historico.iniciado_em and db_historico.finalizado_em:
        delta = db_historico.finalizado_em - db_historico.iniciado_em
        db_historico.tempo_gasto_minutos = int(delta.total_seconds() // 60)

    db.commit()
    db.refresh(db_historico)
    return db_historico


def finalizar_historico(
    db: Session,
    db_historico: ProducaoHistorico,
    finalizado_em: datetime | None = None,
    intercorrencia: str | None = None,
    observacoes: str | None = None,
) -> ProducaoHistorico:
    db_historico.finalizado_em = finalizado_em or datetime.utcnow()
    db_historico.status = "FINALIZADO"

    if intercorrencia is not None:
        db_historico.intercorrencia = intercorrencia

    if observacoes is not None:
        db_historico.observacoes = observacoes

    if db_historico.iniciado_em and db_historico.finalizado_em:
        delta = db_historico.finalizado_em - db_historico.iniciado_em
        db_historico.tempo_gasto_minutos = int(delta.total_seconds() // 60)

    db.commit()
    db.refresh(db_historico)
    return db_historico