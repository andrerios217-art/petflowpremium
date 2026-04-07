from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import extract
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_db
from app.models.financeiro_pagar import FinanceiroPagar
from app.models.financeiro_plano_dre import FinanceiroPlanoDRE
from app.schemas.financeiro import (
    FinanceiroPagarBaixa,
    FinanceiroPagarCreate,
    FinanceiroPagarListOut,
    FinanceiroPagarOut,
)

router = APIRouter(prefix="/api/financeiro/pagar", tags=["Financeiro - Pagar"])


def _serializar(conta: FinanceiroPagar):
    return {
        "id": conta.id,
        "empresa_id": conta.empresa_id,
        "fornecedor": conta.fornecedor,
        "origem_tipo": conta.origem_tipo,
        "origem_id": conta.origem_id,
        "descricao": conta.descricao,
        "observacao": conta.observacao,
        "classificacao_dre_id": conta.classificacao_dre_id,
        "grupo_dre": conta.grupo_dre,
        "categoria_dre": conta.categoria_dre,
        "subcategoria_dre": conta.subcategoria_dre,
        "valor": float(conta.valor or 0),
        "valor_pago": float(conta.valor_pago or 0),
        "vencimento": conta.vencimento.isoformat() if conta.vencimento else None,
        "data_pagamento": conta.data_pagamento.isoformat() if conta.data_pagamento else None,
        "status": conta.status,
        "status_atual": conta.status_atual,
        "esta_vencido": conta.esta_vencido,
        "created_at": conta.created_at.isoformat() if conta.created_at else None,
        "updated_at": conta.updated_at.isoformat() if conta.updated_at else None,
    }


def _buscar_classificacao_valida(
    db: Session,
    empresa_id: int,
    classificacao_dre_id: int | None,
) -> FinanceiroPlanoDRE | None:
    if not classificacao_dre_id:
        return None

    classificacao = (
        db.query(FinanceiroPlanoDRE)
        .filter(
            FinanceiroPlanoDRE.id == classificacao_dre_id,
            FinanceiroPlanoDRE.empresa_id == empresa_id,
        )
        .first()
    )

    if not classificacao:
        raise HTTPException(
            status_code=404,
            detail="Classificação DRE não encontrada para esta empresa.",
        )

    if not classificacao.ativo:
        raise HTTPException(
            status_code=400,
            detail="Classificação DRE inativa.",
        )

    return classificacao


@router.post("/", response_model=FinanceiroPagarOut)
def criar_conta_pagar(
    payload: FinanceiroPagarCreate,
    db: Session = Depends(get_db),
):
    _buscar_classificacao_valida(
        db=db,
        empresa_id=payload.empresa_id,
        classificacao_dre_id=payload.classificacao_dre_id,
    )

    conta = FinanceiroPagar(
        empresa_id=payload.empresa_id,
        fornecedor=payload.fornecedor,
        origem_tipo=payload.origem_tipo,
        origem_id=payload.origem_id,
        descricao=payload.descricao,
        observacao=payload.observacao,
        classificacao_dre_id=payload.classificacao_dre_id,
        valor=Decimal(payload.valor),
        valor_pago=Decimal("0.00"),
        vencimento=payload.vencimento,
        status="PENDENTE",
    )

    db.add(conta)
    db.commit()
    db.refresh(conta)

    conta = (
        db.query(FinanceiroPagar)
        .options(joinedload(FinanceiroPagar.classificacao_dre))
        .filter(FinanceiroPagar.id == conta.id)
        .first()
    )

    return _serializar(conta)


@router.get("/", response_model=FinanceiroPagarListOut)
def listar_contas_pagar(
    empresa_id: int = Query(..., ge=1),
    mes: int | None = Query(None, ge=1, le=12),
    ano: int | None = Query(None, ge=2000, le=2100),
    classificacao_dre_id: int | None = Query(None, ge=1),
    grupo_dre: str | None = Query(None),
    categoria_dre: str | None = Query(None),
    subcategoria_dre: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query = (
        db.query(FinanceiroPagar)
        .options(joinedload(FinanceiroPagar.classificacao_dre))
        .filter(FinanceiroPagar.empresa_id == empresa_id)
    )

    precisa_join_classificacao = any(
        [
            classificacao_dre_id is not None,
            bool(grupo_dre),
            bool(categoria_dre),
            bool(subcategoria_dre),
        ]
    )

    if precisa_join_classificacao:
        query = query.outerjoin(
            FinanceiroPlanoDRE,
            FinanceiroPlanoDRE.id == FinanceiroPagar.classificacao_dre_id,
        )

    if ano is not None:
        query = query.filter(extract("year", FinanceiroPagar.vencimento) == ano)

    if mes is not None:
        query = query.filter(extract("month", FinanceiroPagar.vencimento) == mes)

    if classificacao_dre_id is not None:
        query = query.filter(FinanceiroPagar.classificacao_dre_id == classificacao_dre_id)

    if grupo_dre:
        query = query.filter(FinanceiroPlanoDRE.grupo == grupo_dre)

    if categoria_dre:
        query = query.filter(FinanceiroPlanoDRE.categoria == categoria_dre)

    if subcategoria_dre:
        query = query.filter(FinanceiroPlanoDRE.subcategoria == subcategoria_dre)

    contas = (
        query
        .order_by(FinanceiroPagar.vencimento.asc(), FinanceiroPagar.id.desc())
        .all()
    )

    total_pendente = Decimal("0")
    total_pago = Decimal("0")
    total_vencido = Decimal("0")

    qtd_pendente = 0
    qtd_pago = 0
    qtd_vencido = 0

    resultado = []

    for conta in contas:
        status = conta.status_atual
        valor = Decimal(conta.valor or 0)

        if status == "PAGO":
            total_pago += Decimal(conta.valor_pago or 0)
            qtd_pago += 1
        elif status == "VENCIDO":
            total_vencido += valor
            qtd_vencido += 1
        elif status == "CANCELADO":
            pass
        else:
            total_pendente += valor
            qtd_pendente += 1

        resultado.append(_serializar(conta))

    return {
        "empresa_id": empresa_id,
        "resumo": {
            "total_pendente": float(total_pendente),
            "total_pago": float(total_pago),
            "total_vencido": float(total_vencido),
            "quantidade_pendente": qtd_pendente,
            "quantidade_paga": qtd_pago,
            "quantidade_vencida": qtd_vencido,
        },
        "contas": resultado,
    }


@router.post("/{conta_id}/baixar")
def baixar_conta_pagar(
    conta_id: int,
    payload: FinanceiroPagarBaixa,
    db: Session = Depends(get_db),
):
    conta = db.query(FinanceiroPagar).filter(FinanceiroPagar.id == conta_id).first()

    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada.")

    if conta.status == "PAGO":
        raise HTTPException(status_code=400, detail="Esta conta já está paga.")

    if conta.status == "CANCELADO":
        raise HTTPException(status_code=400, detail="Não é possível baixar uma conta cancelada.")

    conta.status = "PAGO"
    conta.data_pagamento = payload.data_pagamento or date.today()
    conta.valor_pago = Decimal(payload.valor_pago or conta.valor or 0)

    db.commit()
    db.refresh(conta)

    return {"ok": True}