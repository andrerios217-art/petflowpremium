from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PetVacinaBase(BaseModel):
    atendimento_id: Optional[int] = None
    pet_id: Optional[int] = None
    nome: Optional[str] = None
    fabricante: Optional[str] = None
    lote: Optional[str] = None
    data_aplicacao: Optional[datetime] = None
    data_reforco: Optional[datetime] = None
    observacoes: Optional[str] = None


class PetVacinaCreate(PetVacinaBase):
    nome: str


class PetVacinaUpdate(BaseModel):
    nome: Optional[str] = None
    fabricante: Optional[str] = None
    lote: Optional[str] = None
    data_aplicacao: Optional[datetime] = None
    data_reforco: Optional[datetime] = None
    observacoes: Optional[str] = None


class PetVacinaResponse(PetVacinaBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True