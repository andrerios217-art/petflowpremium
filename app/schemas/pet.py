from datetime import date
from pydantic import BaseModel


class PetCreate(BaseModel):
    empresa_id: int
    cliente_id: int
    nome: str
    nascimento: date | None = None
    raca: str | None = None
    sexo: str | None = None
    temperamento: str | None = None
    peso: float | None = None
    porte: str | None = None
    observacoes: str | None = None
    pode_perfume: bool = True
    pode_acessorio: bool = True
    castrado: bool = False
    foto: str | None = None


class PetOut(BaseModel):
    id: int
    empresa_id: int
    cliente_id: int
    nome: str
    nascimento: date | None = None
    raca: str | None = None
    sexo: str | None = None
    temperamento: str | None = None
    peso: float | None = None
    porte: str | None = None
    observacoes: str | None = None
    pode_perfume: bool
    pode_acessorio: bool
    castrado: bool
    foto: str | None = None
    ativo: bool

    class Config:
        from_attributes = True