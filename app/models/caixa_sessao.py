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


class CaixaSessao(Base):
    __tablename__ = "caixa_sessoes"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)

    # Responsável principal pelo caixa no turno/sessão
    usuario_responsavel_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True,
    )

    # Quem efetivamente abriu/fechou
    usuario_abertura_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True,
    )
    usuario_fechamento_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=True,
        index=True,
    )

    # Gerente que autorizou exceções na abertura/fechamento, se houver
    gerente_abertura_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=True,
        index=True,
    )
    gerente_fechamento_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=True,
        index=True,
    )

    # Status:
    # - ABERTO
    # - FECHADO
    # - CANCELADO
    status = Column(String(20), nullable=False, default="ABERTO", index=True)

    # Abertura
    valor_abertura_informado = Column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    valor_referencia_anterior = Column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    diferenca_abertura = Column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    motivo_diferenca_abertura = Column(Text, nullable=True)

    # Fechamento
    valor_fechamento_esperado = Column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    valor_fechamento_informado = Column(
        Numeric(10, 2),
        nullable=True,
    )
    diferenca_fechamento = Column(
        Numeric(10, 2),
        nullable=True,
    )
    motivo_diferenca_fechamento = Column(Text, nullable=True)

    observacoes = Column(Text, nullable=True)

    aberto_em = Column(DateTime(timezone=True), nullable=False, default=_agora_utc)
    fechado_em = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_agora_utc)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_agora_utc,
        onupdate=_agora_utc,
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('ABERTO', 'FECHADO', 'CANCELADO')",
            name="ck_caixa_sessoes_status",
        ),
        CheckConstraint(
            "valor_abertura_informado >= 0",
            name="ck_caixa_sessoes_valor_abertura_non_negative",
        ),
        CheckConstraint(
            "valor_referencia_anterior >= 0",
            name="ck_caixa_sessoes_valor_referencia_non_negative",
        ),
        CheckConstraint(
            "valor_fechamento_esperado >= 0",
            name="ck_caixa_sessoes_valor_fechamento_esperado_non_negative",
        ),
        CheckConstraint(
            "valor_fechamento_informado IS NULL OR valor_fechamento_informado >= 0",
            name="ck_caixa_sessoes_valor_fechamento_informado_non_negative",
        ),
    )

    empresa = relationship("Empresa")

    usuario_responsavel = relationship(
        "Usuario",
        foreign_keys=[usuario_responsavel_id],
    )
    usuario_abertura = relationship(
        "Usuario",
        foreign_keys=[usuario_abertura_id],
    )
    usuario_fechamento = relationship(
        "Usuario",
        foreign_keys=[usuario_fechamento_id],
    )
    gerente_abertura = relationship(
        "Usuario",
        foreign_keys=[gerente_abertura_id],
    )
    gerente_fechamento = relationship(
        "Usuario",
        foreign_keys=[gerente_fechamento_id],
    )

    movimentos = relationship(
        "CaixaMovimento",
        back_populates="caixa_sessao",
        cascade="all, delete-orphan",
    )
    divergencias = relationship(
        "CaixaDivergencia",
        back_populates="caixa_sessao",
        cascade="all, delete-orphan",
    )
    vendas = relationship(
        "PdvVenda",
        back_populates="caixa_sessao",
    )

    @property
    def esta_aberto(self) -> bool:
        return self.status == "ABERTO"

    @property
    def esta_fechado(self) -> bool:
        return self.status == "FECHADO"

    @property
    def possui_diferenca_abertura(self) -> bool:
        return Decimal(str(self.diferenca_abertura or Decimal("0.00"))) != Decimal("0.00")

    @property
    def possui_diferenca_fechamento(self) -> bool:
        if self.diferenca_fechamento is None:
            return False
        return Decimal(str(self.diferenca_fechamento)) != Decimal("0.00")

    def abrir(
        self,
        usuario_responsavel_id: int,
        usuario_abertura_id: int,
        valor_abertura_informado,
        valor_referencia_anterior=Decimal("0.00"),
        motivo_diferenca_abertura: str | None = None,
        gerente_abertura_id: int | None = None,
        observacoes: str | None = None,
    ):
        valor_abertura = Decimal(str(valor_abertura_informado or Decimal("0.00")))
        valor_referencia = Decimal(str(valor_referencia_anterior or Decimal("0.00")))

        self.status = "ABERTO"
        self.usuario_responsavel_id = usuario_responsavel_id
        self.usuario_abertura_id = usuario_abertura_id
        self.gerente_abertura_id = gerente_abertura_id
        self.valor_abertura_informado = valor_abertura
        self.valor_referencia_anterior = valor_referencia
        self.diferenca_abertura = valor_abertura - valor_referencia
        self.motivo_diferenca_abertura = motivo_diferenca_abertura
        self.observacoes = observacoes
        self.aberto_em = _agora_utc()
        self.updated_at = _agora_utc()

    def registrar_fechamento(
        self,
        usuario_fechamento_id: int,
        valor_fechamento_esperado,
        valor_fechamento_informado,
        motivo_diferenca_fechamento: str | None = None,
        gerente_fechamento_id: int | None = None,
    ):
        esperado = Decimal(str(valor_fechamento_esperado or Decimal("0.00")))
        informado = Decimal(str(valor_fechamento_informado or Decimal("0.00")))

        self.status = "FECHADO"
        self.usuario_fechamento_id = usuario_fechamento_id
        self.gerente_fechamento_id = gerente_fechamento_id
        self.valor_fechamento_esperado = esperado
        self.valor_fechamento_informado = informado
        self.diferenca_fechamento = informado - esperado
        self.motivo_diferenca_fechamento = motivo_diferenca_fechamento
        self.fechado_em = _agora_utc()
        self.updated_at = _agora_utc()

    def cancelar(self, observacoes: str | None = None):
        self.status = "CANCELADO"
        if observacoes:
            self.observacoes = observacoes
        self.updated_at = _agora_utc()