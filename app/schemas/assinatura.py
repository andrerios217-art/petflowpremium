from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


StatusAssinaturaLiteral = Literal["ATIVA", "PAUSADA", "CANCELADA", "ENCERRADA"]
OrigemAssinaturaLiteral = Literal["INTERNA", "EXTERNA"]
OrigemConsumoLiteral = Literal["MANUAL", "AGENDAMENTO", "PDV", "ATENDIMENTO"]
StatusConsumoLiteral = Literal["PENDENTE", "CONFIRMADO", "ESTORNADO", "CANCELADO"]


class AssinaturaPetItemBase(BaseModel):
    servico_id: int
    nome_servico: str
    quantidade_contratada: int = Field(ge=1)
    preco_unitario_base: Decimal = Field(ge=0)
    percentual_desconto: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)


class AssinaturaPetItemCreate(AssinaturaPetItemBase):
    pass


class AssinaturaPetItemUpdate(BaseModel):
    servico_id: int | None = None
    nome_servico: str | None = None
    quantidade_contratada: int | None = Field(default=None, ge=1)
    quantidade_consumida: int | None = Field(default=None, ge=0)
    preco_unitario_base: Decimal | None = Field(default=None, ge=0)
    percentual_desconto: Decimal | None = Field(default=None, ge=0, le=100)
    ativo: bool | None = None


class AssinaturaPetItemOut(BaseModel):
    id: int
    assinatura_id: int
    empresa_id: int
    servico_id: int
    nome_servico: str
    quantidade_contratada: int
    quantidade_consumida: int
    quantidade_disponivel: int
    preco_unitario_base: Decimal
    percentual_desconto: Decimal
    valor_desconto_unitario: Decimal
    preco_unitario_final: Decimal
    subtotal_bruto: Decimal
    subtotal_desconto: Decimal
    subtotal_final: Decimal
    ativo: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class AssinaturaPetBase(BaseModel):
    empresa_id: int
    cliente_id: int
    pet_id: int
    data_inicio: date
    data_fim: date | None = None
    dia_fechamento_ciclo: int = Field(default=28, ge=1, le=28)
    usar_limite_ate_dia_28: bool = True
    nao_cumulativa: bool = True
    ativa_renovacao: bool = True
    origem: OrigemAssinaturaLiteral = "INTERNA"
    observacoes: str | None = None
    contrato_externo_id: str | None = None


class AssinaturaPetCreate(AssinaturaPetBase):
    itens: list[AssinaturaPetItemCreate]

    @model_validator(mode="after")
    def validar_itens(self):
        if not self.itens:
            raise ValueError("A assinatura deve ter ao menos um serviço.")
        return self


class AssinaturaPetUpdate(BaseModel):
    cliente_id: int | None = None
    pet_id: int | None = None
    status: StatusAssinaturaLiteral | None = None
    data_inicio: date | None = None
    data_fim: date | None = None
    data_cancelamento: date | None = None
    dia_fechamento_ciclo: int | None = Field(default=None, ge=1, le=28)
    usar_limite_ate_dia_28: bool | None = None
    nao_cumulativa: bool | None = None
    ativa_renovacao: bool | None = None
    origem: OrigemAssinaturaLiteral | None = None
    observacoes: str | None = None
    contrato_externo_id: str | None = None


class AssinaturaPetOut(BaseModel):
    id: int
    empresa_id: int
    cliente_id: int
    pet_id: int
    status: StatusAssinaturaLiteral
    origem: OrigemAssinaturaLiteral
    data_inicio: date
    data_fim: date | None = None
    data_cancelamento: date | None = None
    dia_fechamento_ciclo: int
    usar_limite_ate_dia_28: bool
    nao_cumulativa: bool
    ativa_renovacao: bool
    valor_bruto: Decimal
    valor_desconto: Decimal
    valor_final: Decimal
    observacoes: str | None = None
    contrato_externo_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    itens: list[AssinaturaPetItemOut] = []

    class Config:
        from_attributes = True


class AssinaturaPetListOut(BaseModel):
    id: int
    empresa_id: int
    cliente_id: int
    pet_id: int
    status: StatusAssinaturaLiteral
    data_inicio: date
    data_fim: date | None = None
    valor_final: Decimal
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class AssinaturaPetConsumoCreate(BaseModel):
    assinatura_id: int
    assinatura_item_id: int
    empresa_id: int
    cliente_id: int
    pet_id: int
    servico_id: int
    data_consumo: date = Field(default_factory=date.today)
    quantidade: int = Field(default=1, ge=1)
    origem: OrigemConsumoLiteral = "MANUAL"
    status: StatusConsumoLiteral = "CONFIRMADO"
    agendamento_id: int | None = None
    pdv_venda_id: int | None = None
    pdv_venda_item_id: int | None = None
    observacoes: str | None = None


class AssinaturaPetConsumoOut(BaseModel):
    id: int
    assinatura_id: int
    assinatura_item_id: int
    empresa_id: int
    cliente_id: int
    pet_id: int
    servico_id: int
    data_consumo: date
    competencia_ano: int
    competencia_mes: int
    quantidade: int
    origem: OrigemConsumoLiteral
    status: StatusConsumoLiteral
    agendamento_id: int | None = None
    pdv_venda_id: int | None = None
    pdv_venda_item_id: int | None = None
    observacoes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class AssinaturaOperacaoResponse(BaseModel):
    ok: bool = True
    mensagem: str
    assinatura: AssinaturaPetOut | None = None


class AssinaturaConsumoOperacaoResponse(BaseModel):
    ok: bool = True
    mensagem: str
    consumo: AssinaturaPetConsumoOut | None = None