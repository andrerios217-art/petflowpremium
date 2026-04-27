from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.empresa import Empresa
from app.models.pdv_pagamento import PdvPagamento
from app.models.pdv_venda import PdvVenda
from app.models.pdv_venda_item import PdvVendaItem
from app.models.produto import Produto


DECIMAL_2 = Decimal("0.01")


def _decimal_2(valor) -> Decimal:
    if valor is None:
        return Decimal("0.00")
    return Decimal(str(valor)).quantize(DECIMAL_2, rounding=ROUND_HALF_UP)


def _parse_data_relatorio(valor):
    if not valor:
        return None

    if isinstance(valor, datetime):
        if valor.tzinfo is None:
            return valor.replace(tzinfo=timezone.utc)
        return valor

    texto = str(valor).strip()
    if not texto:
        return None

    try:
        if len(texto) == 10:
            return datetime.fromisoformat(texto).replace(tzinfo=timezone.utc)

        data = datetime.fromisoformat(texto)
        if data.tzinfo is None:
            data = data.replace(tzinfo=timezone.utc)
        return data
    except ValueError:
        raise HTTPException(status_code=400, detail="Data inválida no relatório.")


def _fim_dia_relatorio(valor):
    data = _parse_data_relatorio(valor)
    if not data:
        return None

    return data.replace(hour=23, minute=59, second=59, microsecond=999999)


def _get_empresa_or_404(db: Session, empresa_id: int) -> Empresa:
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    return empresa


def _normalizar_status(status: str | None) -> str | None:
    if not status:
        return None

    status_normalizado = str(status).strip().upper()

    if status_normalizado not in {"ABERTA", "FECHADA", "CANCELADA"}:
        raise HTTPException(status_code=400, detail="Status inválido para relatório.")

    return status_normalizado


def _forma_pagamento_venda(venda: PdvVenda) -> str | None:
    pagamentos = getattr(venda, "pagamentos", []) or []

    for pagamento in pagamentos:
        if getattr(pagamento, "status", None) == "RECEBIDO":
            return getattr(pagamento, "forma_pagamento", None)

    if pagamentos:
        return getattr(pagamentos[0], "forma_pagamento", None)

    return None


def _query_vendas_base(
    db: Session,
    *,
    empresa_id: int,
    data_inicio=None,
    data_fim=None,
    cliente_id: int | None = None,
    status: str | None = None,
):
    _get_empresa_or_404(db, empresa_id)

    inicio = _parse_data_relatorio(data_inicio)
    fim = _fim_dia_relatorio(data_fim)
    status_normalizado = _normalizar_status(status)

    query = db.query(PdvVenda).filter(PdvVenda.empresa_id == empresa_id)

    if inicio:
      query = query.filter(
          or_(
              PdvVenda.fechada_em >= inicio,
              PdvVenda.aberta_em >= inicio,
              PdvVenda.created_at >= inicio,
          )
      )

    if fim:
      query = query.filter(
          or_(
              PdvVenda.fechada_em <= fim,
              PdvVenda.aberta_em <= fim,
              PdvVenda.created_at <= fim,
          )
      )

    if cliente_id:
        query = query.filter(PdvVenda.cliente_id == cliente_id)

    if status_normalizado:
        query = query.filter(PdvVenda.status == status_normalizado)

    return query


