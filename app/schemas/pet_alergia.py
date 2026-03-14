from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PetAlergiaBase(BaseModel):
    pet_id: Optional[int] = None
    nome: Optional[str] = None
    tipo: Optional[str] = None
    gravidade: Optional[str] = None
    observacoes: Optional[str] = None


class PetAlergiaCreate(PetAlergiaBase):
    nome: str
    pet_id: int


class PetAlergiaUpdate(BaseModel):
    nome: Optional[str] = None
    tipo: Optional[str] = None
    gravidade: Optional[str] = None
    observacoes: Optional[str] = None


class PetAlergiaResponse(PetAlergiaBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True