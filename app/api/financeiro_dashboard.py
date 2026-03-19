from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.deps import get_db
from app.models.financeiro_receber import FinanceiroReceber

router = APIRouter(prefix="/api/financeiro/dashboard", tags=["Financeiro Dashboard"])


@router.get("/")
def dashboard_financeiro(empresa_id: int, db: Session = Depends(get_db)):
    hoje = date.today()

    # 🔹 Caixa do dia
    total_hoje = db.query(func.coalesce(func.sum(FinanceiroReceber.valor_pago), 0)) \
        .filter(
            FinanceiroReceber.empresa_id == empresa_id,
            FinanceiroReceber.data_pagamento == hoje
        ).scalar()

    # 🔹 Pendentes hoje
    pendente_hoje = db.query(func.coalesce(func.sum(FinanceiroReceber.valor), 0)) \
        .filter(
            FinanceiroReceber.empresa_id == empresa_id,
            FinanceiroReceber.vencimento == hoje,
            FinanceiroReceber.status != "PAGO"
        ).scalar()

    # 🔹 Vencidos
    vencidos = db.query(func.coalesce(func.sum(FinanceiroReceber.valor), 0)) \
        .filter(
            FinanceiroReceber.empresa_id == empresa_id,
            FinanceiroReceber.vencimento < hoje,
            FinanceiroReceber.status != "PAGO"
        ).scalar()

    # 🔹 Últimos 7 dias (gráfico)
    dias = []
    for i in range(6, -1, -1):
        dia = hoje - timedelta(days=i)

        total = db.query(func.coalesce(func.sum(FinanceiroReceber.valor_pago), 0)) \
            .filter(
                FinanceiroReceber.empresa_id == empresa_id,
                FinanceiroReceber.data_pagamento == dia
            ).scalar()

        dias.append({
            "data": dia.isoformat(),
            "valor": float(total)
        })

    return {
        "caixa_hoje": float(total_hoje),
        "pendente_hoje": float(pendente_hoje),
        "vencido": float(vencidos),
        "grafico_7_dias": dias
    }