def relatorio_vendas(
    db: Session,
    *,
    empresa_id: int,
    data_inicio=None,
    data_fim=None,
    cliente_id: int | None = None,
    status: str | None = None,
    limite: int = 500,
) -> dict:
    query = (
        _query_vendas_base(
            db,
            empresa_id=empresa_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            cliente_id=cliente_id,
            status=status,
        )
        .outerjoin(Cliente, Cliente.id == PdvVenda.cliente_id)
        .order_by(PdvVenda.id.desc())
        .limit(max(1, min(int(limite or 500), 2000)))
    )

    vendas = query.all()

    linhas = []
    for venda in vendas:
        data_ref = venda.fechada_em or venda.aberta_em or venda.created_at
        cliente = getattr(venda, "cliente", None)

        linhas.append(
            {
                "id": venda.id,
                "numero_venda": venda.numero_venda,
                "data": data_ref.isoformat() if data_ref else None,
                "aberta_em": venda.aberta_em.isoformat() if venda.aberta_em else None,
                "fechada_em": venda.fechada_em.isoformat() if venda.fechada_em else None,
                "cliente_id": venda.cliente_id,
                "cliente_nome": (
                    getattr(cliente, "nome", None)
                    or venda.nome_cliente_snapshot
                    or "Cliente não informado"
                ),
                "modo_cliente": venda.modo_cliente,
                "origem": venda.origem,
                "status": venda.status,
                "subtotal": float(_decimal_2(venda.subtotal)),
                "desconto_valor": float(_decimal_2(venda.desconto_valor)),
                "acrescimo_valor": float(_decimal_2(venda.acrescimo_valor)),
                "valor_total": float(_decimal_2(venda.valor_total)),
                "forma_pagamento": _forma_pagamento_venda(venda),
                "quantidade_itens": len(getattr(venda, "itens", []) or []),
            }
        )

    vendas_fechadas = [venda for venda in vendas if venda.status == "FECHADA"]
    vendas_canceladas = [venda for venda in vendas if venda.status == "CANCELADA"]
    vendas_abertas = [venda for venda in vendas if venda.status == "ABERTA"]

    total_subtotal = sum((_decimal_2(venda.subtotal) for venda in vendas_fechadas), Decimal("0.00"))
    total_descontos = sum((_decimal_2(venda.desconto_valor) for venda in vendas_fechadas), Decimal("0.00"))
    total_acrescimos = sum((_decimal_2(venda.acrescimo_valor) for venda in vendas_fechadas), Decimal("0.00"))
    total_vendido = sum((_decimal_2(venda.valor_total) for venda in vendas_fechadas), Decimal("0.00"))

    resumo_por_pagamento = {}
    for venda in vendas_fechadas:
        forma = _forma_pagamento_venda(venda) or "NAO_INFORMADO"

        if forma not in resumo_por_pagamento:
            resumo_por_pagamento[forma] = {
                "forma_pagamento": forma,
                "quantidade": 0,
                "valor_total": 0.0,
            }

        resumo_por_pagamento[forma]["quantidade"] += 1
        resumo_por_pagamento[forma]["valor_total"] = float(
            _decimal_2(
                Decimal(str(resumo_por_pagamento[forma]["valor_total"]))
                + _decimal_2(venda.valor_total)
            )
        )

    return {
        "filtros": {
            "empresa_id": empresa_id,
            "data_inicio": _parse_data_relatorio(data_inicio).isoformat() if data_inicio else None,
            "data_fim": _fim_dia_relatorio(data_fim).isoformat() if data_fim else None,
            "cliente_id": cliente_id,
            "status": status,
            "limite": limite,
        },
        "resumo": {
            "quantidade_vendas": len(vendas),
            "quantidade_fechadas": len(vendas_fechadas),
            "quantidade_abertas": len(vendas_abertas),
            "quantidade_canceladas": len(vendas_canceladas),
            "subtotal": float(_decimal_2(total_subtotal)),
            "descontos": float(_decimal_2(total_descontos)),
            "acrescimos": float(_decimal_2(total_acrescimos)),
            "total_vendido": float(_decimal_2(total_vendido)),
            "por_forma_pagamento": list(resumo_por_pagamento.values()),
        },
        "vendas": linhas,
    }


