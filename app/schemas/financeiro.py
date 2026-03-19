from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class FinanceiroReceberBase(BaseModel):
    cliente_id: int | None = None
    origem_tipo: str | None = None
    origem_id: int | None = None
    descricao: str = Field(..., min_length=2, max_length=255)
    observacao: str | None = None
    valor: Decimal = Field(..., gt=0)
    vencimento: date


class FinanceiroReceberCreate(FinanceiroReceberBase):
    empresa_id: int


class FinanceiroReceberBaixa(BaseModel):
    data_pagamento: date | None = None
    valor_pago: Decimal | None = Field(default=None, gt=0)


class FinanceiroReceberOut(BaseModel):
    id: int
    empresa_id: int
    cliente_id: int | None
    cliente_nome: str | None = None

    origem_tipo: str | None
    origem_id: int | None

    descricao: str
    observacao: str | None

    valor: float
    valor_pago: float

    vencimento: str | None
    data_pagamento: str | None

    status: str
    status_atual: str
    esta_vencido: bool

    created_at: str | None = None
    updated_at: str | None = None


class FinanceiroResumoOut(BaseModel):
    total_pendente: float
    total_pago: float
    total_vencido: float
    quantidade_pendente: int
    quantidade_paga: int
    quantidade_vencida: int


class FinanceiroReceberListOut(BaseModel):
    empresa_id: int
    resumo: FinanceiroResumoOut
    contas: list[FinanceiroReceberOut]