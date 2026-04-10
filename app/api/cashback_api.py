from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.cashback_configuracao import CashbackConfiguracao
from app.models.cashback_lancamento import CashbackLancamento
from app.models.cliente import Cliente
from app.models.empresa import Empresa

DECIMAL_2 = Decimal("0.01")


def _decimal_2(valor) -> Decimal:
    if valor is None:
        return Decimal("0.00")
    return Decimal(str(valor)).quantize(DECIMAL_2, rounding=ROUND_HALF_UP)


def _get_empresa_or_404(db: Session, empresa_id: int) -> Empresa:
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    return empresa


def _get_cliente_or_404(db: Session, cliente_id: int) -> Cliente:
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    return cliente


def obter_configuracao_cashback(db: Session, empresa_id: int) -> CashbackConfiguracao | None:
    _get_empresa_or_404(db, empresa_id)

    return (
        db.query(CashbackConfiguracao)
        .filter(CashbackConfiguracao.empresa_id == empresa_id)
        .first()
    )


def criar_ou_obter_configuracao_cashback(
    db: Session,
    empresa_id: int,
) -> CashbackConfiguracao:
    _get_empresa_or_404(db, empresa_id)

    config = (
        db.query(CashbackConfiguracao)
        .filter(CashbackConfiguracao.empresa_id == empresa_id)
        .first()
    )
    if config:
        return config

    config = CashbackConfiguracao(
        empresa_id=empresa_id,
        ativo=False,
        percentual_cashback=Decimal("0.00"),
        valor_minimo_venda=Decimal("0.00"),
        dias_validade=None,
        permite_uso_no_pdv=True,
        acumula_com_desconto=False,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def atualizar_configuracao_cashback(
    db: Session,
    empresa_id: int,
    *,
    ativo: bool | None = None,
    percentual_cashback: Decimal | None = None,
    valor_minimo_venda: Decimal | None = None,
    dias_validade: int | None = None,
    permite_uso_no_pdv: bool | None = None,
    acumula_com_desconto: bool | None = None,
) -> CashbackConfiguracao:
    config = criar_ou_obter_configuracao_cashback(db, empresa_id)

    if ativo is not None:
        config.ativo = ativo

    if percentual_cashback is not None:
        percentual = _decimal_2(percentual_cashback)
        if percentual < Decimal("0.00") or percentual > Decimal("100.00"):
            raise HTTPException(status_code=400, detail="percentual_cashback deve estar entre 0 e 100.")
        config.percentual_cashback = percentual

    if valor_minimo_venda is not None:
        valor_minimo = _decimal_2(valor_minimo_venda)
        if valor_minimo < Decimal("0.00"):
            raise HTTPException(status_code=400, detail="valor_minimo_venda não pode ser negativo.")
        config.valor_minimo_venda = valor_minimo

    if dias_validade is not None:
        if dias_validade < 0:
            raise HTTPException(status_code=400, detail="dias_validade não pode ser negativo.")
        config.dias_validade = dias_validade

    if permite_uso_no_pdv is not None:
        config.permite_uso_no_pdv = permite_uso_no_pdv

    if acumula_com_desconto is not None:
        config.acumula_com_desconto = acumula_com_desconto

    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def obter_extrato_cashback_cliente(
    db: Session,
    empresa_id: int,
    cliente_id: int,
) -> dict:
    _get_empresa_or_404(db, empresa_id)
    cliente = _get_cliente_or_404(db, cliente_id)

    if cliente.empresa_id != empresa_id:
        raise HTTPException(status_code=400, detail="Cliente não pertence à empresa informada.")

    lancamentos = (
        db.query(CashbackLancamento)
        .filter(
            CashbackLancamento.empresa_id == empresa_id,
            CashbackLancamento.cliente_id == cliente_id,
        )
        .order_by(CashbackLancamento.id.desc())
        .all()
    )

    return {
        "cliente_id": cliente.id,
        "saldo_atual": _decimal_2(getattr(cliente, "saldo_cashback", Decimal("0.00"))),
        "lancamentos": lancamentos,
    }
