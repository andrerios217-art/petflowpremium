from datetime import date, time
from typing import Optional, List

from pydantic import BaseModel


class AgendamentoServicoPayload(BaseModel):
    servico_id: int
    preco: float
    tempo_previsto: int


class AgendamentoServicoOut(BaseModel):
    id: int
    servico_id: int
    nome: str
    preco: float
    tempo_previsto: int

    class Config:
        from_attributes = True


class AgendamentoCreate(BaseModel):
    empresa_id: int
    cliente_id: int
    pet_id: int
    funcionario_id: Optional[int] = None
    data: date
    hora: time
    prioridade: str = "NORMAL"
    observacoes: Optional[str] = None
    servicos: List[AgendamentoServicoPayload]


class AgendamentoUpdate(BaseModel):
    funcionario_id: Optional[int] = None
    data: date
    hora: time
    prioridade: str = "NORMAL"
    observacoes: Optional[str] = None
    servicos: List[AgendamentoServicoPayload]


class AgendamentoOut(BaseModel):
    id: int
    empresa_id: int
    cliente_id: int
    pet_id: int
    funcionario_id: Optional[int] = None
    data: date
    hora: time
    status: str
    prioridade: str
    observacoes: Optional[str] = None
    tem_intercorrencia: bool = False
    intercorrencias: Optional[str] = None

    cliente_nome: str
    pet_nome: str
    funcionario_nome: Optional[str] = None
    servicos: List[AgendamentoServicoOut]

    class Config:
        from_attributes = True