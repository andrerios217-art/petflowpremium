from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import producao as crud_producao
from app.models.agendamento import Agendamento
from app.schemas.producao import (
    ProducaoAvancarEtapa,
    ProducaoCardResponse,
    ProducaoHistoricoResponse,
    ProducaoIniciarEtapa,
)

router = APIRouter(prefix="/api/producao", tags=["Produção"])


def montar_card(ordem):
    ag = ordem.agendamento

    return {
        "id": ordem.id,
        "agendamento_id": ordem.agendamento_id,
        "coluna": ordem.coluna,
        "etapa_status": ordem.etapa_status,
        "prioridade": ordem.prioridade,
        "funcionario_id": ordem.funcionario_id,
        "secagem_tempo": ordem.secagem_tempo,
        "secagem_inicio": ordem.secagem_inicio,
        "finalizado": ordem.finalizado,
        "pet_nome": ag.pet.nome if ag and ag.pet else None,
        "pet_foto": getattr(ag.pet, "foto", None) if ag and ag.pet else None,
        "tutor_nome": ag.cliente.nome if ag and ag.cliente else None,
        "servicos": [item.servico.nome for item in ag.servicos_agendamento if item.servico],
        "funcionario_nome": ordem.funcionario.nome if ordem.funcionario else None,
        "status_agendamento": ag.status if ag else None,
        "observacoes": ordem.observacoes,
        "intercorrencias": ordem.intercorrencias,
        "proximo_destino_automatico": crud_producao.proximo_destino_preview(ordem),
    }


@router.get("/", response_model=list[ProducaoCardResponse])
def listar_producao(empresa_id: int, db: Session = Depends(get_db)):
    ordens = crud_producao.listar_cards(db, empresa_id)
    return [montar_card(o) for o in ordens]


@router.post("/criar-por-agendamento/{agendamento_id}", response_model=ProducaoCardResponse)
def criar_por_agendamento(agendamento_id: int, db: Session = Depends(get_db)):
    agendamento = (
        db.query(Agendamento)
        .filter(Agendamento.id == agendamento_id)
        .first()
    )

    if not agendamento:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")

    ordem = crud_producao.criar_ordem_se_nao_existir(db, agendamento)

    if not ordem:
        raise HTTPException(status_code=400, detail="Não foi possível criar a ordem de produção.")

    return montar_card(ordem)


@router.post("/{producao_id}/iniciar", response_model=ProducaoCardResponse)
def iniciar_etapa(
    producao_id: int,
    payload: ProducaoIniciarEtapa,
    db: Session = Depends(get_db)
):
    ordem = crud_producao.buscar_por_id(db, producao_id)

    if not ordem:
        raise HTTPException(status_code=404, detail="Card de produção não encontrado.")

    try:
        ordem = crud_producao.iniciar_etapa(db, ordem, payload.funcionario_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not ordem:
        raise HTTPException(status_code=400, detail="Não foi possível iniciar a etapa.")

    return montar_card(ordem)


@router.post("/{producao_id}/proximo", response_model=ProducaoCardResponse)
def avancar_para_proxima_etapa(
    producao_id: int,
    payload: ProducaoAvancarEtapa,
    db: Session = Depends(get_db)
):
    ordem = crud_producao.buscar_por_id(db, producao_id)

    if not ordem:
        raise HTTPException(status_code=404, detail="Card de produção não encontrado.")

    try:
        ordem = crud_producao.mover_para_proxima_etapa(
            db=db,
            ordem=ordem,
            funcionario_id=payload.funcionario_id,
            usar_secagem=payload.usar_secagem,
            secagem_tempo=payload.secagem_tempo,
            intercorrencias=payload.intercorrencias,
            descricao_intercorrencia=payload.descricao_intercorrencia,
            observacoes_gerais=payload.observacoes_gerais,
        )

        if not ordem:
            raise HTTPException(status_code=400, detail="Não foi possível avançar a etapa.")

        return montar_card(ordem)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{producao_id}/historico", response_model=ProducaoHistoricoResponse)
def historico_producao(
    producao_id: int,
    db: Session = Depends(get_db)
):
    ordem = crud_producao.buscar_por_id(db, producao_id)

    if not ordem:
        raise HTTPException(status_code=404, detail="Produção não encontrada.")

    historico_ordenado = sorted(
        ordem.historicos or [],
        key=lambda h: (
            h.iniciado_em is None,
            h.iniciado_em,
            h.id,
        )
    )

    historico = []

    for h in historico_ordenado:
        historico.append({
            "etapa": h.etapa,
            "status": h.status,
            "funcionario_id": h.funcionario_id,
            "funcionario_nome": h.funcionario.nome if h.funcionario else None,
            "inicio": h.iniciado_em,
            "fim": h.finalizado_em,
            "tempo_minutos": h.tempo_gasto_minutos,
            "intercorrencia": h.intercorrencia,
            "observacoes": h.observacoes,
        })

    return {
        "producao_id": ordem.id,
        "historico": historico,
    }