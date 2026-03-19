from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


ModoClienteLiteral = Literal["REGISTERED_CLIENT", "WALK_IN"]
OrigemVendaLiteral = Literal["PRODUCT_ONLY", "SERVICE_ONLY", "MIXED"]
StatusVendaLiteral = Literal["ABERTA", "FECHADA", "CANCELADA"]
TipoItemLiteral = Literal["SERVICE", "PRODUCT"]
FormaPagamentoLiteral = Literal["DINHEIRO", "PIX", "CARTAO_DEBITO", "CARTAO_CREDITO"]
StatusPagamentoLiteral = Literal["RECEBIDO", "CANCELADO"]


class PdvClienteResumo(BaseModel):
    id: int
    nome: str
    cpf: str | None = None
    telefone: str | None = None

    class Config:
        from_attributes = True


class PdvVendaCreate(BaseModel):
    empresa_id: int
    caixa_sessao_id: int
    modo_cliente: ModoClienteLiteral
    cliente_id: int | None = None
    nome_cliente_snapshot: str | None = None
    telefone_cliente_snapshot: str | None = None
    observacoes: str | None = None

    @model_validator(mode="after")
    def validar_cliente_por_modo(self):
        if self.modo_cliente == "REGISTERED_CLIENT" and not self.cliente_id:
            raise ValueError("cliente_id é obrigatório para venda com cliente cadastrado.")

        if self.modo_cliente == "WALK_IN" and self.cliente_id is not None:
            raise ValueError("Venda balcão não pode ter cliente_id informado.")

        return self


class PdvVendaUpdate(BaseModel):
    observacoes: str | None = None
    desconto_valor: Decimal | None = Field(default=None, ge=0)
    acrescimo_valor: Decimal | None = Field(default=None, ge=0)


class PdvVendaItemAdd(BaseModel):
    tipo_item: TipoItemLiteral
    atendimento_clinico_id: int | None = None
    produto_id: int | None = None
    descricao_snapshot: str | None = None
    observacao: str | None = None
    quantidade: Decimal = Field(default=Decimal("1.000"), gt=0)
    valor_unitario: Decimal | None = Field(default=None, ge=0)
    desconto_valor: Decimal = Field(default=Decimal("0.00"), ge=0)

    @model_validator(mode="after")
    def validar_campos_por_tipo(self):
        if self.tipo_item == "SERVICE":
            if not self.atendimento_clinico_id:
                raise ValueError("atendimento_clinico_id é obrigatório para item SERVICE.")

            if self.produto_id is not None:
                raise ValueError("Item SERVICE não pode ter produto_id.")

        if self.tipo_item == "PRODUCT":
            if not self.produto_id:
                raise ValueError("produto_id é obrigatório para item PRODUCT.")

            if self.atendimento_clinico_id is not None:
                raise ValueError("Item PRODUCT não pode ter atendimento_clinico_id.")

            if self.valor_unitario is None:
                raise ValueError("valor_unitario é obrigatório para item PRODUCT.")

            if not self.descricao_snapshot:
                raise ValueError("descricao_snapshot é obrigatória para item PRODUCT.")

        return self


class PdvPagamentoCreate(BaseModel):
    forma_pagamento: FormaPagamentoLiteral
    valor: Decimal = Field(gt=0)
    referencia: str | None = None
    observacoes: str | None = None
    usuario_id: int | None = None
    recebido_em: datetime | None = None


class PdvCheckoutRequest(BaseModel):
    pagamento: PdvPagamentoCreate
    observacoes: str | None = None


class PdvCancelRequest(BaseModel):
    motivo_cancelamento: str | None = None
    usuario_cancelamento_id: int | None = None
    gerente_autorizador_id: int | None = None
    senha_gerente: str | None = None


class PdvVendaItemOut(BaseModel):
    id: int
    venda_id: int
    tipo_item: TipoItemLiteral
    atendimento_clinico_id: int | None = None
    produto_id: int | None = None
    descricao_snapshot: str
    observacao: str | None = None
    quantidade: Decimal
    valor_unitario: Decimal
    desconto_valor: Decimal
    valor_total: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PdvPagamentoOut(BaseModel):
    id: int
    venda_id: int
    forma_pagamento: FormaPagamentoLiteral
    valor: Decimal
    status: StatusPagamentoLiteral
    referencia: str | None = None
    observacoes: str | None = None
    usuario_id: int | None = None
    recebido_em: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PdvVendaOut(BaseModel):
    id: int
    empresa_id: int
    caixa_sessao_id: int
    numero_venda: str | None = None
    modo_cliente: ModoClienteLiteral
    cliente_id: int | None = None
    nome_cliente_snapshot: str | None = None
    telefone_cliente_snapshot: str | None = None
    origem: OrigemVendaLiteral
    status: StatusVendaLiteral
    subtotal: Decimal
    desconto_valor: Decimal
    acrescimo_valor: Decimal
    valor_total: Decimal
    observacoes: str | None = None
    usuario_abertura_id: int | None = None
    usuario_fechamento_id: int | None = None
    usuario_cancelamento_id: int | None = None
    aberta_em: datetime
    fechada_em: datetime | None = None
    cancelada_em: datetime | None = None
    motivo_cancelamento: str | None = None
    created_at: datetime
    updated_at: datetime

    cliente: PdvClienteResumo | None = None
    itens: list[PdvVendaItemOut] = []
    pagamentos: list[PdvPagamentoOut] = []

    class Config:
        from_attributes = True


class PdvVendaListOut(BaseModel):
    id: int
    caixa_sessao_id: int
    numero_venda: str | None = None
    modo_cliente: ModoClienteLiteral
    cliente_id: int | None = None
    nome_cliente_snapshot: str | None = None
    origem: OrigemVendaLiteral
    status: StatusVendaLiteral
    valor_total: Decimal
    aberta_em: datetime
    fechada_em: datetime | None = None
    cliente: PdvClienteResumo | None = None

    class Config:
        from_attributes = True


class PdvAtendimentoProntoOut(BaseModel):
    atendimento_id: int
    cliente_id: int
    cliente_nome: str
    pet_nome: str | None = None
    descricao: str
    valor_total: Decimal
    status: str
    enviado_pdv: bool

    class Config:
        from_attributes = True


class PdvClienteBuscaOut(BaseModel):
    id: int
    nome: str
    cpf: str | None = None
    telefone: str | None = None

    class Config:
        from_attributes = True


class PdvOperacaoResponse(BaseModel):
    ok: bool = True
    mensagem: str
    venda: PdvVendaOut | None = None