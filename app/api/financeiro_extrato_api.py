from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.caixa_movimento import CaixaMovimento
from app.models.financeiro_pagar import FinanceiroPagar
from app.models.financeiro_receber import FinanceiroReceber

router = APIRouter(prefix="/api/financeiro/extrato", tags=["Financeiro Extrato"])


def _to_float(valor) -> float:
    return float(valor or 0)


def _normalizar_data(data_valor):
    if not data_valor:
        return None
    if isinstance(data_valor, date):
        return data_valor.isoformat()
    return str(data_valor)


@router.get("/")
def listar_extrato_financeiro(
    empresa_id: int = Query(..., ge=1),
    data_inicial: date | None = Query(None),
    data_final: date | None = Query(None),
    tipo: str | None = Query(None),
    db: Session = Depends(get_db),
):
    lancamentos = []

    contas_receber = (
        db.query(FinanceiroReceber)
        .filter(FinanceiroReceber.empresa_id == empresa_id)
        .order_by(FinanceiroReceber.vencimento.desc(), FinanceiroReceber.id.desc())
        .all()
    )

    for conta in contas_receber:
        data_ref = conta.data_pagamento or conta.vencimento

        if data_inicial and data_ref and data_ref < data_inicial:
            continue
        if data_final and data_ref and data_ref > data_final:
            continue
        if tipo and tipo.upper() != "RECEBER":
            continue

        lancamentos.append(
            {
                "tipo": "RECEBER",
                "origem": conta.origem_tipo or "MANUAL",
                "origem_id": conta.origem_id or conta.id,
                "descricao": conta.descricao,
                "pessoa": conta.cliente.nome if conta.cliente else None,
                "valor": _to_float(conta.valor),
                "valor_pago": _to_float(conta.valor_pago),
                "status": conta.status_atual,
                "data_referencia": _normalizar_data(data_ref),
                "vencimento": _normalizar_data(conta.vencimento),
                "data_pagamento": _normalizar_data(conta.data_pagamento),
            }
        )

    contas_pagar = (
        db.query(FinanceiroPagar)
        .filter(FinanceiroPagar.empresa_id == empresa_id)
        .order_by(FinanceiroPagar.vencimento.desc(), FinanceiroPagar.id.desc())
        .all()
    )

    for conta in contas_pagar:
        data_ref = conta.data_pagamento or conta.vencimento

        if data_inicial and data_ref and data_ref < data_inicial:
            continue
        if data_final and data_ref and data_ref > data_final:
            continue
        if tipo and tipo.upper() != "PAGAR":
            continue

        lancamentos.append(
            {
                "tipo": "PAGAR",
                "origem": "MANUAL",
                "origem_id": conta.id,
                "descricao": conta.descricao,
                "pessoa": conta.fornecedor,
                "valor": _to_float(conta.valor),
                "valor_pago": _to_float(conta.valor_pago),
                "status": conta.status_atual,
                "data_referencia": _normalizar_data(data_ref),
                "vencimento": _normalizar_data(conta.vencimento),
                "data_pagamento": _normalizar_data(conta.data_pagamento),
            }
        )

    movimentos_caixa = (
        db.query(CaixaMovimento)
        .filter(CaixaMovimento.empresa_id == empresa_id)
        .order_by(CaixaMovimento.created_at.desc(), CaixaMovimento.id.desc())
        .all()
    )

    for movimento in movimentos_caixa:
        data_movimento = (
            movimento.created_at.date()
            if movimento.created_at
            else None
        )

        if data_inicial and data_movimento and data_movimento < data_inicial:
            continue
        if data_final and data_movimento and data_movimento > data_final:
            continue
        if tipo and tipo.upper() != "CAIXA":
            continue

        lancamentos.append(
            {
                "tipo": "CAIXA",
                "origem": movimento.tipo_movimento,
                "origem_id": movimento.id,
                "descricao": movimento.motivo or movimento.tipo_movimento,
                "pessoa": None,
                "valor": _to_float(movimento.valor),
                "valor_pago": _to_float(movimento.valor),
                "status": "REGISTRADO",
                "data_referencia": _normalizar_data(data_movimento),
                "vencimento": None,
                "data_pagamento": _normalizar_data(data_movimento),
                "forma_pagamento": movimento.forma_pagamento,
            }
        )

    lancamentos.sort(
        key=lambda item: (
            item.get("data_referencia") or "",
            item.get("origem_id") or 0,
        ),
        reverse=True,
    )

    total_entradas = 0.0
    total_saidas = 0.0

    for item in lancamentos:
        valor_base = float(item.get("valor_pago") or item.get("valor") or 0)

        if item["tipo"] == "RECEBER":
            if item["status"] == "PAGO":
                total_entradas += valor_base
        elif item["tipo"] == "PAGAR":
            if item["status"] == "PAGO":
                total_saidas += valor_base
        elif item["tipo"] == "CAIXA":
            origem = (item.get("origem") or "").upper()
            if origem in ("VENDA", "SUPRIMENTO"):
                total_entradas += valor_base
            elif origem in ("SANGRIA", "ESTORNO", "AJUSTE"):
                total_saidas += valor_base

    return {
        "empresa_id": empresa_id,
        "filtros": {
            "data_inicial": _normalizar_data(data_inicial),
            "data_final": _normalizar_data(data_final),
            "tipo": tipo.upper() if tipo else None,
        },
        "resumo": {
            "total_entradas": total_entradas,
            "total_saidas": total_saidas,
            "saldo": total_entradas - total_saidas,
            "quantidade": len(lancamentos),
        },
        "lancamentos": lancamentos,
    }