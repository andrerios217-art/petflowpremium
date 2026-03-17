from datetime import date, datetime, time
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


# ==========================================================
# SCHEMAS BASE DO PET
# ==========================================================

class PetBase(BaseModel):
    empresa_id: int
    cliente_id: int
    nome: str
    nascimento: Optional[date] = None
    raca: Optional[str] = None
    sexo: Optional[str] = None
    temperamento: Optional[str] = None
    peso: Optional[Decimal] = None
    porte: Optional[str] = None
    observacoes: Optional[str] = None
    pode_perfume: bool = True
    pode_acessorio: bool = True
    castrado: bool = False
    foto: Optional[str] = None
    ativo: bool = True


class PetCreate(PetBase):
    pass


class PetUpdate(BaseModel):
    empresa_id: Optional[int] = None
    cliente_id: Optional[int] = None
    nome: Optional[str] = None
    nascimento: Optional[date] = None
    raca: Optional[str] = None
    sexo: Optional[str] = None
    temperamento: Optional[str] = None
    peso: Optional[Decimal] = None
    porte: Optional[str] = None
    observacoes: Optional[str] = None
    pode_perfume: Optional[bool] = None
    pode_acessorio: Optional[bool] = None
    castrado: Optional[bool] = None
    foto: Optional[str] = None
    ativo: Optional[bool] = None


class PetOut(PetBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# ==========================================================
# HISTÓRICO DO PET - RESUMO
# ==========================================================

class PetResumoHistoricoSchema(BaseModel):
    id: int
    nome: str
    tutor: Optional[str] = None
    especie: Optional[str] = None
    raca: Optional[str] = None
    porte: Optional[str] = None
    peso: Optional[Decimal] = None
    sexo: Optional[str] = None
    temperamento: Optional[str] = None
    observacoes_cadastrais: Optional[str] = None
    nascimento: Optional[date] = None
    pode_perfume: bool = True
    pode_acessorio: bool = True
    castrado: bool = False
    foto: Optional[str] = None
    ativo: bool = True

    class Config:
        orm_mode = True


# ==========================================================
# HISTÓRICO DO PET - TIMELINE DE PRODUÇÃO
# ==========================================================

class PetHistoricoTimelineItemSchema(BaseModel):
    etapa: str
    status: str
    iniciado_em: datetime
    finalizado_em: Optional[datetime] = None
    funcionario: Optional[str] = None
    intercorrencia: Optional[str] = None
    observacoes: Optional[str] = None
    tempo_gasto_minutos: Optional[int] = None

    class Config:
        orm_mode = True


# ==========================================================
# HISTÓRICO DO PET - ATENDIMENTO GROOMING
# ==========================================================

class PetHistoricoAtendimentoSchema(BaseModel):
    agendamento_id: int
    data: date
    hora: time
    servicos_executados: List[str] = []
    funcionario_responsavel: Optional[str] = None
    status_final: str
    teve_intercorrencia: bool = False
    intercorrencias: List[str] = []
    observacoes_gerais: Optional[str] = None
    observacoes_producao: Optional[str] = None
    tempo_total_atendimento_minutos: Optional[int] = None
    timeline: List[PetHistoricoTimelineItemSchema] = []

    class Config:
        orm_mode = True


# ==========================================================
# HISTÓRICO DO PET - CONSULTA VETERINÁRIA
# ==========================================================

class PetHistoricoConsultaAnamneseSchema(BaseModel):
    queixa_principal: Optional[str] = None
    historico_atual: Optional[str] = None
    alimentacao: Optional[str] = None
    alergias: Optional[str] = None
    uso_medicacao_atual: Optional[str] = None
    observacoes: Optional[str] = None

    class Config:
        orm_mode = True


class PetHistoricoConsultaProntuarioSchema(BaseModel):
    exame_fisico: Optional[str] = None
    diagnostico: Optional[str] = None
    conduta: Optional[str] = None
    observacoes: Optional[str] = None

    class Config:
        orm_mode = True


class PetHistoricoConsultaVeterinariaSchema(BaseModel):
    atendimento_id: int
    agendamento_id: Optional[int] = None
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    status: str
    veterinario: Optional[str] = None
    servicos_previstos: List[str] = []
    servicos_executados: List[str] = []
    observacoes_recepcao: Optional[str] = None
    observacoes_clinicas: Optional[str] = None
    anamnese: PetHistoricoConsultaAnamneseSchema
    prontuario: PetHistoricoConsultaProntuarioSchema

    class Config:
        orm_mode = True


# ==========================================================
# HISTÓRICO DO PET - RESPOSTA FINAL
# ==========================================================

class PetHistoricoResponseSchema(BaseModel):
    pet: PetResumoHistoricoSchema
    consultas_veterinarias: List[PetHistoricoConsultaVeterinariaSchema] = []
    atendimentos: List[PetHistoricoAtendimentoSchema] = []

    class Config:
        orm_mode = True