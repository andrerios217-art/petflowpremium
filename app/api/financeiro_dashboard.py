from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.financeiro_pagar import FinanceiroPagar
from app.models.financeiro_plano_dre import FinanceiroPlanoDRE
from app.models.financeiro_receber import FinanceiroReceber

router = APIRouter(prefix="/api/financeiro/dashboard", tags=["Financeiro Dashboard"])


def _to_float(valor) -> float:
    return float(valor or 0)


def _ultimo_dia_mes(ano: int, mes: int) -> date:
    if mes == 12:
        return date(ano + 1, 1, 1) - timedelta(days=1)
    return date(ano, mes + 1, 1) - timedelta(days=1)


@router.get("/")
def dashboard_financeiro(
    empresa_id: int = Query(..., ge=1),
    mes: int | None = Query(None, ge=1, le=12),
    ano: int | None = Query(None, ge=2000, le=2100),
    db: Session = Depends(get_db),
):
    hoje = date.today()
    competencia_mes = mes or hoje.month
    competencia_ano = ano or hoje.year

    inicio_mes = date(competencia_ano, competencia_mes, 1)
    fim_mes = _ultimo_dia_mes(competencia_ano, competencia_mes)

    usar_hoje_real = competencia_mes == hoje.month and competencia_ano == hoje.year
    data_final_periodo = hoje if usar_hoje_real else fim_mes

    entradas_hoje = (
        db.query(func.coalesce(func.sum(FinanceiroReceber.valor_pago), 0))
        .filter(
            FinanceiroReceber.empresa_id == empresa_id,
            FinanceiroReceber.data_pagamento == hoje,
            FinanceiroReceber.status == "PAGO",
        )
        .scalar()
    )

    saidas_hoje = (
        db.query(func.coalesce(func.sum(FinanceiroPagar.valor_pago), 0))
        .filter(
            FinanceiroPagar.empresa_id == empresa_id,
            FinanceiroPagar.data_pagamento == hoje,
            FinanceiroPagar.status == "PAGO",
        )
        .scalar()
    )

    receita_mes = (
        db.query(func.coalesce(func.sum(FinanceiroReceber.valor_pago), 0))
        .filter(
            FinanceiroReceber.empresa_id == empresa_id,
            FinanceiroReceber.data_pagamento >= inicio_mes,
            FinanceiroReceber.data_pagamento <= data_final_periodo,
            FinanceiroReceber.status == "PAGO",
        )
        .scalar()
    )

    despesa_mes = (
        db.query(func.coalesce(func.sum(FinanceiroPagar.valor_pago), 0))
        .filter(
            FinanceiroPagar.empresa_id == empresa_id,
            FinanceiroPagar.data_pagamento >= inicio_mes,
            FinanceiroPagar.data_pagamento <= data_final_periodo,
            FinanceiroPagar.status == "PAGO",
        )
        .scalar()
    )

    lucro_hoje = _to_float(entradas_hoje) - _to_float(saidas_hoje)
    lucro_mes = _to_float(receita_mes) - _to_float(despesa_mes)

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
            FinanceiroReceber.vencimento >= inicio_mes,
            FinanceiroReceber.vencimento <= fim_mes,
            FinanceiroReceber.status == "PENDENTE",
        )
        .scalar()
    )

    receber_vencido = (
        db.query(func.coalesce(func.sum(FinanceiroReceber.valor), 0))
        .filter(
            FinanceiroReceber.empresa_id == empresa_id,
            FinanceiroReceber.vencimento >= inicio_mes,
            FinanceiroReceber.vencimento <= fim_mes,
            FinanceiroReceber.vencimento < hoje,
            FinanceiroReceber.status == "PENDENTE",
        )
        .scalar()
    )

    pagar_aberto = (
        db.query(func.coalesce(func.sum(FinanceiroPagar.valor), 0))
        .filter(
            FinanceiroPagar.empresa_id == empresa_id,
            FinanceiroPagar.vencimento >= inicio_mes,
            FinanceiroPagar.vencimento <= fim_mes,
            FinanceiroPagar.status == "PENDENTE",
        )
        .scalar()
    )

    pagar_vencido = (
        db.query(func.coalesce(func.sum(FinanceiroPagar.valor), 0))
        .filter(
            FinanceiroPagar.empresa_id == empresa_id,
            FinanceiroPagar.vencimento >= inicio_mes,
            FinanceiroPagar.vencimento <= fim_mes,
            FinanceiroPagar.vencimento < hoje,
            FinanceiroPagar.status == "PENDENTE",
        )
        .scalar()
    )

    despesas_por_grupo_rows = (
        db.query(
            func.coalesce(FinanceiroPlanoDRE.grupo, "Sem grupo").label("grupo_dre"),
            func.coalesce(func.sum(FinanceiroPagar.valor_pago), 0).label("total"),
        )
        .outerjoin(
            FinanceiroPlanoDRE,
            FinanceiroPlanoDRE.id == FinanceiroPagar.classificacao_dre_id,
        )
        .filter(
            FinanceiroPagar.empresa_id == empresa_id,
            FinanceiroPagar.data_pagamento >= inicio_mes,
            FinanceiroPagar.data_pagamento <= data_final_periodo,
            FinanceiroPagar.status == "PAGO",
        )
        .group_by(FinanceiroPlanoDRE.grupo)
        .order_by(func.coalesce(func.sum(FinanceiroPagar.valor_pago), 0).desc())
        .all()
    )

    despesas_por_categoria_rows = (
        db.query(
            func.coalesce(FinanceiroPlanoDRE.grupo, "Sem grupo").label("grupo_dre"),
            func.coalesce(FinanceiroPlanoDRE.categoria, "Sem categoria").label("categoria_dre"),
            func.coalesce(func.sum(FinanceiroPagar.valor_pago), 0).label("total"),
        )
        .outerjoin(
            FinanceiroPlanoDRE,
            FinanceiroPlanoDRE.id == FinanceiroPagar.classificacao_dre_id,
        )
        .filter(
            FinanceiroPagar.empresa_id == empresa_id,
            FinanceiroPagar.data_pagamento >= inicio_mes,
            FinanceiroPagar.data_pagamento <= data_final_periodo,
            FinanceiroPagar.status == "PAGO",
        )
        .group_by(FinanceiroPlanoDRE.grupo, FinanceiroPlanoDRE.categoria)
        .order_by(
            func.coalesce(FinanceiroPlanoDRE.grupo, "Sem grupo").asc(),
            func.coalesce(func.sum(FinanceiroPagar.valor_pago), 0).desc(),
        )
        .all()
    )

    despesas_por_subcategoria_rows = (
        db.query(
            func.coalesce(FinanceiroPlanoDRE.grupo, "Sem grupo").label("grupo_dre"),
            func.coalesce(FinanceiroPlanoDRE.categoria, "Sem categoria").label("categoria_dre"),
            func.coalesce(FinanceiroPlanoDRE.subcategoria, "Sem subcategoria").label(
                "subcategoria_dre"
            ),
            func.coalesce(func.sum(FinanceiroPagar.valor_pago), 0).label("total"),
        )
        .outerjoin(
            FinanceiroPlanoDRE,
            FinanceiroPlanoDRE.id == FinanceiroPagar.classificacao_dre_id,
        )
        .filter(
            FinanceiroPagar.empresa_id == empresa_id,
            FinanceiroPagar.data_pagamento >= inicio_mes,
            FinanceiroPagar.data_pagamento <= data_final_periodo,
            FinanceiroPagar.status == "PAGO",
        )
        .group_by(
            FinanceiroPlanoDRE.grupo,
            FinanceiroPlanoDRE.categoria,
            FinanceiroPlanoDRE.subcategoria,
        )
        .order_by(
            func.coalesce(FinanceiroPlanoDRE.grupo, "Sem grupo").asc(),
            func.coalesce(FinanceiroPlanoDRE.categoria, "Sem categoria").asc(),
            func.coalesce(func.sum(FinanceiroPagar.valor_pago), 0).desc(),
        )
        .all()
    )

    despesas_por_grupo = [
        {
            "grupo_dre": row.grupo_dre,
            "total": _to_float(row.total),
        }
        for row in despesas_por_grupo_rows
    ]

    despesas_por_categoria = [
        {
            "grupo_dre": row.grupo_dre,
            "categoria_dre": row.categoria_dre,
            "total": _to_float(row.total),
        }
        for row in despesas_por_categoria_rows
    ]

    despesas_por_subcategoria = [
        {
            "grupo_dre": row.grupo_dre,
            "categoria_dre": row.categoria_dre,
            "subcategoria_dre": row.subcategoria_dre,
            "total": _to_float(row.total),
        }
        for row in despesas_por_subcategoria_rows
    ]

    caixa_hoje = entradas_hoje
    vencido = receber_vencido

    grafico_7_dias = []

    if usar_hoje_real:
        base_final_grafico = hoje
    else:
        base_final_grafico = fim_mes

    for i in range(6, -1, -1):
        dia = base_final_grafico - timedelta(days=i)

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
                "valor": entrada_dia,
            }
        )

    return {
        "caixa_hoje": _to_float(caixa_hoje),
        "pendente_hoje": _to_float(pendente_hoje),
        "vencido": _to_float(vencido),
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
        "dre_despesas_por_grupo": despesas_por_grupo,
        "dre_despesas_por_categoria": despesas_por_categoria,
        "dre_despesas_por_subcategoria": despesas_por_subcategoria,
        "grafico_7_dias": grafico_7_dias,
    }