from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.financeiro_pagar import FinanceiroPagar
from app.models.financeiro_receber import FinanceiroReceber


def _to_float(valor) -> float:
    return float(valor or 0)


def _somar_recebidos_ate(db: Session, empresa_id: int, data_limite: date) -> Decimal:
    contas = (
        db.query(FinanceiroReceber)
        .filter(
            FinanceiroReceber.empresa_id == empresa_id,
            FinanceiroReceber.status == "PAGO",
            FinanceiroReceber.data_pagamento <= data_limite,
        )
        .all()
    )

    return sum((conta.valor_pago or Decimal("0.00")) for conta in contas)


def _somar_pagos_ate(db: Session, empresa_id: int, data_limite: date) -> Decimal:
    contas = (
        db.query(FinanceiroPagar)
        .filter(
            FinanceiroPagar.empresa_id == empresa_id,
            FinanceiroPagar.status == "PAGO",
            FinanceiroPagar.data_pagamento <= data_limite,
        )
        .all()
    )

    return sum((conta.valor_pago or Decimal("0.00")) for conta in contas)


def calcular_saldo_ate(db: Session, empresa_id: int, data_limite: date) -> Decimal:
    entradas = _somar_recebidos_ate(db, empresa_id, data_limite)
    saidas = _somar_pagos_ate(db, empresa_id, data_limite)
    return entradas - saidas


def obter_resumo_fluxo_caixa(
    db: Session,
    empresa_id: int,
    data_inicial: date,
    data_final: date,
) -> dict:
    saldo_inicial = calcular_saldo_ate(
        db=db,
        empresa_id=empresa_id,
        data_limite=data_inicial - timedelta(days=1),
    )

    recebimentos = (
        db.query(FinanceiroReceber)
        .filter(
            FinanceiroReceber.empresa_id == empresa_id,
            FinanceiroReceber.status == "PAGO",
            FinanceiroReceber.data_pagamento >= data_inicial,
            FinanceiroReceber.data_pagamento <= data_final,
        )
        .all()
    )

    pagamentos = (
        db.query(FinanceiroPagar)
        .filter(
            FinanceiroPagar.empresa_id == empresa_id,
            FinanceiroPagar.status == "PAGO",
            FinanceiroPagar.data_pagamento >= data_inicial,
            FinanceiroPagar.data_pagamento <= data_final,
        )
        .all()
    )

    total_entradas = sum((conta.valor_pago or Decimal("0.00")) for conta in recebimentos)
    total_saidas = sum((conta.valor_pago or Decimal("0.00")) for conta in pagamentos)

    saldo_final = saldo_inicial + total_entradas - total_saidas

    return {
        "saldo_inicial": _to_float(saldo_inicial),
        "total_entradas": _to_float(total_entradas),
        "total_saidas": _to_float(total_saidas),
        "saldo_final": _to_float(saldo_final),
    }


def obter_extrato_fluxo_caixa(
    db: Session,
    empresa_id: int,
    data_inicial: date,
    data_final: date,
) -> dict:
    saldo_inicial = calcular_saldo_ate(
        db=db,
        empresa_id=empresa_id,
        data_limite=data_inicial - timedelta(days=1),
    )

    movimentos = []

    recebimentos = (
        db.query(FinanceiroReceber)
        .filter(
            FinanceiroReceber.empresa_id == empresa_id,
            FinanceiroReceber.status == "PAGO",
            FinanceiroReceber.data_pagamento >= data_inicial,
            FinanceiroReceber.data_pagamento <= data_final,
        )
        .order_by(FinanceiroReceber.data_pagamento.asc(), FinanceiroReceber.id.asc())
        .all()
    )

    for conta in recebimentos:
        movimentos.append(
            {
                "data": conta.data_pagamento,
                "tipo": "ENTRADA",
                "descricao": conta.descricao,
                "forma_pagamento": None,
                "entrada": conta.valor_pago or Decimal("0.00"),
                "saida": Decimal("0.00"),
                "origem_id": conta.id,
            }
        )

    pagamentos = (
        db.query(FinanceiroPagar)
        .filter(
            FinanceiroPagar.empresa_id == empresa_id,
            FinanceiroPagar.status == "PAGO",
            FinanceiroPagar.data_pagamento >= data_inicial,
            FinanceiroPagar.data_pagamento <= data_final,
        )
        .order_by(FinanceiroPagar.data_pagamento.asc(), FinanceiroPagar.id.asc())
        .all()
    )

    for conta in pagamentos:
        movimentos.append(
            {
                "data": conta.data_pagamento,
                "tipo": "SAIDA",
                "descricao": conta.descricao,
                "forma_pagamento": conta.forma_pagamento,
                "entrada": Decimal("0.00"),
                "saida": conta.valor_pago or Decimal("0.00"),
                "origem_id": conta.id,
            }
        )

    movimentos.sort(
        key=lambda item: (
            item["data"] or date.min,
            0 if item["tipo"] == "ENTRADA" else 1,
            item["origem_id"],
        )
    )

    saldo = saldo_inicial
    movimentos_saida = []

    for item in movimentos:
        saldo = saldo + item["entrada"] - item["saida"]

        movimentos_saida.append(
            {
                "data": item["data"],
                "tipo": item["tipo"],
                "descricao": item["descricao"],
                "forma_pagamento": item["forma_pagamento"],
                "entrada": _to_float(item["entrada"]),
                "saida": _to_float(item["saida"]),
                "saldo": _to_float(saldo),
            }
        )

    return {
        "empresa_id": empresa_id,
        "data_inicial": data_inicial,
        "data_final": data_final,
        "saldo_inicial": _to_float(saldo_inicial),
        "saldo_final": _to_float(saldo),
        "movimentos": movimentos_saida,
    }


def obter_previsao_fluxo_caixa(
    db: Session,
    empresa_id: int,
    dias: int,
) -> dict:
    hoje = date.today()
    saldo_atual = calcular_saldo_ate(
        db=db,
        empresa_id=empresa_id,
        data_limite=hoje,
    )

    saldo_previsto = saldo_atual
    previsoes = []

    for i in range(1, dias + 1):
        dia = hoje + timedelta(days=i)

        contas_receber = (
            db.query(FinanceiroReceber)
            .filter(
                FinanceiroReceber.empresa_id == empresa_id,
                FinanceiroReceber.status == "PENDENTE",
                FinanceiroReceber.vencimento == dia,
            )
            .all()
        )

        contas_pagar = (
            db.query(FinanceiroPagar)
            .filter(
                FinanceiroPagar.empresa_id == empresa_id,
                FinanceiroPagar.status == "PENDENTE",
                FinanceiroPagar.vencimento == dia,
            )
            .all()
        )

        receber = sum((conta.valor or Decimal("0.00")) for conta in contas_receber)
        pagar = sum((conta.valor or Decimal("0.00")) for conta in contas_pagar)

        saldo_previsto = saldo_previsto + receber - pagar

        previsoes.append(
            {
                "data": dia,
                "receber": _to_float(receber),
                "pagar": _to_float(pagar),
                "saldo_previsto": _to_float(saldo_previsto),
            }
        )

    return {
        "empresa_id": empresa_id,
        "dias": dias,
        "saldo_atual": _to_float(saldo_atual),
        "previsoes": previsoes,
    }
