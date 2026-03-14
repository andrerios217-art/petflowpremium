from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PetReceitaBase(BaseModel):
    atendimento_id: Optional[int] = None
    pet_id: Optional[int] = None
    descricao: Optional[str] = None
    orientacoes: Optional[str] = None


class PetReceitaCreate(PetReceitaBase):
    descricao: str


class PetReceitaUpdate(BaseModel):
    descricao: Optional[str] = None
    orientacoes: Optional[str] = None


class PetReceitaResponse(PetReceitaBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True