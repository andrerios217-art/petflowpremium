from datetime import date, time
from pydantic import BaseModel, ConfigDict


class AgendamentoServicoCreate(BaseModel):
    servico_id: int
    preco: float
    tempo_previsto: int


class AgendamentoCreate(BaseModel):
    empresa_id: int
    cliente_id: int
    pet_id: int
    funcionario_id: int | None = None

    data: date
    hora: time

    prioridade: str = "NORMAL"
    observacoes: str | None = None

    servicos: list[AgendamentoServicoCreate]


class AgendamentoUpdate(BaseModel):
    funcionario_id: int | None = None
    data: date
    hora: time
    prioridade: str = "NORMAL"
    observacoes: str | None = None
    servicos: list[AgendamentoServicoCreate]


class AgendamentoServicoOut(BaseModel):
    id: int | None = None
    servico_id: int
    nome: str
    preco: float
    tempo_previsto: int

    model_config = ConfigDict(from_attributes=True)


class AgendamentoOut(BaseModel):
    id: int
    empresa_id: int
    cliente_id: int
    pet_id: int
    funcionario_id: int | None

    data: date
    hora: time

    status: str
    prioridade: str
    observacoes: str | None

    cliente_nome: str
    pet_nome: str
    funcionario_nome: str | None = None

    servicos: list[AgendamentoServicoOut] = []

    model_config = ConfigDict(from_attributes=True)