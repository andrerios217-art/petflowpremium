from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy.orm import Session

from app.models.empresa_categoria_precificacao import EmpresaCategoriaPrecificacao
from app.models.empresa_precificacao_config import EmpresaPrecificacaoConfig

ZERO = Decimal("0.00")
CEM = Decimal("100.00")
PRECO_2 = Decimal("0.01")

MODO_MARKUP = "MARKUP"
MODO_MARGEM = "MARGEM"


@dataclass
class RegraPrecificacaoAplicada:
    origem: str
    modo: str
    percentual: Decimal


def _decimal(valor) -> Decimal:
    if valor is None:
        return ZERO
    return Decimal(str(valor))


def _round_preco(valor: Decimal) -> Decimal:
    return valor.quantize(PRECO_2, rounding=ROUND_HALF_UP)


def _normalizar_modo(valor: str | None) -> str:
    modo = (valor or "").strip().upper()
    if modo not in {MODO_MARKUP, MODO_MARGEM}:
        raise ValueError("Modo de precificação inválido. Use MARKUP ou MARGEM.")
    return modo


def _normalizar_percentual(valor) -> Decimal:
    percentual = _decimal(valor)
    if percentual < ZERO:
        raise ValueError("Percentual de precificação não pode ser negativo.")
    return percentual


def calcular_preco_venda_por_regra(
    custo: Decimal | float | str,
    modo: str,
    percentual: Decimal | float | str,
) -> Decimal:
    custo_decimal = _decimal(custo)
    if custo_decimal < ZERO:
        raise ValueError("Custo não pode ser negativo.")

    modo_normalizado = _normalizar_modo(modo)
    percentual_decimal = _normalizar_percentual(percentual)

    if custo_decimal == ZERO:
        return ZERO

    if percentual_decimal == ZERO:
        return _round_preco(custo_decimal)

    if modo_normalizado == MODO_MARKUP:
        fator = Decimal("1.00") + (percentual_decimal / CEM)
        return _round_preco(custo_decimal * fator)

    if percentual_decimal >= CEM:
        raise ValueError("Percentual de margem deve ser menor que 100.")

    divisor = Decimal("1.00") - (percentual_decimal / CEM)
    if divisor <= ZERO:
        raise ValueError("Percentual de margem inválido para cálculo.")

    return _round_preco(custo_decimal / divisor)


def obter_regra_precificacao(
    db: Session,
    empresa_id: int,
    categoria_id: Optional[int] = None,
) -> Optional[RegraPrecificacaoAplicada]:
    if categoria_id:
        regra_categoria = (
            db.query(EmpresaCategoriaPrecificacao)
            .filter(
                EmpresaCategoriaPrecificacao.empresa_id == empresa_id,
                EmpresaCategoriaPrecificacao.categoria_id == categoria_id,
                EmpresaCategoriaPrecificacao.ativo.is_(True),
            )
            .first()
        )
        if regra_categoria:
            return RegraPrecificacaoAplicada(
                origem="CATEGORIA",
                modo=_normalizar_modo(regra_categoria.modo),
                percentual=_normalizar_percentual(regra_categoria.percentual),
            )

    regra_empresa = (
        db.query(EmpresaPrecificacaoConfig)
        .filter(
            EmpresaPrecificacaoConfig.empresa_id == empresa_id,
            EmpresaPrecificacaoConfig.ativo.is_(True),
        )
        .first()
    )
    if regra_empresa:
        return RegraPrecificacaoAplicada(
            origem="EMPRESA",
            modo=_normalizar_modo(regra_empresa.modo_padrao),
            percentual=_normalizar_percentual(regra_empresa.percentual_padrao),
        )

    return None


def calcular_preco_venda_sugerido(
    db: Session,
    empresa_id: int,
    custo: Decimal | float | str,
    categoria_id: Optional[int] = None,
) -> Decimal:
    regra = obter_regra_precificacao(
        db=db,
        empresa_id=empresa_id,
        categoria_id=categoria_id,
    )
    if not regra:
        return ZERO

    return calcular_preco_venda_por_regra(
        custo=custo,
        modo=regra.modo,
        percentual=regra.percentual,
    )