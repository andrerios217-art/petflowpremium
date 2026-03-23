from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProdutoCategoriaBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=120)
    descricao: Optional[str] = None
    margem_padrao_pct: Optional[Decimal] = None
    ativo: bool = True


class ProdutoCategoriaCreate(ProdutoCategoriaBase):
    pass


class ProdutoCategoriaUpdate(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=1, max_length=120)
    descricao: Optional[str] = None
    margem_padrao_pct: Optional[Decimal] = None
    ativo: Optional[bool] = None


class ProdutoCategoriaOut(ProdutoCategoriaBase):
    id: int
    empresa_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProdutoCodigoBarrasBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=60)
    tipo: str = Field(default="INTERNO", min_length=1, max_length=20)
    principal: bool = False
    ativo: bool = True


class ProdutoCodigoBarrasCreate(ProdutoCodigoBarrasBase):
    produto_id: int


class ProdutoCodigoBarrasOut(ProdutoCodigoBarrasBase):
    id: int
    empresa_id: int
    produto_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProdutoBase(BaseModel):
    categoria_id: Optional[int] = None
    sku: str = Field(..., min_length=1, max_length=60)
    nome: str = Field(..., min_length=1, max_length=150)
    descricao: Optional[str] = None
    unidade: str = Field(default="UN", min_length=1, max_length=20)
    ativo: bool = True
    aceita_fracionado: bool = False
    preco_venda_atual: Decimal = Decimal("0")
    estoque_minimo: Decimal = Decimal("0")
    observacao: Optional[str] = None


class ProdutoCreate(ProdutoBase):
    pass


class ProdutoUpdate(BaseModel):
    categoria_id: Optional[int] = None
    sku: Optional[str] = Field(default=None, min_length=1, max_length=60)
    nome: Optional[str] = Field(default=None, min_length=1, max_length=150)
    descricao: Optional[str] = None
    unidade: Optional[str] = Field(default=None, min_length=1, max_length=20)
    ativo: Optional[bool] = None
    aceita_fracionado: Optional[bool] = None
    preco_venda_atual: Optional[Decimal] = None
    estoque_minimo: Optional[Decimal] = None
    observacao: Optional[str] = None


class EstoqueDepositoBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=120)
    descricao: Optional[str] = None
    padrao: bool = False
    ativo: bool = True


class EstoqueDepositoCreate(EstoqueDepositoBase):
    pass


class EstoqueDepositoUpdate(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=1, max_length=120)
    descricao: Optional[str] = None
    padrao: Optional[bool] = None
    ativo: Optional[bool] = None


class ProdutoOut(BaseModel):
    id: int
    empresa_id: int
    categoria_id: Optional[int]
    sku: str
    nome: str
    descricao: Optional[str]
    unidade: str
    ativo: bool
    aceita_fracionado: bool
    preco_venda_atual: Decimal
    estoque_minimo: Decimal
    observacao: Optional[str]
    created_at: datetime
    updated_at: datetime
    codigos_barras: list[ProdutoCodigoBarrasOut] = []

    model_config = ConfigDict(from_attributes=True)


class EstoqueDepositoOut(EstoqueDepositoBase):
    id: int
    empresa_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EstoqueSaldoOut(BaseModel):
    id: int
    empresa_id: int
    deposito_id: int
    produto_id: int
    quantidade_atual: Decimal
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EstoqueMovimentoOut(BaseModel):
    id: int
    empresa_id: int
    deposito_id: int
    produto_id: int
    usuario_id: Optional[int]
    tipo_movimento: str
    origem: str
    origem_id: Optional[int]
    quantidade: Decimal
    saldo_antes: Decimal
    saldo_depois: Decimal
    custo_unitario: Optional[Decimal]
    documento_referencia: Optional[str]
    observacao: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EstoqueMovimentoEntradaManualIn(BaseModel):
    deposito_id: int
    produto_id: int
    quantidade: Decimal = Field(..., gt=0)
    custo_unitario: Optional[Decimal] = None
    documento_referencia: Optional[str] = Field(default=None, max_length=120)
    observacao: Optional[str] = None


class EstoqueMovimentoAjusteIn(BaseModel):
    deposito_id: int
    produto_id: int
    quantidade_ajuste: Decimal
    documento_referencia: Optional[str] = Field(default=None, max_length=120)
    observacao: Optional[str] = None


class EstoqueTransferenciaIn(BaseModel):
    deposito_origem_id: int
    deposito_destino_id: int
    produto_id: int
    quantidade: Decimal = Field(..., gt=0)
    documento_referencia: Optional[str] = Field(default=None, max_length=120)
    observacao: Optional[str] = None