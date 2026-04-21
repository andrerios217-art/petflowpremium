from typing import Optional

from pydantic import BaseModel, Field


class EmpresaCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=150)
    cnpj: Optional[str] = Field(default=None, max_length=18)

    razao_social: Optional[str] = Field(default=None, max_length=180)
    nome_fantasia: Optional[str] = Field(default=None, max_length=180)

    telefone: Optional[str] = Field(default=None, max_length=25)
    email: Optional[str] = Field(default=None, max_length=150)

    cep: Optional[str] = Field(default=None, max_length=10)
    logradouro: Optional[str] = Field(default=None, max_length=180)
    numero: Optional[str] = Field(default=None, max_length=20)
    complemento: Optional[str] = Field(default=None, max_length=120)
    bairro: Optional[str] = Field(default=None, max_length=120)
    cidade: Optional[str] = Field(default=None, max_length=120)
    uf: Optional[str] = Field(default=None, max_length=2)

    endereco_loja: Optional[str] = Field(default=None, max_length=255)

    logo_url: Optional[str] = Field(default=None, max_length=255)


class EmpresaOut(BaseModel):
    id: int
    nome: str
    cnpj: Optional[str] = None

    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None

    telefone: Optional[str] = None
    email: Optional[str] = None

    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None

    endereco_loja: Optional[str] = None

    logo_url: Optional[str] = None
    ativa: bool

    class Config:
        from_attributes = True