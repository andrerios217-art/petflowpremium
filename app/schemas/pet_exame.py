from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PetExameBase(BaseModel):
    atendimento_id: Optional[int] = None
    pet_id: Optional[int] = None
    nome: Optional[str] = None
    tipo: Optional[str] = None
    status: Optional[str] = "SOLICITADO"
    resultado: Optional[str] = None
    observacoes: Optional[str] = None


class PetExameCreate(PetExameBase):
    nome: str


class PetExameUpdate(BaseModel):
    nome: Optional[str] = None
    tipo: Optional[str] = None
    status: Optional[str] = None
    resultado: Optional[str] = None
    observacoes: Optional[str] = None


class PetExameResponse(PetExameBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True