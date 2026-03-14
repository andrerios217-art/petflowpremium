from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.pet_anamnese import PetAnamneseResponse, PetAnamneseUpdate
from app.schemas.pet_prontuario import PetProntuarioResponse, PetProntuarioUpdate


class AtendimentoClinicoBase(BaseModel):
    observacoes_recepcao: Optional[str] = None
    observacoes_clinicas: Optional[str] = None


class AtendimentoClinicoIniciar(BaseModel):
    empresa_id: int
    agendamento_id: Optional[int] = None
    pet_id: int
    cliente_id: int
    veterinario_id: Optional[int] = None
    observacoes_recepcao: Optional[str] = None


class AtendimentoClinicoResponse(BaseModel):
    id: int
    empresa_id: int
    agendamento_id: Optional[int] = None
    pet_id: int
    cliente_id: int
    veterinario_id: Optional[int] = None
    status: str
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    observacoes_recepcao: Optional[str] = None
    observacoes_clinicas: Optional[str] = None
    enviado_pdv: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AtendimentoClinicoItemCreate(BaseModel):
    servico_id: Optional[int] = None
    descricao: str = Field(..., min_length=2, max_length=255)
    quantidade: int = Field(default=1, ge=1)
    valor_unitario: float = Field(default=0, ge=0)
    tipo_item: Optional[str] = Field(default="SERVICO_EXECUTADO", max_length=50)


class AtendimentoClinicoItemResponse(BaseModel):
    id: int
    atendimento_id: int
    servico_id: Optional[int] = None
    descricao: str
    quantidade: int
    valor_unitario: float
    valor_total: float
    tipo_item: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AtendimentoClinicoDetalheResponse(BaseModel):
    atendimento: AtendimentoClinicoResponse
    anamnese: Optional[PetAnamneseResponse] = None
    prontuario: Optional[PetProntuarioResponse] = None
    itens: List[AtendimentoClinicoItemResponse] = []


class AtendimentoClinicoFinalizarResponse(BaseModel):
    atendimento: AtendimentoClinicoResponse
    itens: List[AtendimentoClinicoItemResponse]
    total_faturavel: float
    payload_pdv: dict


class AtendimentoClinicoAnamneseSalvar(PetAnamneseUpdate):
    pass


class AtendimentoClinicoProntuarioSalvar(PetProntuarioUpdate):
    pass