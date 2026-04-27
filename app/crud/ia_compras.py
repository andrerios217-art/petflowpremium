from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.empresa import Empresa
from app.models.estoque_saldo import EstoqueSaldo
from app.models.pdv_venda import PdvVenda
from app.models.pdv_venda_item import PdvVendaItem
from app.models.produto import Produto


DECIMAL_2 = Decimal("0.01")
DECIMAL_3 = Decimal("0.001")


def _decimal_2(valor) -> Decimal:
    if valor is None:
        return Decimal("0.00")
    return Decimal(str(valor)).quantize(DECIMAL_2, rounding=ROUND_HALF_UP)


def _decimal_3(valor) -> Decimal:
    if valor is None:
        return Decimal("0.000")
    return Decimal(str(valor)).quantize(DECIMAL_3, rounding=ROUND_HALF_UP)


def _inteiro_para_compra(valor) -> int:
    quantidade = Decimal(str(valor or 0))
    if quantidade <= Decimal("0"):
        return 0
    return int(quantidade.to_integral_value(rounding=ROUND_CEILING))


def _inicio_dia(valor: date | datetime | None) -> datetime | None:
    if not valor:
        return None

    if isinstance(valor, datetime):
        if valor.tzinfo is None:
            return valor.replace(tzinfo=timezone.utc)
        return valor

    return datetime.combine(valor, time.min).replace(tzinfo=timezone.utc)


def _fim_dia(valor: date | datetime | None) -> datetime | None:
    if not valor:
        return None

    if isinstance(valor, datetime):
        base = valor
        if base.tzinfo is None:
            base = base.replace(tzinfo=timezone.utc)
        return base.replace(hour=23, minute=59, second=59, microsecond=999999)

    return datetime.combine(valor, time.max).replace(tzinfo=timezone.utc)


def _get_empresa_or_404(db: Session, empresa_id: int) -> Empresa:
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    return empresa


def _classificar_abc(percentual_acumulado: Decimal) -> str:
    if percentual_acumulado <= Decimal("80.00"):
        return "A"
    if percentual_acumulado <= Decimal("95.00"):
        return "B"
    return "C"


def _classificar_prioridade(
    curva_abc: str,
    quantidade_sugerida: int,
    dias_sem_venda: int | None,
) -> str:
    if quantidade_sugerida <= 0:
        if dias_sem_venda is not None and dias_sem_venda >= 90:
            return "BAIXA"
        return "SEM_COMPRA"

    if curva_abc == "A":
        return "ALTA"

    if curva_abc == "B":
        return "MEDIA"

    return "BAIXA"


def _calcular_estoque_atual_produtos(db: Session, empresa_id: int) -> dict[int, Decimal]:
    rows = (
        db.query(
            EstoqueSaldo.produto_id.label("produto_id"),
            func.coalesce(func.sum(EstoqueSaldo.quantidade_atual), 0).label("saldo_total"),
        )
        .filter(EstoqueSaldo.empresa_id == empresa_id)
        .group_by(EstoqueSaldo.produto_id)
        .all()
    )

    return {
        int(row.produto_id): _decimal_3(row.saldo_total)
        for row in rows
        if row.produto_id is not None
    }


