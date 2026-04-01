from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import extract
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.financeiro_receber import FinanceiroReceber
from app.schemas.financeiro import (
    FinanceiroReceberBaixa,
    FinanceiroReceberCreate,
    FinanceiroReceberListOut,
    FinanceiroReceberOut,
)

router = APIRouter(prefix="/api/financeiro", tags=["Financeiro"])


def _serializar(conta: FinanceiroReceber):
    return {
        "id": conta.id,
        "empresa_id": conta.empresa_id,
        "cliente_id": conta.cliente_id,
        "cliente_nome": conta.cliente.nome if conta.cliente else None,
        "origem_tipo": conta.origem_tipo,
        "origem_id": conta.origem_id,
        "descricao": conta.descricao,
        "observacao": conta.observacao,
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


@router.post("/receber", response_model=FinanceiroReceberOut)
def criar_conta_receber(
    payload: FinanceiroReceberCreate,
    db: Session = Depends(get_db),
):
    conta = FinanceiroReceber(
        empresa_id=payload.empresa_id,
        cliente_id=payload.cliente_id,
        origem_tipo=payload.origem_tipo,
        origem_id=payload.origem_id,
        descricao=payload.descricao,
        observacao=payload.observacao,
        valor=Decimal(payload.valor),
        valor_pago=Decimal("0.00"),
        vencimento=payload.vencimento,
        status="PENDENTE",
    )

    db.add(conta)
    db.commit()
    db.refresh(conta)

    return _serializar(conta)


@router.get("/receber", response_model=FinanceiroReceberListOut)
def listar_contas_receber(
    empresa_id: int = Query(..., ge=1),
    mes: int | None = Query(None, ge=1, le=12),
    ano: int | None = Query(None, ge=2000, le=2100),
    db: Session = Depends(get_db),
):
    query = db.query(FinanceiroReceber).filter(FinanceiroReceber.empresa_id == empresa_id)

    if ano is not None:
        query = query.filter(extract("year", FinanceiroReceber.vencimento) == ano)

    if mes is not None:
        query = query.filter(extract("month", FinanceiroReceber.vencimento) == mes)

    contas = (
        query
        .order_by(FinanceiroReceber.vencimento.asc(), FinanceiroReceber.id.desc())
        .all()
    )

    hoje = date.today()
    total_pendente = Decimal("0")
    total_pago = Decimal("0")
    total_vencido = Decimal("0")
    qtd_pendente = 0
    qtd_pago = 0
    qtd_vencido = 0
    resultado = []

    for conta in contas:
        status = conta.status

        if status != "PAGO" and conta.vencimento < hoje:
            status = "VENCIDO"

        valor = Decimal(conta.valor or 0)

        if status == "PAGO":
            total_pago += valor
            qtd_pago += 1
        elif status == "VENCIDO":
            total_vencido += valor
            qtd_vencido += 1
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


@router.post("/receber/{conta_id}/baixar")
def baixar_conta_receber(
    conta_id: int,
    payload: FinanceiroReceberBaixa,
    db: Session = Depends(get_db),
):
    conta = db.query(FinanceiroReceber).filter(FinanceiroReceber.id == conta_id).first()

    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada.")

    if conta.status == "PAGO":
        raise HTTPException(status_code=400, detail="Esta conta já está paga.")

    conta.status = "PAGO"
    conta.data_pagamento = payload.data_pagamento or date.today()
    conta.valor_pago = Decimal(payload.valor_pago or conta.valor or 0)

    db.commit()

    return {"ok": True}