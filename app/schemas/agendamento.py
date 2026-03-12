from pydantic import BaseModel
from datetime import date, time
from typing import List, Optional


class AgendamentoServicoCreate(BaseModel):
    servico_id: int
    preco: float
    tempo_previsto: int


class AgendamentoCreate(BaseModel):
    empresa_id: int
    cliente_id: int
    pet_id: int
    funcionario_id: Optional[int] = None

    data: date
    hora: time

    prioridade: Optional[str] = "NORMAL"
    observacoes: Optional[str] = None

    servicos: List[AgendamentoServicoCreate]


class AgendamentoUpdate(BaseModel):
    funcionario_id: Optional[int] = None

    data: date
    hora: time

    prioridade: Optional[str] = "NORMAL"
    observacoes: Optional[str] = None

    servicos: List[AgendamentoServicoCreate]


class AgendamentoServicoOut(BaseModel):
    id: int
    servico_id: int
    nome: str
    preco: float
    tempo_previsto: int


class AgendamentoOut(BaseModel):
    id: int

    empresa_id: int
    cliente_id: int
    pet_id: int
    funcionario_id: Optional[int]

    data: date
    hora: time

    status: str
    prioridade: Optional[str]

    observacoes: Optional[str]

    cliente_nome: Optional[str]
    pet_nome: Optional[str]
    funcionario_nome: Optional[str]

    tem_intercorrencia: Optional[bool] = False

    servicos: List[AgendamentoServicoOut]