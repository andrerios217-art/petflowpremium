from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def _agora_utc():
    return datetime.now(timezone.utc)


class AssinaturaPet(Base):
    __tablename__ = "assinaturas_pet"

    id = Column(Integer, primary_key=True, index=True)

    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False, index=True)

    status = Column(String(20), nullable=False, default="ATIVA", index=True)
    origem = Column(String(20), nullable=False, default="INTERNA", index=True)

    data_inicio = Column(Date, nullable=False)
    data_fim = Column(Date, nullable=True)
    data_cancelamento = Column(Date, nullable=True)

    dia_fechamento_ciclo = Column(Integer, nullable=False, default=28)
    usar_limite_ate_dia_28 = Column(Boolean, nullable=False, default=True)
    nao_cumulativa = Column(Boolean, nullable=False, default=True)
    ativa_renovacao = Column(Boolean, nullable=False, default=True)

    valor_bruto = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    valor_desconto = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    valor_final = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))

    observacoes = Column(Text, nullable=True)
    contrato_externo_id = Column(String(100), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_agora_utc)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_agora_utc,
        onupdate=_agora_utc,
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('ATIVA', 'PAUSADA', 'CANCELADA', 'ENCERRADA')",
            name="ck_assinaturas_pet_status",
        ),
        CheckConstraint(
            "origem IN ('INTERNA', 'EXTERNA')",
            name="ck_assinaturas_pet_origem",
        ),
        CheckConstraint(
            "dia_fechamento_ciclo >= 1 AND dia_fechamento_ciclo <= 28",
            name="ck_assinaturas_pet_dia_fechamento_1_28",
        ),
        CheckConstraint(
            "valor_bruto >= 0",
            name="ck_assinaturas_pet_valor_bruto_non_negative",
        ),
        CheckConstraint(
            "valor_desconto >= 0",
            name="ck_assinaturas_pet_valor_desconto_non_negative",
        ),
        CheckConstraint(
            "valor_final >= 0",
            name="ck_assinaturas_pet_valor_final_non_negative",
        ),
        UniqueConstraint(
            "empresa_id",
            "pet_id",
            "status",
            name="uq_assinaturas_pet_empresa_pet_status",
        ),
    )

    empresa = relationship("Empresa")
    cliente = relationship("Cliente")
    pet = relationship("Pet")

    itens = relationship(
        "AssinaturaPetItem",
        back_populates="assinatura",
        cascade="all, delete-orphan",
    )

    consumos = relationship(
        "AssinaturaPetConsumo",
        back_populates="assinatura",
        cascade="all, delete-orphan",
    )

    @property
    def esta_ativa(self) -> bool:
        return self.status == "ATIVA"

    @property
    def esta_cancelada(self) -> bool:
        return self.status == "CANCELADA"

    def recalcular_totais(self):
        bruto = Decimal("0.00")
        desconto = Decimal("0.00")

        for item in self.itens or []:
            bruto += Decimal(str(item.subtotal_bruto or Decimal("0.00")))
            desconto += Decimal(str(item.subtotal_desconto or Decimal("0.00")))

        self.valor_bruto = bruto
        self.valor_desconto = desconto

        final = bruto - desconto
        if final < Decimal("0.00"):
            final = Decimal("0.00")

        self.valor_final = final
        self.updated_at = _agora_utc()

    def ativar(self):
        self.status = "ATIVA"
        self.updated_at = _agora_utc()

    def pausar(self):
        self.status = "PAUSADA"
        self.updated_at = _agora_utc()

    def cancelar(self, data_cancelamento: Date | None = None):
        self.status = "CANCELADA"
        self.data_cancelamento = data_cancelamento or _agora_utc().date()
        self.updated_at = _agora_utc()

    def encerrar(self, data_fim: Date | None = None):
        self.status = "ENCERRADA"
        self.data_fim = data_fim or _agora_utc().date()
        self.updated_at = _agora_utc()