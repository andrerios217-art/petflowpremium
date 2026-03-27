from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


MODOS_PRECIFICACAO = {"MARKUP", "MARGEM"}


class EmpresaPrecificacaoConfigBase(BaseModel):
    modo_padrao: str = Field(default="MARKUP")
    percentual_padrao: Decimal = Field(default=Decimal("0.00"))
    ativo: bool = True

    @field_validator("modo_padrao")
    @classmethod
    def validar_modo_padrao(cls, value: str) -> str:
        modo = (value or "").strip().upper()
        if modo not in MODOS_PRECIFICACAO:
            raise ValueError("Modo inválido. Use MARKUP ou MARGEM.")
        return modo

    @field_validator("percentual_padrao")
    @classmethod
    def validar_percentual_padrao(cls, value: Decimal) -> Decimal:
        percentual = Decimal(str(value))
        if percentual < 0:
            raise ValueError("Percentual não pode ser negativo.")
        if percentual >= 100 and cls.__name__ == "EmpresaPrecificacaoConfigBase":
            return percentual
        return percentual


class EmpresaPrecificacaoConfigUpsertIn(EmpresaPrecificacaoConfigBase):
    pass


class EmpresaPrecificacaoConfigOut(BaseModel):
    id: int
    empresa_id: int
    modo_padrao: str
    percentual_padrao: Decimal
    ativo: bool

    model_config = ConfigDict(from_attributes=True)


class EmpresaCategoriaPrecificacaoBase(BaseModel):
    categoria_id: int
    modo: str = Field(default="MARKUP")
    percentual: Decimal = Field(default=Decimal("0.00"))
    ativo: bool = True

    @field_validator("modo")
    @classmethod
    def validar_modo(cls, value: str) -> str:
        modo = (value or "").strip().upper()
        if modo not in MODOS_PRECIFICACAO:
            raise ValueError("Modo inválido. Use MARKUP ou MARGEM.")
        return modo

    @field_validator("percentual")
    @classmethod
    def validar_percentual(cls, value: Decimal) -> Decimal:
        percentual = Decimal(str(value))
        if percentual < 0:
            raise ValueError("Percentual não pode ser negativo.")
        return percentual


class EmpresaCategoriaPrecificacaoUpsertIn(EmpresaCategoriaPrecificacaoBase):
    pass


class EmpresaCategoriaPrecificacaoOut(BaseModel):
    id: int
    empresa_id: int
    categoria_id: int
    modo: str
    percentual: Decimal
    ativo: bool
    categoria_nome: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PrecificacaoConfigTelaOut(BaseModel):
    config_padrao: Optional[EmpresaPrecificacaoConfigOut] = None
    regras_categoria: list[EmpresaCategoriaPrecificacaoOut] = Field(default_factory=list)