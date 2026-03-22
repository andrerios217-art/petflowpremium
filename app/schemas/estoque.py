from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ProdutoCategoriaCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=120)
    descricao: Optional[str] = None
    margem_padrao_pct: Optional[Decimal] = None
    ativo: bool = True


class ProdutoCategoriaUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=120)
    descricao: Optional[str] = None
    margem_padrao_pct: Optional[Decimal] = None
    ativo: Optional[bool] = None


class ProdutoCategoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    empresa_id: int
    nome: str
    descricao: Optional[str]
    margem_padrao_pct: Optional[Decimal]
    ativo: bool
    created_at: datetime
    updated_at: datetime


class ProdutoCreate(BaseModel):
    categoria_id: Optional[int] = None
    sku: str = Field(..., min_length=1, max_length=60)
    nome: str = Field(..., min_length=1, max_length=150)
    descricao: Optional[str] = None
    unidade: str = Field(default="UN", min_length=1, max_length=20)
    ativo: bool = True
    aceita_fracionado: bool = False
    preco_venda_atual: Decimal = Field(default=Decimal("0"))
    estoque_minimo: Decimal = Field(default=Decimal("0"))
    observacao: Optional[str] = None


class ProdutoUpdate(BaseModel):
    categoria_id: Optional[int] = None
    sku: Optional[str] = Field(None, min_length=1, max_length=60)
    nome: Optional[str] = Field(None, min_length=1, max_length=150)
    descricao: Optional[str] = None
    unidade: Optional[str] = Field(None, min_length=1, max_length=20)
    ativo: Optional[bool] = None
    aceita_fracionado: Optional[bool] = None
    preco_venda_atual: Optional[Decimal] = None
    estoque_minimo: Optional[Decimal] = None
    observacao: Optional[str] = None


class ProdutoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class ProdutoCodigoBarrasCreate(BaseModel):
    produto_id: int
    codigo: str = Field(..., min_length=1, max_length=60)
    tipo: str = Field(default="INTERNO", min_length=1, max_length=20)
    principal: bool = False
    ativo: bool = True


class ProdutoCodigoBarrasOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    empresa_id: int
    produto_id: int
    codigo: str
    tipo: str
    principal: bool
    ativo: bool
    created_at: datetime


class EstoqueDepositoCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=120)
    descricao: Optional[str] = None
    padrao: bool = False
    ativo: bool = True


class EstoqueDepositoUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=120)
    descricao: Optional[str] = None
    padrao: Optional[bool] = None
    ativo: Optional[bool] = None


class EstoqueDepositoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    empresa_id: int
    nome: str
    descricao: Optional[str]
    padrao: bool
    ativo: bool
    created_at: datetime
    updated_at: datetime


class EstoqueSaldoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    empresa_id: int
    deposito_id: int
    produto_id: int
    quantidade_atual: Decimal
    updated_at: datetime


class EstoqueMovimentoEntradaManualIn(BaseModel):
    produto_id: int
    deposito_id: Optional[int] = None
    quantidade: Decimal = Field(..., gt=0)
    custo_unitario: Optional[Decimal] = None
    documento_referencia: Optional[str] = Field(None, max_length=120)
    observacao: Optional[str] = None


class EstoqueMovimentoAjusteIn(BaseModel):
    produto_id: int
    deposito_id: Optional[int] = None
    quantidade: Decimal = Field(..., gt=0)
    tipo_movimento: str = Field(..., pattern="^(ENTRADA|SAIDA)$")
    observacao: Optional[str] = None
    documento_referencia: Optional[str] = Field(None, max_length=120)


class EstoqueMovimentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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