from pydantic import BaseModel, Field
from typing import Optional


# ==========================================================
# TIPOS DE SERVIÇO
# ==========================================================

TIPOS_SERVICO = [
    "PETSHOP",      # banho, tosa, hidratação etc
    "VETERINARIO",  # consulta, vacina, procedimento
]


# ==========================================================
# CRIAÇÃO DE SERVIÇO
# ==========================================================

class ServicoCreate(BaseModel):

    empresa_id: int

    nome: str = Field(..., min_length=2)

    # PETSHOP ou VETERINARIO
    tipo_servico: str = Field(default="PETSHOP")

    # porte é obrigatório apenas para PETSHOP
    porte_referencia: Optional[str] = None

    custo: float = Field(..., gt=0)

    venda: float = Field(..., gt=0)

    tempo_minutos: int = Field(..., gt=0)


# ==========================================================
# ATUALIZAÇÃO DE SERVIÇO
# ==========================================================

class ServicoUpdate(BaseModel):

    nome: Optional[str] = Field(None, min_length=2)

    tipo_servico: Optional[str] = None

    porte_referencia: Optional[str] = None

    custo: Optional[float] = Field(None, gt=0)

    venda: Optional[float] = Field(None, gt=0)

    tempo_minutos: Optional[int] = Field(None, gt=0)

    ativo: Optional[bool] = None


# ==========================================================
# RETORNO DE SERVIÇO
# ==========================================================

class ServicoOut(BaseModel):

    id: int
    empresa_id: int

    nome: str

    tipo_servico: str

    porte_referencia: Optional[str] = None

    custo: float
    venda: float

    tempo_minutos: int

    ativo: bool

    class Config:
        from_attributes = True