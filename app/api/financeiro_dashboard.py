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


def _parse_competencia(valor: str | None) -> tuple[int, int] | None:
    if not valor:
        return None

    valor = valor.strip()
    if not valor:
        return None

    try:
        ano_str, mes_str = valor.split("-", 1)
        ano = int(ano_str)
        mes = int(mes_str)
        if mes < 1 or mes > 12:
            return None
        return ano, mes
    except (ValueError, AttributeError):
        return None


def _resolver_periodo(
    mes: int | None,
    ano: int | None,
    competencia_inicio: str | None,
    competencia_fim: str | None,
) -> tuple[date, date]:
    hoje = date.today()

    comp_inicio = _parse_competencia(competencia_inicio)
    comp_fim = _parse_competencia(competencia_fim)

    if comp_inicio or comp_fim:
        if not comp_inicio:
            comp_inicio = comp_fim
        if not comp_fim:
            comp_fim = comp_inicio

        ano_inicio, mes_inicio = comp_inicio
        ano_fim, mes_fim = comp_fim

        inicio = date(ano_inicio, mes_inicio, 1)
        fim = _ultimo_dia_mes(ano_fim, mes_fim)

        if inicio > fim:
            inicio = date(ano_fim, mes_fim, 1)
            fim = _ultimo_dia_mes(ano_inicio, mes_inicio)

        return inicio, fim

    competencia_mes = mes or hoje.month
    competencia_ano = ano or hoje.year
    inicio = date(competencia_ano, competencia_mes, 1)
    fim = _ultimo_dia_mes(competencia_ano, competencia_mes)
    return inicio, fim


