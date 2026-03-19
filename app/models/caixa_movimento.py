from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def _agora_utc():
    return datetime.now(timezone.utc)


class CaixaMovimento(Base):
    __tablename__ = "caixa_movimentos"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    caixa_sessao_id = Column(
        Integer,
        ForeignKey("caixa_sessoes.id"),
        nullable=False,
        index=True,
    )

    # Tipos:
    # - VENDA
    # - SANGRIA
    # - SUPRIMENTO
    # - ESTORNO
    # - AJUSTE
    tipo_movimento = Column(String(20), nullable=False, index=True)

    # Formas:
    # - DINHEIRO
    # - PIX
    # - CARTAO_DEBITO
    # - CARTAO_CREDITO
    # Pode ser nulo em alguns ajustes operacionais
    forma_pagamento = Column(String(30), nullable=True, index=True)

    valor = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))

    # Origem lógica do movimento
    # exemplos:
    # - PDV_VENDA
    # - CAIXA_SANGRIA
    # - CAIXA_SUPRIMENTO
    # - CAIXA_AJUSTE
    origem_tipo = Column(String(50), nullable=True, index=True)
    origem_id = Column(Integer, nullable=True, index=True)

    # Motivo padronizado e detalhe livre
    motivo = Column(String(100), nullable=True)
    observacoes = Column(Text, nullable=True)

    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    gerente_autorizador_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=True,
        index=True,
    )

    created_at = Column(DateTime(timezone=True), nullable=False, default=_agora_utc)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_agora_utc,
        onupdate=_agora_utc,
    )

    __table_args__ = (
        CheckConstraint(
            "tipo_movimento IN ('VENDA', 'SANGRIA', 'SUPRIMENTO', 'ESTORNO', 'AJUSTE')",
            name="ck_caixa_movimentos_tipo_movimento",
        ),
        CheckConstraint(
            "forma_pagamento IS NULL OR forma_pagamento IN "
            "('DINHEIRO', 'PIX', 'CARTAO_DEBITO', 'CARTAO_CREDITO')",
            name="ck_caixa_movimentos_forma_pagamento",
        ),
        CheckConstraint(
            "valor > 0",
            name="ck_caixa_movimentos_valor_positive",
        ),
    )

    empresa = relationship("Empresa")
    caixa_sessao = relationship("CaixaSessao", back_populates="movimentos")
    usuario = relationship("Usuario", foreign_keys=[usuario_id])
    gerente_autorizador = relationship(
        "Usuario",
        foreign_keys=[gerente_autorizador_id],
    )

    @property
    def eh_venda(self) -> bool:
        return self.tipo_movimento == "VENDA"

    @property
    def eh_sangria(self) -> bool:
        return self.tipo_movimento == "SANGRIA"

    @property
    def eh_suprimento(self) -> bool:
        return self.tipo_movimento == "SUPRIMENTO"

    @property
    def eh_estorno(self) -> bool:
        return self.tipo_movimento == "ESTORNO"

    @property
    def eh_ajuste(self) -> bool:
        return self.tipo_movimento == "AJUSTE"

    @property
    def impacta_dinheiro_fisico(self) -> bool:
        return self.forma_pagamento == "DINHEIRO" or self.tipo_movimento in (
            "SANGRIA",
            "SUPRIMENTO",
            "AJUSTE",
        )

    def definir_como_venda(
        self,
        empresa_id: int,
        caixa_sessao_id: int,
        valor,
        forma_pagamento: str,
        usuario_id: int,
        origem_id: int | None = None,
        observacoes: str | None = None,
    ):
        self.empresa_id = empresa_id
        self.caixa_sessao_id = caixa_sessao_id
        self.tipo_movimento = "VENDA"
        self.forma_pagamento = forma_pagamento
        self.valor = Decimal(str(valor))
        self.origem_tipo = "PDV_VENDA"
        self.origem_id = origem_id
        self.motivo = "VENDA_REALIZADA"
        self.observacoes = observacoes
        self.usuario_id = usuario_id
        self.updated_at = _agora_utc()

    def definir_como_sangria(
        self,
        empresa_id: int,
        caixa_sessao_id: int,
        valor,
        usuario_id: int,
        motivo: str,
        observacoes: str | None = None,
        gerente_autorizador_id: int | None = None,
    ):
        self.empresa_id = empresa_id
        self.caixa_sessao_id = caixa_sessao_id
        self.tipo_movimento = "SANGRIA"
        self.forma_pagamento = "DINHEIRO"
        self.valor = Decimal(str(valor))
        self.origem_tipo = "CAIXA_SANGRIA"
        self.origem_id = None
        self.motivo = motivo
        self.observacoes = observacoes
        self.usuario_id = usuario_id
        self.gerente_autorizador_id = gerente_autorizador_id
        self.updated_at = _agora_utc()

    def definir_como_suprimento(
        self,
        empresa_id: int,
        caixa_sessao_id: int,
        valor,
        usuario_id: int,
        motivo: str,
        observacoes: str | None = None,
        gerente_autorizador_id: int | None = None,
    ):
        self.empresa_id = empresa_id
        self.caixa_sessao_id = caixa_sessao_id
        self.tipo_movimento = "SUPRIMENTO"
        self.forma_pagamento = "DINHEIRO"
        self.valor = Decimal(str(valor))
        self.origem_tipo = "CAIXA_SUPRIMENTO"
        self.origem_id = None
        self.motivo = motivo
        self.observacoes = observacoes
        self.usuario_id = usuario_id
        self.gerente_autorizador_id = gerente_autorizador_id
        self.updated_at = _agora_utc()

    def definir_como_estorno(
        self,
        empresa_id: int,
        caixa_sessao_id: int,
        valor,
        forma_pagamento: str,
        usuario_id: int,
        origem_tipo: str | None = None,
        origem_id: int | None = None,
        motivo: str | None = None,
        observacoes: str | None = None,
        gerente_autorizador_id: int | None = None,
    ):
        self.empresa_id = empresa_id
        self.caixa_sessao_id = caixa_sessao_id
        self.tipo_movimento = "ESTORNO"
        self.forma_pagamento = forma_pagamento
        self.valor = Decimal(str(valor))
        self.origem_tipo = origem_tipo or "CAIXA_ESTORNO"
        self.origem_id = origem_id
        self.motivo = motivo or "ESTORNO"
        self.observacoes = observacoes
        self.usuario_id = usuario_id
        self.gerente_autorizador_id = gerente_autorizador_id
        self.updated_at = _agora_utc()

    def definir_como_ajuste(
        self,
        empresa_id: int,
        caixa_sessao_id: int,
        valor,
        usuario_id: int,
        motivo: str,
        observacoes: str | None = None,
        gerente_autorizador_id: int | None = None,
    ):
        self.empresa_id = empresa_id
        self.caixa_sessao_id = caixa_sessao_id
        self.tipo_movimento = "AJUSTE"
        self.forma_pagamento = "DINHEIRO"
        self.valor = Decimal(str(valor))
        self.origem_tipo = "CAIXA_AJUSTE"
        self.origem_id = None
        self.motivo = motivo
        self.observacoes = observacoes
        self.usuario_id = usuario_id
        self.gerente_autorizador_id = gerente_autorizador_id
        self.updated_at = _agora_utc()