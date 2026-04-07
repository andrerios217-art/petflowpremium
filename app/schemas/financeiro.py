from datetime import date
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


class FinanceiroPlanoDREBase(BaseModel):
    grupo: str = Field(..., min_length=2, max_length=100)
    categoria: str = Field(..., min_length=2, max_length=100)
    subcategoria: str = Field(..., min_length=2, max_length=100)
    ordem: int = Field(default=0, ge=0)
    ativo: bool = True


class FinanceiroPlanoDRECreate(FinanceiroPlanoDREBase):
    empresa_id: int


class FinanceiroPlanoDREUpdate(BaseModel):
    grupo: str | None = Field(default=None, min_length=2, max_length=100)
    categoria: str | None = Field(default=None, min_length=2, max_length=100)
    subcategoria: str | None = Field(default=None, min_length=2, max_length=100)
    ordem: int | None = Field(default=None, ge=0)
    ativo: bool | None = None


class FinanceiroPlanoDREOut(BaseModel):
    id: int
    empresa_id: int
    grupo: str
    categoria: str
    subcategoria: str
    ordem: int
    ativo: bool
    created_at: str | None = None
    updated_at: str | None = None


class FinanceiroPlanoDREListOut(BaseModel):
    itens: list[FinanceiroPlanoDREOut]


class FinanceiroPagarBase(BaseModel):
    fornecedor: str | None = Field(default=None, max_length=255)
    origem_tipo: str | None = None
    origem_id: int | None = None
    descricao: str = Field(..., min_length=2, max_length=255)
    observacao: str | None = None
    classificacao_dre_id: int | None = Field(default=None, ge=1)
    valor: Decimal = Field(..., gt=0)
    vencimento: date


class FinanceiroPagarCreate(FinanceiroPagarBase):
    empresa_id: int


class FinanceiroPagarBaixa(BaseModel):
    data_pagamento: date | None = None
    valor_pago: Decimal | None = Field(default=None, gt=0)


class FinanceiroPagarOut(BaseModel):
    id: int
    empresa_id: int
    fornecedor: str | None = None
    origem_tipo: str | None
    origem_id: int | None
    descricao: str
    observacao: str | None
    classificacao_dre_id: int | None = None
    grupo_dre: str | None = None
    categoria_dre: str | None = None
    subcategoria_dre: str | None = None
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


class FinanceiroPagarListOut(BaseModel):
    empresa_id: int
    resumo: FinanceiroResumoOut
    contas: list[FinanceiroPagarOut]