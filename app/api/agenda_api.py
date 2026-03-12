from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import agendamento as agendamento_crud
from app.crud import producao as producao_crud
from app.schemas.agendamento import AgendamentoCreate, AgendamentoOut, AgendamentoUpdate

router = APIRouter(prefix="/api/agenda", tags=["Agenda"])

STATUS_VALIDOS = {
    "AGUARDANDO",
    "EM_ATENDIMENTO",
    "FINALIZADO",
    "FALTA",
    "CANCELADO",
}


@router.get("/semana", response_model=list[AgendamentoOut])
def listar_semana(
    empresa_id: int,
    data_inicio: str,
    data_fim: str,
    db: Session = Depends(get_db)
):
    return agendamento_crud.list_semana(db, empresa_id, data_inicio, data_fim)


@router.post("/", response_model=AgendamentoOut)
def criar(data: AgendamentoCreate, db: Session = Depends(get_db)):
    ag = agendamento_crud.create(db, data)

    if isinstance(ag, dict) and ag.get("error"):
        raise HTTPException(status_code=400, detail=ag["error"])

    return ag


@router.get("/{agendamento_id}", response_model=AgendamentoOut)
def buscar(agendamento_id: int, db: Session = Depends(get_db)):
    ag = agendamento_crud.get_by_id(db, agendamento_id)

    if not ag:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    return ag


@router.put("/{agendamento_id}", response_model=AgendamentoOut)
def atualizar(
    agendamento_id: int,
    data: AgendamentoUpdate,
    db: Session = Depends(get_db)
):
    ag = agendamento_crud.update(db, agendamento_id, data)

    if ag is None:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    if isinstance(ag, dict) and ag.get("error"):
        raise HTTPException(status_code=400, detail=ag["error"])

    return ag


@router.put("/{agendamento_id}/status", response_model=AgendamentoOut)
def alterar_status(
    agendamento_id: int,
    status: str = Query(...),
    db: Session = Depends(get_db)
):
    status = (status or "").strip().upper()

    if status not in STATUS_VALIDOS:
        raise HTTPException(status_code=400, detail="Status inválido.")

    ag = agendamento_crud.alterar_status(db, agendamento_id, status)

    if ag is None:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    if ag is False:
        raise HTTPException(status_code=400, detail="Transição de status não permitida.")

    if status == "EM_ATENDIMENTO":
        agendamento_model = agendamento_crud.get_model_by_id(db, agendamento_id)
        if agendamento_model:
            producao_crud.criar_ordem_se_nao_existir(db, agendamento_model)

    return ag


@router.delete("/{agendamento_id}")
def excluir(agendamento_id: int, db: Session = Depends(get_db)):
    ok = agendamento_crud.delete(db, agendamento_id)

    if ok is None:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    if ok is False:
        raise HTTPException(
            status_code=400,
            detail="Só é possível excluir agendamentos AGUARDANDO"
        )

    return {"success": True}