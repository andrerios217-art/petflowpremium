from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import producao as crud_producao
from app.models.agendamento import Agendamento
from app.models.financeiro_receber import FinanceiroReceber
from app.schemas.producao import (
    ProducaoAvancarEtapa,
    ProducaoCardResponse,
    ProducaoHistoricoResponse,
    ProducaoIniciarEtapa,
)

router = APIRouter(prefix="/api/producao", tags=["Produção"])


def _somar_valor_agendamento(agendamento: Agendamento) -> Decimal:
    total = Decimal("0.00")

    if not agendamento or not agendamento.servicos_agendamento:
        return total

    for item in agendamento.servicos_agendamento:
        total += Decimal(str(item.preco or 0))

    return total


def _montar_descricao_financeira(agendamento: Agendamento) -> str:
    if not agendamento:
        return "Serviços petshop"

    nomes_servicos = [
        item.servico.nome
        for item in (agendamento.servicos_agendamento or [])
        if item.servico and item.servico.nome
    ]

    if nomes_servicos:
        return "Serviços: " + ", ".join(nomes_servicos)

    return "Serviços petshop"


def _gerar_conta_receber_se_nao_existir(db: Session, ordem) -> None:
    if not ordem or not ordem.finalizado:
        return

    existe = (
        db.query(FinanceiroReceber)
        .filter(
            FinanceiroReceber.origem_tipo == "PRODUCAO",
            FinanceiroReceber.origem_id == ordem.id,
        )
        .first()
    )

    if existe:
        return

    agendamento = ordem.agendamento
    if not agendamento:
        return

    valor_total = _somar_valor_agendamento(agendamento)
    if valor_total <= Decimal("0.00"):
        return

    nova_conta = FinanceiroReceber(
        empresa_id=agendamento.empresa_id,
        cliente_id=agendamento.cliente_id,
        origem_tipo="PRODUCAO",
        origem_id=ordem.id,
        descricao=_montar_descricao_financeira(agendamento),
        observacao=f"Gerado automaticamente a partir da produção #{ordem.id}",
        valor=valor_total,
        valor_pago=Decimal("0.00"),
        vencimento=date.today(),
        status="PENDENTE",
    )

    db.add(nova_conta)
    db.commit()
    db.refresh(nova_conta)
    db.refresh(ordem)


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
        "aguardando_pdv": bool(getattr(ordem, "aguardando_pdv", False)),
        "enviado_pdv": bool(getattr(ordem, "enviado_pdv", False)),
        "enviado_pdv_em": getattr(ordem, "enviado_pdv_em", None),
        "pet_nome": ag.pet.nome if ag and ag.pet else None,
        "pet_foto": getattr(ag.pet, "foto", None) if ag and ag.pet else None,
        "tutor_nome": ag.cliente.nome if ag and ag.cliente else None,
        "cliente_id": ag.cliente_id if ag else None,
        "empresa_id": ag.empresa_id if ag else None,
        "servicos": [item.servico.nome for item in ag.servicos_agendamento if item.servico] if ag else [],
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


@router.get("/prontos-pdv")
def listar_prontos_pdv(empresa_id: int, db: Session = Depends(get_db)):
    if not hasattr(crud_producao, "listar_prontos_para_pdv"):
        raise HTTPException(
            status_code=500,
            detail="O CRUD da produção ainda não implementa listar_prontos_para_pdv.",
        )

    ordens = crud_producao.listar_prontos_para_pdv(db, empresa_id)
    return [montar_card(o) for o in ordens]


@router.post("/{producao_id}/marcar-enviado-pdv")
def marcar_enviado_pdv(producao_id: int, db: Session = Depends(get_db)):
    if not hasattr(crud_producao, "marcar_enviado_pdv"):
        raise HTTPException(
            status_code=500,
            detail="O CRUD da produção ainda não implementa marcar_enviado_pdv.",
        )

    ordem = crud_producao.marcar_enviado_pdv(db, producao_id)
    return montar_card(ordem)


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

        _gerar_conta_receber_se_nao_existir(db, ordem)

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