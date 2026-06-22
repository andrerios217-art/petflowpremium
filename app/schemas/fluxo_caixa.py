from datetime import date

from pydantic import BaseModel


class FluxoCaixaResumoOut(BaseModel):
    saldo_inicial: float
    total_entradas: float
    total_saidas: float
    saldo_final: float


class FluxoCaixaMovimentoOut(BaseModel):
    data: date
    tipo: str
    descricao: str
    forma_pagamento: str | None = None
    entrada: float
    saida: float
    saldo: float


class FluxoCaixaExtratoOut(BaseModel):
    empresa_id: int
    data_inicial: date
    data_final: date
    saldo_inicial: float
    saldo_final: float
    movimentos: list[FluxoCaixaMovimentoOut]


class FluxoCaixaPrevisaoItemOut(BaseModel):
    data: date
    receber: float
    pagar: float
    saldo_previsto: float


class FluxoCaixaPrevisaoOut(BaseModel):
    empresa_id: int
    dias: int
    saldo_atual: float
    previsoes: list[FluxoCaixaPrevisaoItemOut]
