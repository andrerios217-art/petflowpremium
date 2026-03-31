from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.financeiro_pagar import FinanceiroPagar
from app.models.financeiro_receber import FinanceiroReceber

router = APIRouter(prefix="/api/financeiro/dashboard", tags=["Financeiro Dashboard"])


def _to_float(valor) -> float:
    return float(valor or 0)


@router.get("/")
def dashboard_financeiro(
    empresa_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
):
    hoje = date.today()
    inicio_mes = hoje.replace(day=1)

    # =========================
    # ENTRADAS HOJE
    # =========================
    entradas_hoje = (
        db.query(func.coalesce(func.sum(FinanceiroReceber.valor_pago), 0))
        .filter(
            FinanceiroReceber.empresa_id == empresa_id,
            FinanceiroReceber.data_pagamento == hoje,
            FinanceiroReceber.status == "PAGO",
        )
        .scalar()
    )

    # =========================
    # SAÍDAS HOJE
    # =========================
    saidas_hoje = (
        db.query(func.coalesce(func.sum(FinanceiroPagar.valor_pago), 0))
        .filter(
            FinanceiroPagar.empresa_id == empresa_id,
            FinanceiroPagar.data_pagamento == hoje,
            FinanceiroPagar.status == "PAGO",
        )
        .scalar()
    )

    # =========================
    # RECEITA / DESPESA DO MÊS
    # =========================
    receita_mes = (
        db.query(func.coalesce(func.sum(FinanceiroReceber.valor_pago), 0))
        .filter(
            FinanceiroReceber.empresa_id == empresa_id,
            FinanceiroReceber.data_pagamento >= inicio_mes,
            FinanceiroReceber.data_pagamento <= hoje,
            FinanceiroReceber.status == "PAGO",
        )
        .scalar()
    )

    despesa_mes = (
        db.query(func.coalesce(func.sum(FinanceiroPagar.valor_pago), 0))
        .filter(
            FinanceiroPagar.empresa_id == empresa_id,
            FinanceiroPagar.data_pagamento >= inicio_mes,
            FinanceiroPagar.data_pagamento <= hoje,
            FinanceiroPagar.status == "PAGO",
        )
        .scalar()
    )

    lucro_hoje = _to_float(entradas_hoje) - _to_float(saidas_hoje)
    lucro_mes = _to_float(receita_mes) - _to_float(despesa_mes)

    # =========================
    # CONTAS A RECEBER
    # =========================
    pendente_hoje = (
        db.query(func.coalesce(func.sum(FinanceiroReceber.valor), 0))
        .filter(
            FinanceiroReceber.empresa_id == empresa_id,
            FinanceiroReceber.vencimento == hoje,
            FinanceiroReceber.status == "PENDENTE",
        )
        .scalar()
    )

    receber_aberto = (
        db.query(func.coalesce(func.sum(FinanceiroReceber.valor), 0))
        .filter(
            FinanceiroReceber.empresa_id == empresa_id,
            FinanceiroReceber.status == "PENDENTE",
        )
        .scalar()
    )

    receber_vencido = (
        db.query(func.coalesce(func.sum(FinanceiroReceber.valor), 0))
        .filter(
            FinanceiroReceber.empresa_id == empresa_id,
            FinanceiroReceber.vencimento < hoje,
            FinanceiroReceber.status == "PENDENTE",
        )
        .scalar()
    )

    # =========================
    # CONTAS A PAGAR
    # =========================
    pagar_aberto = (
        db.query(func.coalesce(func.sum(FinanceiroPagar.valor), 0))
        .filter(
            FinanceiroPagar.empresa_id == empresa_id,
            FinanceiroPagar.status == "PENDENTE",
        )
        .scalar()
    )

    pagar_vencido = (
        db.query(func.coalesce(func.sum(FinanceiroPagar.valor), 0))
        .filter(
            FinanceiroPagar.empresa_id == empresa_id,
            FinanceiroPagar.vencimento < hoje,
            FinanceiroPagar.status == "PENDENTE",
        )
        .scalar()
    )

    # Mantém compatibilidade com o dashboard antigo
    caixa_hoje = entradas_hoje
    vencido = receber_vencido

    # =========================
    # GRÁFICO 7 DIAS
    # =========================
    grafico_7_dias = []

    for i in range(6, -1, -1):
        dia = hoje - timedelta(days=i)

        entrada_dia = (
            db.query(func.coalesce(func.sum(FinanceiroReceber.valor_pago), 0))
            .filter(
                FinanceiroReceber.empresa_id == empresa_id,
                FinanceiroReceber.data_pagamento == dia,
                FinanceiroReceber.status == "PAGO",
            )
            .scalar()
        )

        saida_dia = (
            db.query(func.coalesce(func.sum(FinanceiroPagar.valor_pago), 0))
            .filter(
                FinanceiroPagar.empresa_id == empresa_id,
                FinanceiroPagar.data_pagamento == dia,
                FinanceiroPagar.status == "PAGO",
            )
            .scalar()
        )

        entrada_dia = _to_float(entrada_dia)
        saida_dia = _to_float(saida_dia)
        lucro_dia = entrada_dia - saida_dia

        grafico_7_dias.append(
            {
                "data": dia.isoformat(),
                "entrada": entrada_dia,
                "saida": saida_dia,
                "lucro": lucro_dia,
                # compatibilidade com o gráfico legado
                "valor": entrada_dia,
            }
        )

    return {
        # legado
        "caixa_hoje": _to_float(caixa_hoje),
        "pendente_hoje": _to_float(pendente_hoje),
        "vencido": _to_float(vencido),
        # premium
        "entradas_hoje": _to_float(entradas_hoje),
        "saidas_hoje": _to_float(saidas_hoje),
        "lucro_hoje": _to_float(lucro_hoje),
        "receita_mes": _to_float(receita_mes),
        "despesa_mes": _to_float(despesa_mes),
        "lucro_mes": _to_float(lucro_mes),
        "receber_aberto": _to_float(receber_aberto),
        "pagar_aberto": _to_float(pagar_aberto),
        "receber_vencido": _to_float(receber_vencido),
        "pagar_vencido": _to_float(pagar_vencido),
        "grafico_7_dias": grafico_7_dias,
    }