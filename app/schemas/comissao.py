from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class ComissaoFaixaBase(BaseModel):
    ordem: int = Field(default=1, ge=1)
    pontos_min: int = Field(..., ge=0)
    pontos_max: Optional[int] = Field(default=None, ge=0)
    valor_reais: Decimal = Field(..., ge=0)


class ComissaoFaixaCreate(ComissaoFaixaBase):
    pass


class ComissaoFaixaOut(ComissaoFaixaBase):
    id: Optional[int] = None
    ativo: bool = True

    class Config:
        orm_mode = True
        from_attributes = True


class ComissaoConfiguracaoUpsert(BaseModel):
    empresa_id: int = Field(..., ge=1)
    pontos_banho: int = Field(default=0, ge=0)
    pontos_tosa: int = Field(default=0, ge=0)
    pontos_tosa_higienica: int = Field(default=0, ge=0)
    pontos_finalizacao: int = Field(default=0, ge=0)
    dias_trabalhados_mes: int = Field(default=26, ge=1)
    responsavel_aprovacao: Optional[str] = None
    faixas: list[ComissaoFaixaCreate] = Field(default_factory=list)


class ComissaoConfiguracaoOut(BaseModel):
    id: Optional[int] = None
    empresa_id: int
    pontos_banho: int = 0
    pontos_tosa: int = 0
    pontos_tosa_higienica: int = 0
    pontos_finalizacao: int = 0
    dias_trabalhados_mes: int = 26
    responsavel_aprovacao: Optional[str] = None
    faixas: list[ComissaoFaixaOut] = Field(default_factory=list)

    class Config:
        orm_mode = True
        from_attributes = True