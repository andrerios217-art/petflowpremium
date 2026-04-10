from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CashbackConfiguracaoBase(BaseModel):
    ativo: bool = False
    percentual_cashback: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    valor_minimo_venda: Decimal = Field(default=Decimal("0.00"), ge=0)
    dias_validade: int | None = Field(default=None, ge=0)
    permite_uso_no_pdv: bool = True
    acumula_com_desconto: bool = False


class CashbackConfiguracaoCreate(CashbackConfiguracaoBase):
    empresa_id: int


class CashbackConfiguracaoUpdate(BaseModel):
    ativo: bool | None = None
    percentual_cashback: Decimal | None = Field(default=None, ge=0, le=100)
    valor_minimo_venda: Decimal | None = Field(default=None, ge=0)
    dias_validade: int | None = Field(default=None, ge=0)
    permite_uso_no_pdv: bool | None = None
    acumula_com_desconto: bool | None = None


class CashbackConfiguracaoOut(CashbackConfiguracaoBase):
    id: int
    empresa_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CashbackLancamentoOut(BaseModel):
    id: int
    empresa_id: int
    cliente_id: int
    venda_id: int | None = None
    tipo: str
    origem: str
    valor: Decimal
    saldo_apos: Decimal
    expira_em: datetime | None = None
    observacao: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class CashbackExtratoResponse(BaseModel):
    cliente_id: int
    saldo_atual: Decimal
    lancamentos: list[CashbackLancamentoOut]