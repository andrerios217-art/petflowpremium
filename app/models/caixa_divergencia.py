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


class CaixaDivergencia(Base):
    __tablename__ = "caixa_divergencias"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)

    caixa_sessao_id = Column(
        Integer,
        ForeignKey("caixa_sessoes.id"),
        nullable=False,
        index=True,
    )

    # Tipos:
    # - ABERTURA
    # - FECHAMENTO
    # - SANGRIA
    # - SUPRIMENTO
    # - AJUSTE
    tipo = Column(String(20), nullable=False, index=True)

    valor_referencia = Column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    valor_informado = Column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    valor_diferenca = Column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Direção:
    # - FALTA -> valor informado menor que a referência
    # - SOBRA -> valor informado maior que a referência
    # - NEUTRA -> diferença zero (em geral não devemos gravar, mas fica previsto)
    direcao = Column(String(10), nullable=False, index=True)

    # Status:
    # - PENDENTE_ANALISE
    # - JUSTIFICADA
    # - CONFIRMADA
    # - RESOLVIDA
    status = Column(String(30), nullable=False, default="PENDENTE_ANALISE", index=True)

    # Risco:
    # - BAIXO
    # - MEDIO
    # - ALTO
    nivel_risco = Column(String(10), nullable=False, default="BAIXO", index=True)

    # Motivo padronizado e detalhe livre
    motivo_padrao = Column(String(100), nullable=True, index=True)
    motivo_detalhe = Column(Text, nullable=True)

    usuario_responsavel_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True,
    )
    gerente_autorizador_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=True,
        index=True,
    )

    observacao_gerencial = Column(Text, nullable=True)

    ocorreu_em = Column(DateTime(timezone=True), nullable=False, default=_agora_utc)
    resolvido_em = Column(DateTime(timezone=True), nullable=True)
    resolvido_por_usuario_id = Column(
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
            "tipo IN ('ABERTURA', 'FECHAMENTO', 'SANGRIA', 'SUPRIMENTO', 'AJUSTE')",
            name="ck_caixa_divergencias_tipo",
        ),
        CheckConstraint(
            "direcao IN ('FALTA', 'SOBRA', 'NEUTRA')",
            name="ck_caixa_divergencias_direcao",
        ),
        CheckConstraint(
            "status IN ('PENDENTE_ANALISE', 'JUSTIFICADA', 'CONFIRMADA', 'RESOLVIDA')",
            name="ck_caixa_divergencias_status",
        ),
        CheckConstraint(
            "nivel_risco IN ('BAIXO', 'MEDIO', 'ALTO')",
            name="ck_caixa_divergencias_nivel_risco",
        ),
        CheckConstraint(
            "valor_referencia >= 0",
            name="ck_caixa_divergencias_valor_referencia_non_negative",
        ),
        CheckConstraint(
            "valor_informado >= 0",
            name="ck_caixa_divergencias_valor_informado_non_negative",
        ),
    )

    empresa = relationship("Empresa")
    caixa_sessao = relationship("CaixaSessao", back_populates="divergencias")

    usuario_responsavel = relationship(
        "Usuario",
        foreign_keys=[usuario_responsavel_id],
    )
    gerente_autorizador = relationship(
        "Usuario",
        foreign_keys=[gerente_autorizador_id],
    )
    resolvido_por_usuario = relationship(
        "Usuario",
        foreign_keys=[resolvido_por_usuario_id],
    )

    @property
    def eh_falta(self) -> bool:
        return self.direcao == "FALTA"

    @property
    def eh_sobra(self) -> bool:
        return self.direcao == "SOBRA"

    @property
    def esta_pendente(self) -> bool:
        return self.status == "PENDENTE_ANALISE"

    @staticmethod
    def calcular_diferenca(valor_referencia, valor_informado) -> Decimal:
        referencia = Decimal(str(valor_referencia or Decimal("0.00")))
        informado = Decimal(str(valor_informado or Decimal("0.00")))
        return informado - referencia

    @staticmethod
    def calcular_direcao(valor_referencia, valor_informado) -> str:
        diferenca = CaixaDivergencia.calcular_diferenca(
            valor_referencia=valor_referencia,
            valor_informado=valor_informado,
        )
        if diferenca > Decimal("0.00"):
            return "SOBRA"
        if diferenca < Decimal("0.00"):
            return "FALTA"
        return "NEUTRA"

    def definir(
        self,
        empresa_id: int,
        caixa_sessao_id: int,
        tipo: str,
        valor_referencia,
        valor_informado,
        usuario_responsavel_id: int,
        motivo_padrao: str | None = None,
        motivo_detalhe: str | None = None,
        gerente_autorizador_id: int | None = None,
        nivel_risco: str = "BAIXO",
    ):
        referencia = Decimal(str(valor_referencia or Decimal("0.00")))
        informado = Decimal(str(valor_informado or Decimal("0.00")))
        diferenca = informado - referencia

        self.empresa_id = empresa_id
        self.caixa_sessao_id = caixa_sessao_id
        self.tipo = tipo
        self.valor_referencia = referencia
        self.valor_informado = informado
        self.valor_diferenca = diferenca.copy_abs()
        self.direcao = self.calcular_direcao(referencia, informado)
        self.usuario_responsavel_id = usuario_responsavel_id
        self.motivo_padrao = motivo_padrao
        self.motivo_detalhe = motivo_detalhe
        self.gerente_autorizador_id = gerente_autorizador_id
        self.nivel_risco = nivel_risco
        self.ocorreu_em = _agora_utc()
        self.updated_at = _agora_utc()

    def marcar_justificada(
        self,
        observacao_gerencial: str | None = None,
        gerente_autorizador_id: int | None = None,
    ):
        self.status = "JUSTIFICADA"
        if observacao_gerencial:
            self.observacao_gerencial = observacao_gerencial
        if gerente_autorizador_id:
            self.gerente_autorizador_id = gerente_autorizador_id
        self.updated_at = _agora_utc()

    def marcar_confirmada(
        self,
        observacao_gerencial: str | None = None,
        gerente_autorizador_id: int | None = None,
    ):
        self.status = "CONFIRMADA"
        if observacao_gerencial:
            self.observacao_gerencial = observacao_gerencial
        if gerente_autorizador_id:
            self.gerente_autorizador_id = gerente_autorizador_id
        self.updated_at = _agora_utc()

    def marcar_resolvida(
        self,
        resolvido_por_usuario_id: int,
        observacao_gerencial: str | None = None,
    ):
        self.status = "RESOLVIDA"
        self.resolvido_por_usuario_id = resolvido_por_usuario_id
        self.resolvido_em = _agora_utc()
        if observacao_gerencial:
            self.observacao_gerencial = observacao_gerencial
        self.updated_at = _agora_utc()