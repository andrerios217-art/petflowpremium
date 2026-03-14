from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PetProntuarioBase(BaseModel):
    atendimento_id: Optional[int] = None
    pet_id: Optional[int] = None
    exame_fisico: Optional[str] = None
    diagnostico: Optional[str] = None
    conduta: Optional[str] = None
    observacoes: Optional[str] = None


class PetProntuarioCreate(PetProntuarioBase):
    pass


class PetProntuarioUpdate(BaseModel):
    exame_fisico: Optional[str] = None
    diagnostico: Optional[str] = None
    conduta: Optional[str] = None
    observacoes: Optional[str] = None


class PetProntuarioResponse(PetProntuarioBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True