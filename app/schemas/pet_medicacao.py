from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PetMedicacaoBase(BaseModel):
    atendimento_id: Optional[int] = None
    pet_id: Optional[int] = None
    nome: Optional[str] = None
    dosagem: Optional[str] = None
    via_administracao: Optional[str] = None
    frequencia: Optional[str] = None
    duracao: Optional[str] = None
    observacoes: Optional[str] = None


class PetMedicacaoCreate(PetMedicacaoBase):
    nome: str


class PetMedicacaoUpdate(BaseModel):
    nome: Optional[str] = None
    dosagem: Optional[str] = None
    via_administracao: Optional[str] = None
    frequencia: Optional[str] = None
    duracao: Optional[str] = None
    observacoes: Optional[str] = None


class PetMedicacaoResponse(PetMedicacaoBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True