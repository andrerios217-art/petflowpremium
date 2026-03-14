from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PetAnamneseBase(BaseModel):
    atendimento_id: Optional[int] = None
    pet_id: Optional[int] = None
    queixa_principal: Optional[str] = None
    historico_atual: Optional[str] = None
    alimentacao: Optional[str] = None
    alergias: Optional[str] = None
    uso_medicacao_atual: Optional[str] = None
    observacoes: Optional[str] = None


class PetAnamneseCreate(PetAnamneseBase):
    pass


class PetAnamneseUpdate(BaseModel):
    queixa_principal: Optional[str] = None
    historico_atual: Optional[str] = None
    alimentacao: Optional[str] = None
    alergias: Optional[str] = None
    uso_medicacao_atual: Optional[str] = None
    observacoes: Optional[str] = None


class PetAnamneseResponse(PetAnamneseBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True