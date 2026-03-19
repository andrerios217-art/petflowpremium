from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.financeiro_pagar import FinanceiroPagar

router = APIRouter(prefix="/api/financeiro/pagar", tags=["Financeiro Pagar"])


def _serializar(conta: FinanceiroPagar):
    return {
        "id": conta.id,
        "empresa_id": conta.empresa_id,
        "descricao": conta.descricao,
        "fornecedor": conta.fornecedor,
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


@router.get("/")
def listar_contas_pagar(
    empresa_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
):
    contas = (
        db.query(FinanceiroPagar)
        .filter(FinanceiroPagar.empresa_id == empresa_id)
        .order_by(FinanceiroPagar.vencimento.asc(), FinanceiroPagar.id.desc())
        .all()
    )

    hoje = date.today()

    total_pendente = Decimal("0")
    total_pago = Decimal("0")
    total_vencido = Decimal("0")

    quantidade_pendente = 0
    quantidade_paga = 0
    quantidade_vencida = 0

    resultado = []

    for conta in contas:
        status = conta.status

        if status != "PAGO" and conta.vencimento < hoje:
            status = "VENCIDO"

        valor = Decimal(conta.valor or 0)

        if status == "PAGO":
            total_pago += Decimal(conta.valor_pago or 0)
            quantidade_paga += 1
        elif status == "VENCIDO":
            total_vencido += valor
            quantidade_vencida += 1
        else:
            total_pendente += valor
            quantidade_pendente += 1

        resultado.append(_serializar(conta))

    return {
        "empresa_id": empresa_id,
        "resumo": {
            "total_pendente": float(total_pendente),
            "total_pago": float(total_pago),
            "total_vencido": float(total_vencido),
            "quantidade_pendente": quantidade_pendente,
            "quantidade_paga": quantidade_paga,
            "quantidade_vencida": quantidade_vencida,
        },
        "contas": resultado,
    }


@router.post("/")
def criar_conta_pagar(
    payload: dict,
    db: Session = Depends(get_db),
):
    descricao = str(payload.get("descricao") or "").strip()
    fornecedor = str(payload.get("fornecedor") or "").strip() or None
    observacao = str(payload.get("observacao") or "").strip() or None
    valor = payload.get("valor")
    vencimento = payload.get("vencimento")
    empresa_id = payload.get("empresa_id")

    if not empresa_id:
        raise HTTPException(status_code=400, detail="Empresa é obrigatória.")

    if not descricao:
        raise HTTPException(status_code=400, detail="Descrição é obrigatória.")

    if valor in (None, ""):
        raise HTTPException(status_code=400, detail="Valor é obrigatório.")

    try:
        valor_decimal = Decimal(str(valor))
    except Exception:
        raise HTTPException(status_code=400, detail="Valor inválido.")

    if valor_decimal <= 0:
        raise HTTPException(status_code=400, detail="O valor deve ser maior que zero.")

    if not vencimento:
        raise HTTPException(status_code=400, detail="Vencimento é obrigatório.")

    try:
        vencimento_data = date.fromisoformat(vencimento)
    except Exception:
        raise HTTPException(status_code=400, detail="Vencimento inválido. Use YYYY-MM-DD.")

    conta = FinanceiroPagar(
        empresa_id=int(empresa_id),
        descricao=descricao,
        fornecedor=fornecedor,
        observacao=observacao,
        valor=valor_decimal,
        valor_pago=Decimal("0.00"),
        vencimento=vencimento_data,
        status="PENDENTE",
    )

    db.add(conta)
    db.commit()
    db.refresh(conta)

    return _serializar(conta)


@router.post("/{conta_id}/baixar")
def baixar_conta_pagar(
    conta_id: int,
    db: Session = Depends(get_db),
):
    conta = db.query(FinanceiroPagar).filter(FinanceiroPagar.id == conta_id).first()

    if not conta:
        raise HTTPException(status_code=404, detail="Conta não encontrada.")

    if conta.status == "PAGO":
        raise HTTPException(status_code=400, detail="Esta conta já está paga.")

    conta.status = "PAGO"
    conta.data_pagamento = date.today()
    conta.valor_pago = Decimal(conta.valor or 0)

    db.commit()
    db.refresh(conta)

    return {"ok": True}