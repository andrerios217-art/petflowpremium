from pydantic import BaseModel, Field


class ServicoCreate(BaseModel):

    empresa_id: int

    nome: str = Field(..., min_length=2)

    porte_referencia: str = Field(...)

    custo: float = Field(..., gt=0)

    venda: float = Field(..., gt=0)

    tempo_minutos: int = Field(..., gt=0)


class ServicoOut(BaseModel):

    id: int
    empresa_id: int

    nome: str
    porte_referencia: str

    custo: float
    venda: float

    tempo_minutos: int

    ativo: bool

    class Config:
        from_attributes = True