def analisar_compras_produtos(
    db: Session,
    *,
    empresa_id: int,
    data_inicio: date | datetime | None = None,
    data_fim: date | datetime | None = None,
    dias_cobertura: int = 30,
    prazo_reposicao_dias_uteis: int = 3,
    limite: int = 300,
) -> dict:
    _get_empresa_or_404(db, empresa_id)

    if not data_fim:
        data_fim = datetime.now(timezone.utc)

    if not data_inicio:
        data_inicio = _fim_dia(data_fim) - timedelta(days=90)

    inicio = _inicio_dia(data_inicio)
    fim = _fim_dia(data_fim)

    dias_periodo = max(1, (fim.date() - inicio.date()).days + 1)
    dias_cobertura = max(1, min(int(dias_cobertura or 30), 180))
    prazo_reposicao_dias_uteis = max(0, min(int(prazo_reposicao_dias_uteis or 3), 30))
    dias_planejamento_total = dias_cobertura + prazo_reposicao_dias_uteis
    limite = max(1, min(int(limite or 300), 1000))

    estoque_atual_por_produto = _calcular_estoque_atual_produtos(db, empresa_id)

    rows = (
        db.query(
            Produto.id.label("produto_id"),
            Produto.sku.label("sku"),
            Produto.nome.label("produto_nome"),
            Produto.preco_venda_atual.label("preco_venda_atual"),
            Produto.custo_medio_atual.label("custo_medio_atual"),
            Produto.estoque_minimo.label("estoque_minimo"),
            func.sum(PdvVendaItem.quantidade).label("quantidade_vendida"),
            func.sum(PdvVendaItem.valor_total).label("faturamento"),
            func.sum(PdvVendaItem.desconto_valor).label("desconto_total"),
            func.count(PdvVendaItem.id).label("quantidade_linhas"),
            func.count(func.distinct(PdvVenda.id)).label("quantidade_vendas"),
            func.max(PdvVenda.fechada_em).label("ultima_venda_em"),
        )
        .join(PdvVendaItem, PdvVendaItem.produto_id == Produto.id)
        .join(PdvVenda, PdvVenda.id == PdvVendaItem.venda_id)
        .filter(
            Produto.empresa_id == empresa_id,
            PdvVenda.empresa_id == empresa_id,
            PdvVenda.status == "FECHADA",
            PdvVendaItem.tipo_item == "PRODUCT",
            PdvVendaItem.produto_id.isnot(None),
            PdvVenda.fechada_em >= inicio,
            PdvVenda.fechada_em <= fim,
        )
        .group_by(
            Produto.id,
            Produto.sku,
            Produto.nome,
            Produto.preco_venda_atual,
            Produto.custo_medio_atual,
            Produto.estoque_minimo,
        )
        .order_by(func.sum(PdvVendaItem.valor_total).desc())
        .limit(limite)
        .all()
    )

    total_faturamento = sum((_decimal_2(row.faturamento) for row in rows), Decimal("0.00"))
    total_quantidade = sum((_decimal_3(row.quantidade_vendida) for row in rows), Decimal("0.000"))

    produtos = []
    acumulado = Decimal("0.00")

    for row in rows:
        produto_id = int(row.produto_id)
        faturamento = _decimal_2(row.faturamento)
        quantidade_vendida = _decimal_3(row.quantidade_vendida)
        desconto_total = _decimal_2(row.desconto_total)
        preco_venda = _decimal_2(row.preco_venda_atual)
        custo_medio = _decimal_2(row.custo_medio_atual)
        estoque_minimo = _decimal_3(row.estoque_minimo)
        estoque_atual = _decimal_3(estoque_atual_por_produto.get(produto_id, Decimal("0.000")))

        participacao = Decimal("0.00")
        if total_faturamento > 0:
            participacao = ((faturamento / total_faturamento) * Decimal("100")).quantize(
                DECIMAL_2,
                rounding=ROUND_HALF_UP,
            )

        acumulado += participacao
        curva_abc = _classificar_abc(acumulado)

        media_diaria = _decimal_3(quantidade_vendida / Decimal(str(dias_periodo)))

        previsao_venda_durante_reposicao = _decimal_3(
            media_diaria * Decimal(str(prazo_reposicao_dias_uteis))
        )

        demanda_cobertura = _decimal_3(
            media_diaria * Decimal(str(dias_cobertura))
        )

        demanda_total_planejada = _decimal_3(
            media_diaria * Decimal(str(dias_planejamento_total))
        )

        estoque_alvo = demanda_total_planejada
        if estoque_alvo < estoque_minimo:
            estoque_alvo = estoque_minimo

        necessidade_liquida = _decimal_3(estoque_alvo - estoque_atual)
        if necessidade_liquida < Decimal("0.000"):
            necessidade_liquida = Decimal("0.000")

        quantidade_sugerida_compra = _inteiro_para_compra(necessidade_liquida)

        ultima_venda_em = row.ultima_venda_em
        dias_sem_venda = None
        if ultima_venda_em:
            if ultima_venda_em.tzinfo is None:
                ultima_venda_em = ultima_venda_em.replace(tzinfo=timezone.utc)
            dias_sem_venda = max(0, (fim.date() - ultima_venda_em.date()).days)

        prioridade = _classificar_prioridade(
            curva_abc=curva_abc,
            quantidade_sugerida=quantidade_sugerida_compra,
            dias_sem_venda=dias_sem_venda,
        )

        margem_unitaria = _decimal_2(preco_venda - custo_medio)
        margem_total_estimada = _decimal_2(margem_unitaria * quantidade_vendida)

        produtos.append(
            {
                "produto_id": produto_id,
                "sku": row.sku,
                "produto_nome": row.produto_nome,
                "curva_abc": curva_abc,
                "prioridade": prioridade,
                "quantidade_vendida": float(quantidade_vendida),
                "faturamento": float(faturamento),
                "participacao_percentual": float(participacao),
                "participacao_acumulada_percentual": float(_decimal_2(acumulado)),
                "desconto_total": float(desconto_total),
                "quantidade_vendas": int(row.quantidade_vendas or 0),
                "quantidade_linhas": int(row.quantidade_linhas or 0),
                "media_diaria": float(media_diaria),
                "dias_periodo": dias_periodo,
                "dias_cobertura": dias_cobertura,
                "prazo_reposicao_dias_uteis": prazo_reposicao_dias_uteis,
                "dias_planejamento_total": dias_planejamento_total,
                "estoque_atual": float(estoque_atual),
                "estoque_minimo": float(estoque_minimo),
                "previsao_venda_durante_reposicao": float(previsao_venda_durante_reposicao),
                "demanda_cobertura": float(demanda_cobertura),
                "demanda_total_planejada": float(demanda_total_planejada),
                "estoque_alvo": float(_decimal_3(estoque_alvo)),
                "necessidade_liquida": float(necessidade_liquida),
                "quantidade_sugerida_compra": quantidade_sugerida_compra,
                "preco_venda_atual": float(preco_venda),
                "custo_medio_atual": float(custo_medio),
                "margem_unitaria_estimada": float(margem_unitaria),
                "margem_total_estimada": float(margem_total_estimada),
                "ultima_venda_em": ultima_venda_em.isoformat() if ultima_venda_em else None,
                "dias_sem_venda": dias_sem_venda,
            }
        )

    produtos_parados = [
        item
        for item in produtos
        if item["dias_sem_venda"] is not None and item["dias_sem_venda"] >= 60
    ]

    sugestoes_compra = [
        item
        for item in produtos
        if int(item["quantidade_sugerida_compra"]) > 0
    ]

    sugestoes_compra = sorted(
        sugestoes_compra,
        key=lambda item: (
            {"ALTA": 3, "MEDIA": 2, "BAIXA": 1, "SEM_COMPRA": 0}.get(item["prioridade"], 0),
            item["faturamento"],
        ),
        reverse=True,
    )

    return {
        "filtros": {
            "empresa_id": empresa_id,
            "data_inicio": inicio.isoformat(),
            "data_fim": fim.isoformat(),
            "dias_periodo": dias_periodo,
            "dias_cobertura": dias_cobertura,
            "prazo_reposicao_dias_uteis": prazo_reposicao_dias_uteis,
            "dias_planejamento_total": dias_planejamento_total,
            "limite": limite,
        },
        "resumo": {
            "produtos_analisados": len(produtos),
            "total_quantidade_vendida": float(_decimal_3(total_quantidade)),
            "total_faturamento": float(_decimal_2(total_faturamento)),
            "produtos_curva_a": len([p for p in produtos if p["curva_abc"] == "A"]),
            "produtos_curva_b": len([p for p in produtos if p["curva_abc"] == "B"]),
            "produtos_curva_c": len([p for p in produtos if p["curva_abc"] == "C"]),
            "produtos_parados_60_dias": len(produtos_parados),
            "sugestoes_compra": len(sugestoes_compra),
        },
        "produtos": produtos,
        "produtos_parados": produtos_parados[:50],
        "sugestoes_compra": sugestoes_compra[:100],
    }