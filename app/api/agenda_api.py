from datetime import datetime, date, timedelta
from typing import Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.deps import get_db
from app.models.agendamento import Agendamento
from app.models.agendamento_servico import AgendamentoServico
from app.models.servico import Servico
from app.models.producao import Producao
from app.crud import producao as crud_producao

router = APIRouter(tags=["Agenda Grooming"])


def _get_week_range(data_ref: date):
    inicio = data_ref - timedelta(days=data_ref.weekday())
    fim = inicio + timedelta(days=5)
    return inicio, fim


def _format_time_value(value: Any) -> Optional[str]:
    if value is None:
        return None

    if hasattr(value, "strftime"):
        try:
            return value.strftime("%H:%M")
        except Exception:
            return str(value)

    texto = str(value)
    return texto[:5] if len(texto) >= 5 else texto


def _get_attr_safe(obj: Any, attr: str, default=None):
    try:
        return getattr(obj, attr, default)
    except Exception:
        return default


def _obter_intercorrencias_agendamento(db: Session, agendamento: Agendamento):
    intercorrencias_agendamento = _get_attr_safe(agendamento, "intercorrencias")

    if intercorrencias_agendamento:
        return intercorrencias_agendamento

    producao = (
        db.query(Producao)
        .filter(Producao.agendamento_id == agendamento.id)
        .first()
    )

    if producao and producao.intercorrencias:
        return producao.intercorrencias

    return None


def _serialize_agendamento(db: Session, agendamento: Agendamento):
    servicos_rows = (
        db.query(AgendamentoServico, Servico)
        .join(Servico, Servico.id == AgendamentoServico.servico_id)
        .filter(AgendamentoServico.agendamento_id == agendamento.id)
        .all()
    )

    servicos = []
    for ag_servico, servico in servicos_rows:
        servicos.append(
            {
                "servico_id": servico.id,
                "nome": servico.nome,
                "tipo_servico": servico.tipo_servico,
                "porte_referencia": servico.porte_referencia,
                "preco": _get_attr_safe(ag_servico, "preco"),
                "tempo_previsto": _get_attr_safe(ag_servico, "tempo_previsto"),
            }
        )

    cliente = _get_attr_safe(agendamento, "cliente")
    pet = _get_attr_safe(agendamento, "pet")
    funcionario = _get_attr_safe(agendamento, "funcionario")
    intercorrencias = _obter_intercorrencias_agendamento(db, agendamento)

    return {
        "id": agendamento.id,
        "empresa_id": _get_attr_safe(agendamento, "empresa_id"),
        "cliente_id": _get_attr_safe(agendamento, "cliente_id"),
        "cliente_nome": _get_attr_safe(cliente, "nome"),
        "pet_id": _get_attr_safe(agendamento, "pet_id"),
        "pet_nome": _get_attr_safe(pet, "nome"),
        "funcionario_id": _get_attr_safe(agendamento, "funcionario_id"),
        "funcionario_nome": _get_attr_safe(funcionario, "nome"),
        "data": str(_get_attr_safe(agendamento, "data") or ""),
        "hora": _format_time_value(_get_attr_safe(agendamento, "hora")),
        "status": _get_attr_safe(agendamento, "status", "AGUARDANDO"),
        "prioridade": _get_attr_safe(agendamento, "prioridade", "NORMAL"),
        "observacoes": _get_attr_safe(agendamento, "observacoes"),
        "tem_intercorrencia": _get_attr_safe(agendamento, "tem_intercorrencia", False),
        "intercorrencias": intercorrencias,
        "servicos": servicos,
    }


def _parse_data_ref(
    data_ref: Optional[str],
    data_inicio: Optional[str],
) -> date:
    valor = data_ref or data_inicio

    if not valor:
        return date.today()

    try:
        return datetime.strptime(valor, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Data inválida. Use YYYY-MM-DD.",
        )


def _buscar_agendamento_grooming(db: Session, agendamento_id: int) -> Agendamento:
    agendamento = (
        db.query(Agendamento)
        .filter(Agendamento.id == agendamento_id)
        .first()
    )

    if not agendamento:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")

    servicos_petshop = (
        db.query(AgendamentoServico, Servico)
        .join(Servico, Servico.id == AgendamentoServico.servico_id)
        .filter(
            AgendamentoServico.agendamento_id == agendamento_id,
            Servico.tipo_servico == "PETSHOP",
        )
        .all()
    )

    if not servicos_petshop:
        raise HTTPException(
            status_code=404,
            detail="Agendamento não encontrado na agenda de banho e tosa."
        )

    return agendamento


