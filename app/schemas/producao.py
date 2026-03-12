from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class ProducaoMoverEtapa(BaseModel):
    coluna_destino: str
    funcionario_id: Optional[int] = None
    secagem_tempo: Optional[int] = None
    intercorrencias: Optional[List[str]] = None
    descricao_intercorrencia: Optional[str] = None


class ProducaoIniciarEtapa(BaseModel):
    funcionario_id: int


class ProducaoCardResponse(BaseModel):
    id: int
    agendamento_id: int
    coluna: str
    etapa_status: str
    prioridade: str
    funcionario_id: Optional[int] = None
    secagem_tempo: Optional[int] = None
    secagem_inicio: Optional[datetime] = None
    finalizado: bool

    pet_nome: Optional[str] = None
    pet_foto: Optional[str] = None
    tutor_nome: Optional[str] = None
    servicos: List[str] = []
    funcionario_nome: Optional[str] = None
    status_agendamento: Optional[str] = None

    class Config:
        from_attributes = True