@router.get("/")
def dashboard_financeiro(
    empresa_id: int = Query(..., ge=1),
    mes: int | None = Query(None, ge=1, le=12),
    ano: int | None = Query(None, ge=2000, le=2100),
    competencia_inicio: str | None = Query(None),
    competencia_fim: str | None = Query(None),
    db: Session = Depends(get_db),
):
    hoje = date.today()
    inicio_periodo, fim_periodo = _resolver_periodo(mes, ano, competencia_inicio, competencia_fim)

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

    receita_periodo = (
        db.query(func.coalesce(func.sum(FinanceiroReceber.valor_pago), 0))
        .filter(
            FinanceiroReceber.empresa_id == empresa_id,
            FinanceiroReceber.data_pagamento >= inicio_periodo,
            FinanceiroReceber.data_pagamento <= fim_periodo,
            FinanceiroReceber.status == "PAGO",
        )
        .scalar()
    )

    despesa_periodo = (
        db.query(func.coalesce(func.sum(FinanceiroPagar.valor_pago), 0))
        .filter(
            FinanceiroPagar.empresa_id == empresa_id,
            FinanceiroPagar.data_pagamento >= inicio_periodo,
            FinanceiroPagar.data_pagamento <= fim_periodo,
            FinanceiroPagar.status == "PAGO",
        )
        .scalar()
    )

    lucro_hoje = _to_float(entradas_hoje) - _to_float(saidas_hoje)
    lucro_periodo = _to_float(receita_periodo) - _to_float(despesa_periodo)

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
            FinanceiroReceber.vencimento >= inicio_periodo,
            FinanceiroReceber.vencimento <= fim_periodo,
            FinanceiroReceber.status == "PENDENTE",
        )
        .scalar()
    )

    receber_vencido = (
        db.query(func.coalesce(func.sum(FinanceiroReceber.valor), 0))
        .filter(
            FinanceiroReceber.empresa_id == empresa_id,
            FinanceiroReceber.vencimento >= inicio_periodo,
            FinanceiroReceber.vencimento <= fim_periodo,
            FinanceiroReceber.vencimento < hoje,
            FinanceiroReceber.status == "PENDENTE",
        )
        .scalar()
    )

    pagar_aberto = (
        db.query(func.coalesce(func.sum(FinanceiroPagar.valor), 0))
        .filter(
            FinanceiroPagar.empresa_id == empresa_id,
            FinanceiroPagar.vencimento >= inicio_periodo,
            FinanceiroPagar.vencimento <= fim_periodo,
            FinanceiroPagar.status == "PENDENTE",
        )
        .scalar()
    )

    pagar_vencido = (
        db.query(func.coalesce(func.sum(FinanceiroPagar.valor), 0))
        .filter(
            FinanceiroPagar.empresa_id == empresa_id,
            FinanceiroPagar.vencimento >= inicio_periodo,
            FinanceiroPagar.vencimento <= fim_periodo,
            FinanceiroPagar.vencimento < hoje,
            FinanceiroPagar.status == "PENDENTE",
        )
        .scalar()
    )

    despesas_por_grupo_rows = (
        db.query(
            func.coalesce(FinanceiroPlanoDRE.grupo, "Sem grupo").label("grupo"),
            func.coalesce(func.sum(FinanceiroPagar.valor_pago), 0).label("valor"),
        )
        .select_from(FinanceiroPagar)
        .outerjoin(
            FinanceiroPlanoDRE,
            FinanceiroPlanoDRE.id == FinanceiroPagar.classificacao_dre_id,
        )
        .filter(
            FinanceiroPagar.empresa_id == empresa_id,
            FinanceiroPagar.data_pagamento >= inicio_periodo,
            FinanceiroPagar.data_pagamento <= fim_periodo,
            FinanceiroPagar.status == "PAGO",
        )
        .group_by(FinanceiroPlanoDRE.grupo)
        .order_by(func.coalesce(func.sum(FinanceiroPagar.valor_pago), 0).desc())
        .all()
    )

    despesas_por_categoria_rows = (
        db.query(
            func.coalesce(FinanceiroPlanoDRE.grupo, "Sem grupo").label("grupo"),
            func.coalesce(FinanceiroPlanoDRE.categoria, "Sem categoria").label("categoria"),
            func.coalesce(func.sum(FinanceiroPagar.valor_pago), 0).label("valor"),
        )
        .select_from(FinanceiroPagar)
        .outerjoin(
            FinanceiroPlanoDRE,
            FinanceiroPlanoDRE.id == FinanceiroPagar.classificacao_dre_id,
        )
        .filter(
            FinanceiroPagar.empresa_id == empresa_id,
            FinanceiroPagar.data_pagamento >= inicio_periodo,
            FinanceiroPagar.data_pagamento <= fim_periodo,
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
            func.coalesce(FinanceiroPlanoDRE.grupo, "Sem grupo").label("grupo"),
            func.coalesce(FinanceiroPlanoDRE.categoria, "Sem categoria").label("categoria"),
            func.coalesce(FinanceiroPlanoDRE.subcategoria, "Sem subcategoria").label("subcategoria"),
            func.coalesce(func.sum(FinanceiroPagar.valor_pago), 0).label("valor"),
        )
        .select_from(FinanceiroPagar)
        .outerjoin(
            FinanceiroPlanoDRE,
            FinanceiroPlanoDRE.id == FinanceiroPagar.classificacao_dre_id,
        )
        .filter(
            FinanceiroPagar.empresa_id == empresa_id,
            FinanceiroPagar.data_pagamento >= inicio_periodo,
            FinanceiroPagar.data_pagamento <= fim_periodo,
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
            "grupo": row.grupo,
            "valor": _to_float(row.valor),
            "grupo_dre": row.grupo,
            "total": _to_float(row.valor),
        }
        for row in despesas_por_grupo_rows
    ]

    despesas_por_categoria = [
        {
            "grupo": row.grupo,
            "categoria": row.categoria,
            "valor": _to_float(row.valor),
            "grupo_dre": row.grupo,
            "categoria_dre": row.categoria,
            "total": _to_float(row.valor),
        }
        for row in despesas_por_categoria_rows
    ]

    despesas_por_subcategoria = [
        {
            "grupo": row.grupo,
            "categoria": row.categoria,
            "subcategoria": row.subcategoria,
            "valor": _to_float(row.valor),
            "grupo_dre": row.grupo,
            "categoria_dre": row.categoria,
            "subcategoria_dre": row.subcategoria,
            "total": _to_float(row.valor),
        }
        for row in despesas_por_subcategoria_rows
    ]

    grafico_7_dias = []
    base_final_grafico = hoje if fim_periodo >= hoje else fim_periodo

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

        grafico_7_dias.append(
            {
                "data": dia.isoformat(),
                "entrada": entrada_dia,
                "saida": saida_dia,
                "lucro": entrada_dia - saida_dia,
                "valor": entrada_dia,
            }
        )

    return {
        "periodo": {
            "inicio": inicio_periodo.isoformat(),
            "fim": fim_periodo.isoformat(),
        },
        "caixa_hoje": _to_float(entradas_hoje),
        "pendente_hoje": _to_float(pendente_hoje),
        "vencido": _to_float(receber_vencido),
        "entradas_hoje": _to_float(entradas_hoje),
        "saidas_hoje": _to_float(saidas_hoje),
        "lucro_hoje": _to_float(lucro_hoje),
        "receita_mes": _to_float(receita_periodo),
        "despesa_mes": _to_float(despesa_periodo),
        "lucro_mes": _to_float(lucro_periodo),
        "total_receitas": _to_float(receita_periodo),
        "total_despesas": _to_float(despesa_periodo),
        "resultado": _to_float(lucro_periodo),
        "receber_aberto": _to_float(receber_aberto),
        "pagar_aberto": _to_float(pagar_aberto),
        "receber_vencido": _to_float(receber_vencido),
        "pagar_vencido": _to_float(pagar_vencido),
        "dre_despesas_por_grupo": despesas_por_grupo,
        "dre_despesas_por_categoria": despesas_por_categoria,
        "dre_despesas_por_subcategoria": despesas_por_subcategoria,
        "grafico_7_dias": grafico_7_dias,
    }