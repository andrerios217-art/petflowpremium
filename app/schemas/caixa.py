from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


StatusCaixaLiteral = Literal["ABERTO", "FECHADO", "CANCELADO"]
TipoMovimentoLiteral = Literal["VENDA", "SANGRIA", "SUPRIMENTO", "ESTORNO", "AJUSTE"]
FormaPagamentoLiteral = Literal["DINHEIRO", "PIX", "CARTAO_DEBITO", "CARTAO_CREDITO"]
TipoDivergenciaLiteral = Literal["ABERTURA", "FECHAMENTO", "SANGRIA", "SUPRIMENTO", "AJUSTE"]
DirecaoDivergenciaLiteral = Literal["FALTA", "SOBRA", "NEUTRA"]
StatusDivergenciaLiteral = Literal[
    "PENDENTE_ANALISE",
    "JUSTIFICADA",
    "CONFIRMADA",
    "RESOLVIDA",
]
NivelRiscoLiteral = Literal["BAIXO", "MEDIO", "ALTO"]


class CaixaUsuarioResumo(BaseModel):
    id: int
    nome: str | None = None
    email: str | None = None

    class Config:
        from_attributes = True


class CaixaOperadorBuscaOut(BaseModel):
    id: int
    nome: str
    email: str | None = None
    tipo: str | None = None
    ativo: bool = True

    class Config:
        from_attributes = True


class CaixaSessaoAberturaRequest(BaseModel):
    empresa_id: int
    usuario_responsavel_id: int | None = None
    usuario_responsavel_nome: str | None = None
    usuario_abertura_id: int | None = None
    usuario_abertura_nome: str | None = None
    valor_abertura_informado: Decimal = Field(ge=0)
    observacoes: str | None = None

    # Quando houver diferença acima da tolerância,
    # estes campos serão exigidos pela regra de negócio no CRUD/API
    motivo_diferenca_abertura: str | None = None
    gerente_abertura_id: int | None = None
    gerente_abertura_nome: str | None = None
    senha_gerente: str | None = None


class CaixaSessaoFechamentoRequest(BaseModel):
    usuario_fechamento_id: int | None = None
    usuario_fechamento_nome: str | None = None
    valor_fechamento_informado: Decimal = Field(ge=0)

    # Quando houver diferença acima da tolerância,
    # estes campos serão exigidos pela regra de negócio no CRUD/API
    motivo_diferenca_fechamento: str | None = None
    gerente_fechamento_id: int | None = None
    gerente_fechamento_nome: str | None = None
    senha_gerente: str | None = None


class CaixaMovimentoBaseRequest(BaseModel):
    empresa_id: int
    caixa_sessao_id: int
    valor: Decimal = Field(gt=0)
    usuario_id: int | None = None
    usuario_nome: str | None = None
    motivo: str
    observacoes: str | None = None

    # Quando a política exigir, estes campos serão validados no CRUD/API
    gerente_autorizador_id: int | None = None
    gerente_autorizador_nome: str | None = None
    senha_gerente: str | None = None


class CaixaSangriaRequest(CaixaMovimentoBaseRequest):
    pass


class CaixaSuprimentoRequest(CaixaMovimentoBaseRequest):
    pass


class CaixaDivergenciaResolverRequest(BaseModel):
    resolvido_por_usuario_id: int
    observacao_gerencial: str | None = None


class CaixaDivergenciaAtualizarStatusRequest(BaseModel):
    status: Literal["JUSTIFICADA", "CONFIRMADA", "RESOLVIDA"]
    observacao_gerencial: str | None = None
    gerente_autorizador_id: int | None = None
    senha_gerente: str | None = None
    resolvido_por_usuario_id: int | None = None


class CaixaMovimentoOut(BaseModel):
    id: int
    empresa_id: int
    caixa_sessao_id: int
    tipo_movimento: TipoMovimentoLiteral
    forma_pagamento: FormaPagamentoLiteral | None = None
    valor: Decimal
    origem_tipo: str | None = None
    origem_id: int | None = None
    motivo: str | None = None
    observacoes: str | None = None
    usuario_id: int
    gerente_autorizador_id: int | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CaixaDivergenciaOut(BaseModel):
    id: int
    empresa_id: int
    caixa_sessao_id: int
    tipo: TipoDivergenciaLiteral
    valor_referencia: Decimal
    valor_informado: Decimal
    valor_diferenca: Decimal
    direcao: DirecaoDivergenciaLiteral
    status: StatusDivergenciaLiteral
    nivel_risco: NivelRiscoLiteral
    motivo_padrao: str | None = None
    motivo_detalhe: str | None = None
    usuario_responsavel_id: int
    gerente_autorizador_id: int | None = None
    observacao_gerencial: str | None = None
    ocorreu_em: datetime
    resolvido_em: datetime | None = None
    resolvido_por_usuario_id: int | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CaixaSessaoOut(BaseModel):
    id: int
    empresa_id: int
    usuario_responsavel_id: int
    usuario_abertura_id: int
    usuario_fechamento_id: int | None = None
    gerente_abertura_id: int | None = None
    gerente_fechamento_id: int | None = None
    status: StatusCaixaLiteral
    valor_abertura_informado: Decimal
    valor_referencia_anterior: Decimal
    diferenca_abertura: Decimal
    motivo_diferenca_abertura: str | None = None
    valor_fechamento_esperado: Decimal
    valor_fechamento_informado: Decimal | None = None
    diferenca_fechamento: Decimal | None = None
    motivo_diferenca_fechamento: str | None = None
    observacoes: str | None = None
    aberto_em: datetime
    fechado_em: datetime | None = None
    created_at: datetime
    updated_at: datetime
    usuario_responsavel: CaixaUsuarioResumo | None = None
    usuario_abertura: CaixaUsuarioResumo | None = None
    usuario_fechamento: CaixaUsuarioResumo | None = None
    gerente_abertura: CaixaUsuarioResumo | None = None
    gerente_fechamento: CaixaUsuarioResumo | None = None
    movimentos: list[CaixaMovimentoOut] = []
    divergencias: list[CaixaDivergenciaOut] = []

    class Config:
        from_attributes = True


class CaixaSessaoResumoOut(BaseModel):
    id: int
    empresa_id: int
    usuario_responsavel_id: int
    status: StatusCaixaLiteral
    valor_abertura_informado: Decimal
    valor_referencia_anterior: Decimal
    diferenca_abertura: Decimal
    valor_fechamento_esperado: Decimal
    valor_fechamento_informado: Decimal | None = None
    diferenca_fechamento: Decimal | None = None
    aberto_em: datetime
    fechado_em: datetime | None = None
    usuario_responsavel: CaixaUsuarioResumo | None = None

    class Config:
        from_attributes = True


class CaixaResumoFinanceiroOut(BaseModel):
    caixa_sessao_id: int
    total_vendas: Decimal = Decimal("0.00")
    total_dinheiro: Decimal = Decimal("0.00")
    total_pix: Decimal = Decimal("0.00")
    total_cartao_debito: Decimal = Decimal("0.00")
    total_cartao_credito: Decimal = Decimal("0.00")
    total_sangria: Decimal = Decimal("0.00")
    total_suprimento: Decimal = Decimal("0.00")
    saldo_dinheiro_esperado: Decimal = Decimal("0.00")


class CaixaOperacaoResponse(BaseModel):
    ok: bool = True
    mensagem: str
    caixa_sessao: CaixaSessaoOut | None = None
    divergencia: CaixaDivergenciaOut | None = None