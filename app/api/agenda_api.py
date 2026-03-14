from datetime import datetime, date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.deps import get_db
from app.models.agendamento import Agendamento
from app.models.agendamento_servico import AgendamentoServico
from app.models.servico import Servico

router = APIRouter(tags=["Agenda Grooming"])


def _get_week_range(data_ref: date):
    inicio = data_ref - timedelta(days=data_ref.weekday())
    fim = inicio + timedelta(days=5)  # segunda a sábado
    return inicio, fim


@router.get("/api/agenda/semana")
def listar_agenda_semana(
    data_ref: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    try:
        if data_ref:
            data_base = datetime.strptime(data_ref, "%Y-%m-%d").date()
        else:
            data_base = date.today()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Data inválida. Use YYYY-MM-DD.",
        )

    inicio, fim = _get_week_range(data_base)

    agendamentos = (
        db.query(Agendamento)
        .join(AgendamentoServico, AgendamentoServico.agendamento_id == Agendamento.id)
        .join(Servico, Servico.id == AgendamentoServico.servico_id)
        .filter(
            and_(
                Agendamento.data >= inicio,
                Agendamento.data <= fim,
                Servico.tipo_servico == "PETSHOP",
            )
        )
        .distinct()
        .order_by(Agendamento.data.asc(), Agendamento.hora.asc())
        .all()
    )

    return agendamentos