def _validar_servicos_petshop(db: Session, servicos_payload: list):
    if not servicos_payload:
        raise HTTPException(status_code=400, detail="Informe ao menos um serviço.")

    servico_ids = []
    for item in servicos_payload:
        servico_id = item.get("servico_id")
        if not servico_id:
            raise HTTPException(status_code=400, detail="Serviço inválido.")
        servico_ids.append(servico_id)

    servicos_db = (
        db.query(Servico)
        .filter(Servico.id.in_(servico_ids))
        .all()
    )

    if len(servicos_db) != len(servico_ids):
        raise HTTPException(status_code=400, detail="Um ou mais serviços não foram encontrados.")

    for servico in servicos_db:
        if str(servico.tipo_servico or "").upper() != "PETSHOP":
            raise HTTPException(
                status_code=400,
                detail=f"O serviço '{servico.nome}' não pertence à agenda de banho e tosa."
            )

    return servicos_db


def _parse_data_hora(data_str: Optional[str], hora_str: Optional[str]):
    if not data_str:
        raise HTTPException(status_code=400, detail="Data é obrigatória.")

    if not hora_str:
        raise HTTPException(status_code=400, detail="Hora é obrigatória.")

    try:
        data_obj = datetime.strptime(data_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Data inválida. Use YYYY-MM-DD.")

    try:
        hora_obj = datetime.strptime(hora_str, "%H:%M").time()
    except ValueError:
        raise HTTPException(status_code=400, detail="Hora inválida. Use HH:MM.")

    return data_obj, hora_obj


@router.get("/api/agenda/semana")
def listar_agenda_semana(
    data_ref: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    empresa_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    data_base = _parse_data_ref(data_ref, data_inicio)
    inicio, fim = _get_week_range(data_base)

    if data_inicio and data_fim:
        try:
            inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
            fim = datetime.strptime(data_fim, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Data inválida. Use YYYY-MM-DD.",
            )

    query = (
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
    )

    if empresa_id is not None and hasattr(Agendamento, "empresa_id"):
        query = query.filter(Agendamento.empresa_id == empresa_id)

    agendamentos = query.all()
    return [_serialize_agendamento(db, item) for item in agendamentos]


@router.get("/api/agenda/{agendamento_id}")
def detalhar_agendamento(
    agendamento_id: int,
    db: Session = Depends(get_db),
):
    agendamento = _buscar_agendamento_grooming(db, agendamento_id)
    return _serialize_agendamento(db, agendamento)


@router.post("/api/agenda")
@router.post("/api/agenda/")
def criar_agendamento(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
):
    cliente_id = payload.get("cliente_id")
    pet_id = payload.get("pet_id")
    funcionario_id = payload.get("funcionario_id")
    empresa_id = payload.get("empresa_id")
    data_str = payload.get("data")
    hora_str = payload.get("hora")
    prioridade = payload.get("prioridade") or "NORMAL"
    observacoes = payload.get("observacoes")
    servicos_payload = payload.get("servicos") or []

    if not cliente_id:
        raise HTTPException(status_code=400, detail="Cliente é obrigatório.")

    if not pet_id:
        raise HTTPException(status_code=400, detail="Pet é obrigatório.")

    data_obj, hora_obj = _parse_data_hora(data_str, hora_str)
    _validar_servicos_petshop(db, servicos_payload)

    dados_agendamento = {}

    if hasattr(Agendamento, "empresa_id"):
        dados_agendamento["empresa_id"] = empresa_id

    if hasattr(Agendamento, "cliente_id"):
        dados_agendamento["cliente_id"] = cliente_id

    if hasattr(Agendamento, "pet_id"):
        dados_agendamento["pet_id"] = pet_id

    if hasattr(Agendamento, "funcionario_id"):
        dados_agendamento["funcionario_id"] = funcionario_id

    if hasattr(Agendamento, "data"):
        dados_agendamento["data"] = data_obj

    if hasattr(Agendamento, "hora"):
        dados_agendamento["hora"] = hora_obj

    if hasattr(Agendamento, "prioridade"):
        dados_agendamento["prioridade"] = prioridade

    if hasattr(Agendamento, "observacoes"):
        dados_agendamento["observacoes"] = observacoes

    if hasattr(Agendamento, "status"):
        dados_agendamento["status"] = "AGUARDANDO"

    novo_agendamento = Agendamento(**dados_agendamento)

    try:
        db.add(novo_agendamento)
        db.flush()

        for item in servicos_payload:
            preco = item.get("preco", 0)
            tempo_previsto = item.get("tempo_previsto", 0)

            agendamento_servico = AgendamentoServico(
                agendamento_id=novo_agendamento.id,
                servico_id=item["servico_id"],
                preco=preco if preco is not None else 0,
                tempo_previsto=tempo_previsto if tempo_previsto is not None else 0,
            )
            db.add(agendamento_servico)

        db.commit()
        db.refresh(novo_agendamento)

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao salvar agendamento: {str(error)}"
        )

    try:
        crud_producao.criar_ordem_se_nao_existir(
            db=db,
            agendamento=novo_agendamento,
            commit=True,
        )
    except Exception as error:
        return {
            "warning": f"Agendamento salvo, mas houve falha ao enviar para produção: {str(error)}",
            "agendamento": _serialize_agendamento(db, novo_agendamento),
        }

    return _serialize_agendamento(db, novo_agendamento)


@router.put("/api/agenda/{agendamento_id}")
def editar_agendamento(
    agendamento_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
):
    agendamento = _buscar_agendamento_grooming(db, agendamento_id)

    funcionario_id = payload.get("funcionario_id")
    data_str = payload.get("data")
    hora_str = payload.get("hora")
    prioridade = payload.get("prioridade") or "NORMAL"
    observacoes = payload.get("observacoes")
    servicos_payload = payload.get("servicos") or []

    data_obj, hora_obj = _parse_data_hora(data_str, hora_str)
    _validar_servicos_petshop(db, servicos_payload)

    if hasattr(agendamento, "funcionario_id"):
        agendamento.funcionario_id = funcionario_id

    if hasattr(agendamento, "data"):
        agendamento.data = data_obj

    if hasattr(agendamento, "hora"):
        agendamento.hora = hora_obj

    if hasattr(agendamento, "prioridade"):
        agendamento.prioridade = prioridade

    if hasattr(agendamento, "observacoes"):
        agendamento.observacoes = observacoes

    try:
        (
            db.query(AgendamentoServico)
            .filter(AgendamentoServico.agendamento_id == agendamento.id)
            .delete(synchronize_session=False)
        )

        for item in servicos_payload:
            preco = item.get("preco", 0)
            tempo_previsto = item.get("tempo_previsto", 0)

            agendamento_servico = AgendamentoServico(
                agendamento_id=agendamento.id,
                servico_id=item["servico_id"],
                preco=preco if preco is not None else 0,
                tempo_previsto=tempo_previsto if tempo_previsto is not None else 0,
            )
            db.add(agendamento_servico)

        db.add(agendamento)
        db.commit()
        db.refresh(agendamento)
    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao atualizar agendamento: {str(error)}"
        )

    return _serialize_agendamento(db, agendamento)


