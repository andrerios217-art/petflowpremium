from datetime import date
from decimal import Decimal

from app.db.session import SessionLocal
from app.models.financeiro_pagar import FinanceiroPagar
from app.models.financeiro_receber import FinanceiroReceber


EMPRESA_ID = 2
PREFIXOS = [
    "[DEMO CONCILIAÇÃO]",
    "[DEMO SUGESTAO CONCILIACAO]",
    "[DEMO SUGESTÃO CONCILIAÇÃO]",
]


def mostrar_contas(modelo, nome):
    db = SessionLocal()

    try:
        print("")
        print("=" * 80)
        print(nome)
        print("=" * 80)

        query = db.query(modelo).filter(modelo.empresa_id == EMPRESA_ID)

        condicoes = []
        for prefixo in PREFIXOS:
            condicoes.append(modelo.descricao.like(f"{prefixo}%"))

        from sqlalchemy import or_
        query = query.filter(or_(*condicoes))

        contas = (
            query
            .order_by(modelo.data_pagamento.asc(), modelo.valor.asc(), modelo.id.asc())
            .limit(80)
            .all()
        )

        print(f"Total encontrado: {len(contas)}")

        for conta in contas:
            print(
                f"id={conta.id} | data_pagamento={getattr(conta, 'data_pagamento', None)} | "
                f"valor={getattr(conta, 'valor', None)} | valor_pago={getattr(conta, 'valor_pago', None)} | "
                f"status={getattr(conta, 'status', None)} | descricao={getattr(conta, 'descricao', '')}"
            )

    finally:
        db.close()


def buscar_valores_chave():
    db = SessionLocal()

    try:
        valores = [
            Decimal("73.50"),
            Decimal("115.27"),
            Decimal("373.29"),
            Decimal("12.00"),
            Decimal("500.00"),
            Decimal("135.00"),
            Decimal("99.90"),
            Decimal("410.00"),
            Decimal("101.58"),
            Decimal("36.00"),
            Decimal("156.51"),
            Decimal("200.20"),
            Decimal("66.90"),
            Decimal("313.01"),
        ]

        print("")
        print("=" * 80)
        print("BUSCA POR VALORES-CHAVE")
        print("=" * 80)

        for valor in valores:
            pagar = (
                db.query(FinanceiroPagar)
                .filter(FinanceiroPagar.empresa_id == EMPRESA_ID)
                .filter(FinanceiroPagar.status == "PAGO")
                .filter(FinanceiroPagar.valor == valor)
                .all()
            )

            receber = (
                db.query(FinanceiroReceber)
                .filter(FinanceiroReceber.empresa_id == EMPRESA_ID)
                .filter(FinanceiroReceber.status == "PAGO")
                .filter(FinanceiroReceber.valor == valor)
                .all()
            )

            print(f"Valor {valor}: pagar={len(pagar)} | receber={len(receber)}")

            for conta in pagar[:3]:
                print(f"  SAÍDA   id={conta.id} data={conta.data_pagamento} descricao={conta.descricao}")

            for conta in receber[:3]:
                print(f"  ENTRADA id={conta.id} data={conta.data_pagamento} descricao={conta.descricao}")

    finally:
        db.close()


mostrar_contas(FinanceiroPagar, "SAÍDAS DEMO")
mostrar_contas(FinanceiroReceber, "ENTRADAS DEMO")
buscar_valores_chave()