def relatorio_itens_vendidos(
    db: Session,
    *,
    empresa_id: int,
    data_inicio=None,
    data_fim=None,
    cliente_id: int | None = None,
    status: str | None = "FECHADA",
    tipo_item: str | None = None,
    produto_id: int | None = None,
    termo: str | None = None,
    ordenar_por: str = "valor_total",
    ordem: str = "desc",
    limite: int = 200,
) -> dict:
    _get_empresa_or_404(db, empresa_id)

    status_normalizado = _normalizar_status(status) if status else None
    tipo_normalizado = str(tipo_item).strip().upper() if tipo_item else None

    if tipo_normalizado and tipo_normalizado not in {"PRODUCT", "SERVICE"}:
        raise HTTPException(status_code=400, detail="Tipo de item inválido.")

    ordenar_por = str(ordenar_por or "valor_total").strip().lower()
    if ordenar_por not in {"quantidade", "valor_total", "descricao"}:
        ordenar_por = "valor_total"

    ordem = str(ordem or "desc").strip().lower()
    if ordem not in {"asc", "desc"}:
        ordem = "desc"

    query = (
        db.query(
            PdvVendaItem.tipo_item.label("tipo_item"),
            PdvVendaItem.produto_id.label("produto_id"),
            PdvVendaItem.descricao_snapshot.label("descricao"),
            func.sum(PdvVendaItem.quantidade).label("quantidade_total"),
            func.sum(PdvVendaItem.valor_total).label("valor_total"),
            func.sum(PdvVendaItem.desconto_valor).label("desconto_total"),
            func.count(PdvVendaItem.id).label("quantidade_linhas"),
            func.count(func.distinct(PdvVenda.id)).label("quantidade_vendas"),
        )
        .join(PdvVenda, PdvVenda.id == PdvVendaItem.venda_id)
        .filter(PdvVenda.empresa_id == empresa_id)
    )

    inicio = _parse_data_relatorio(data_inicio)
    fim = _fim_dia_relatorio(data_fim)

    if inicio:
        query = query.filter(
            or_(
                PdvVenda.fechada_em >= inicio,
                PdvVenda.aberta_em >= inicio,
                PdvVenda.created_at >= inicio,
            )
        )

    if fim:
        query = query.filter(
            or_(
                PdvVenda.fechada_em <= fim,
                PdvVenda.aberta_em <= fim,
                PdvVenda.created_at <= fim,
            )
        )

    if cliente_id:
        query = query.filter(PdvVenda.cliente_id == cliente_id)

    if status_normalizado:
        query = query.filter(PdvVenda.status == status_normalizado)

    if tipo_normalizado:
        query = query.filter(PdvVendaItem.tipo_item == tipo_normalizado)

    if produto_id:
        query = query.filter(PdvVendaItem.produto_id == produto_id)

    if termo:
        termo_like = f"%{str(termo).strip()}%"
        query = query.filter(PdvVendaItem.descricao_snapshot.ilike(termo_like))

    query = query.group_by(
        PdvVendaItem.tipo_item,
        PdvVendaItem.produto_id,
        PdvVendaItem.descricao_snapshot,
    )

    if ordenar_por == "quantidade":
        order_col = func.sum(PdvVendaItem.quantidade)
    elif ordenar_por == "descricao":
        order_col = PdvVendaItem.descricao_snapshot
    else:
        order_col = func.sum(PdvVendaItem.valor_total)

    if ordem == "asc":
        query = query.order_by(order_col.asc())
    else:
        query = query.order_by(order_col.desc())

    limite_seguro = max(1, min(int(limite or 200), 1000))
    rows = query.limit(limite_seguro).all()

    itens = []
    total_quantidade = Decimal("0.000")
    total_valor = Decimal("0.00")
    total_desconto = Decimal("0.00")

    for row in rows:
        quantidade_total = Decimal(str(row.quantidade_total or 0))
        valor_total = _decimal_2(row.valor_total)
        desconto_total = _decimal_2(row.desconto_total)
        ticket_medio = _decimal_2(valor_total / Decimal(str(row.quantidade_vendas or 1)))

        total_quantidade += quantidade_total
        total_valor += valor_total
        total_desconto += desconto_total

        itens.append(
            {
                "tipo_item": row.tipo_item,
                "produto_id": row.produto_id,
                "descricao": row.descricao or "Item sem descrição",
                "quantidade_total": float(quantidade_total),
                "valor_total": float(valor_total),
                "desconto_total": float(desconto_total),
                "quantidade_linhas": int(row.quantidade_linhas or 0),
                "quantidade_vendas": int(row.quantidade_vendas or 0),
                "ticket_medio_por_venda": float(ticket_medio),
            }
        )

    mais_vendidos = sorted(
        itens,
        key=lambda item: (item["quantidade_total"], item["valor_total"]),
        reverse=True,
    )[:10]

    menos_vendidos = sorted(
        itens,
        key=lambda item: (item["quantidade_total"], item["valor_total"]),
    )[:10]

    maior_faturamento = sorted(
        itens,
        key=lambda item: item["valor_total"],
        reverse=True,
    )[:10]

    return {
        "filtros": {
            "empresa_id": empresa_id,
            "data_inicio": inicio.isoformat() if inicio else None,
            "data_fim": fim.isoformat() if fim else None,
            "cliente_id": cliente_id,
            "status": status,
            "tipo_item": tipo_normalizado,
            "produto_id": produto_id,
            "termo": termo,
            "ordenar_por": ordenar_por,
            "ordem": ordem,
            "limite": limite_seguro,
        },
        "resumo": {
            "quantidade_itens_agrupados": len(itens),
            "quantidade_total": float(total_quantidade),
            "valor_total": float(_decimal_2(total_valor)),
            "desconto_total": float(_decimal_2(total_desconto)),
            "mais_vendidos": mais_vendidos,
            "menos_vendidos": menos_vendidos,
            "maior_faturamento": maior_faturamento,
        },
        "itens": itens,
    }