@router.delete("/api/agenda/{agendamento_id}")
def excluir_agendamento(
    agendamento_id: int,
    db: Session = Depends(get_db),
):
    agendamento = _buscar_agendamento_grooming(db, agendamento_id)

    try:
        producao = (
            db.query(Producao)
            .filter(Producao.agendamento_id == agendamento.id)
            .first()
        )
        if producao:
            db.delete(producao)
            db.flush()

        (
            db.query(AgendamentoServico)
            .filter(AgendamentoServico.agendamento_id == agendamento.id)
            .delete(synchronize_session=False)
        )
        db.delete(agendamento)
        db.commit()
    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao excluir agendamento: {str(error)}"
        )

    return {"message": "Agendamento excluído com sucesso."}


@router.put("/api/agenda/{agendamento_id}/status")
def alterar_status_agendamento(
    agendamento_id: int,
    status: str = Query(...),
    db: Session = Depends(get_db),
):
    agendamento = _buscar_agendamento_grooming(db, agendamento_id)

    status_normalizado = str(status or "").strip().upper()
    status_validos = {
        "AGUARDANDO",
        "EM_ATENDIMENTO",
        "FINALIZADO",
        "FALTA",
        "CANCELADO",
    }

    if status_normalizado not in status_validos:
        raise HTTPException(
            status_code=400,
            detail="Status inválido para o agendamento."
        )

    if hasattr(agendamento, "status"):
        agendamento.status = status_normalizado

    try:
        db.add(agendamento)
        db.commit()
        db.refresh(agendamento)
    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao alterar status do agendamento: {str(error)}"
        )

    return _serialize_agendamento(db, agendamento)