from typing import Optional

from pydantic import BaseModel, Field


class EmpresaCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=150)
    cnpj: Optional[str] = Field(default=None, max_length=18)
    logo_url: Optional[str] = Field(default=None, max_length=255)


class EmpresaOut(BaseModel):
    id: int
    nome: str
    cnpj: Optional[str] = None
    logo_url: Optional[str] = None
    ativa: bool

    class Config:
        from_attributes = True