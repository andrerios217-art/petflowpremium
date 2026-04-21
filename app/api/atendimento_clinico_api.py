from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud.atendimento_clinico import (
    adicionar_item,
    calcular_total_faturavel,
    finalizar_atendimento,
    gerar_payload_pdv,
    iniciar_atendimento,
    iniciar_por_agendamento,
    listar_itens,
    marcar_enviado_pdv,
    montar_contexto_receita_impressao,
    obter_atendimento,
    salvar_anamnese,
    salvar_prontuario,
)
from app.schemas.atendimento_clinico import (
    AtendimentoClinicoAnamneseSalvar,
    AtendimentoClinicoDetalheResponse,
    AtendimentoClinicoFinalizarResponse,
    AtendimentoClinicoItemCreate,
    AtendimentoClinicoItemResponse,
    AtendimentoClinicoIniciar,
    AtendimentoClinicoProntuarioSalvar,
    AtendimentoClinicoResponse,
)

router = APIRouter(prefix="/api/clinico", tags=["Atendimento Clínico"])
templates = Jinja2Templates(directory="app/templates")


@router.post("/iniciar", response_model=AtendimentoClinicoResponse)
def iniciar_atendimento_clinico(
    payload: AtendimentoClinicoIniciar,
    db: Session = Depends(get_db),
):
    atendimento = iniciar_atendimento(db, payload)
    return atendimento


@router.post("/iniciar-por-agendamento/{agendamento_id}", response_model=AtendimentoClinicoResponse)
def iniciar_atendimento_clinico_por_agendamento(
    agendamento_id: int,
    empresa_id: int = Query(...),
    db: Session = Depends(get_db),
):
    atendimento = iniciar_por_agendamento(db, agendamento_id, empresa_id)
    return atendimento


@router.get("/{atendimento_id}", response_model=AtendimentoClinicoDetalheResponse)
def obter_atendimento_clinico(
    atendimento_id: int,
    db: Session = Depends(get_db),
):
    atendimento = obter_atendimento(db, atendimento_id)

    return AtendimentoClinicoDetalheResponse(
        atendimento=atendimento,
        anamnese=atendimento.anamnese,
        prontuario=atendimento.prontuario,
        itens=atendimento.itens or [],
    )


@router.get("/{atendimento_id}/receita/imprimir", response_class=HTMLResponse)
def imprimir_receita_veterinaria(
    request: Request,
    atendimento_id: int,
    db: Session = Depends(get_db),
):
    contexto = montar_contexto_receita_impressao(db, atendimento_id)

    return templates.TemplateResponse(
        request,
        "receita_veterinaria.html",
        {
            "request": request,
            **contexto,
        },
    )


@router.post("/{atendimento_id}/anamnese")
def salvar_anamnese_clinica(
    atendimento_id: int,
    payload: AtendimentoClinicoAnamneseSalvar,
    db: Session = Depends(get_db),
):
    anamnese = salvar_anamnese(db, atendimento_id, payload)
    return anamnese


@router.post("/{atendimento_id}/prontuario")
def salvar_prontuario_clinico(
    atendimento_id: int,
    payload: AtendimentoClinicoProntuarioSalvar,
    db: Session = Depends(get_db),
):
    prontuario = salvar_prontuario(db, atendimento_id, payload)
    return prontuario


@router.post("/{atendimento_id}/itens", response_model=AtendimentoClinicoItemResponse)
def adicionar_item_clinico(
    atendimento_id: int,
    payload: AtendimentoClinicoItemCreate,
    db: Session = Depends(get_db),
):
    item = adicionar_item(db, atendimento_id, payload)
    return item


@router.get("/{atendimento_id}/itens", response_model=list[AtendimentoClinicoItemResponse])
def listar_itens_clinicos(
    atendimento_id: int,
    db: Session = Depends(get_db),
):
    return listar_itens(db, atendimento_id)


@router.post("/{atendimento_id}/finalizar", response_model=AtendimentoClinicoFinalizarResponse)
def finalizar_atendimento_clinico(
    atendimento_id: int,
    db: Session = Depends(get_db),
):
    atendimento = finalizar_atendimento(db, atendimento_id)
    itens = listar_itens(db, atendimento_id)
    total_faturavel = calcular_total_faturavel(db, atendimento_id)
    payload_pdv = gerar_payload_pdv(db, atendimento_id)

    return AtendimentoClinicoFinalizarResponse(
        atendimento=atendimento,
        itens=itens,
        total_faturavel=total_faturavel,
        payload_pdv=payload_pdv,
    )


@router.get("/{atendimento_id}/pdv")
def obter_payload_pdv_atendimento(
    atendimento_id: int,
    db: Session = Depends(get_db),
):
    atendimento = obter_atendimento(db, atendimento_id)
    payload = gerar_payload_pdv(db, atendimento_id)

    return {
        "atendimento_id": atendimento.id,
        "status": atendimento.status,
        "enviado_pdv": atendimento.enviado_pdv,
        "payload_pdv": payload,
    }


@router.post("/{atendimento_id}/marcar-enviado-pdv", response_model=AtendimentoClinicoResponse)
def marcar_atendimento_como_enviado_pdv(
    atendimento_id: int,
    db: Session = Depends(get_db),
):
    atendimento = marcar_enviado_pdv(db, atendimento_id)
    return atendimento