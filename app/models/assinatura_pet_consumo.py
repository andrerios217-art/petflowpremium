from datetime import date, datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def _agora_utc():
    return datetime.now(timezone.utc)


class AssinaturaPetConsumo(Base):
    __tablename__ = "assinaturas_pet_consumos"

    id = Column(Integer, primary_key=True, index=True)

    assinatura_id = Column(
        Integer,
        ForeignKey("assinaturas_pet.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assinatura_item_id = Column(
        Integer,
        ForeignKey("assinaturas_pet_itens.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False, index=True)
    servico_id = Column(Integer, ForeignKey("servicos.id"), nullable=False, index=True)

    data_consumo = Column(Date, nullable=False, default=date.today, index=True)
    competencia_ano = Column(Integer, nullable=False, index=True)
    competencia_mes = Column(Integer, nullable=False, index=True)

    quantidade = Column(Integer, nullable=False, default=1)

    origem = Column(String(20), nullable=False, default="MANUAL", index=True)
    status = Column(String(20), nullable=False, default="CONFIRMADO", index=True)

    agendamento_id = Column(Integer, ForeignKey("agendamentos.id"), nullable=True, index=True)
    pdv_venda_id = Column(Integer, ForeignKey("pdv_vendas.id"), nullable=True, index=True)
    pdv_venda_item_id = Column(Integer, ForeignKey("pdv_venda_itens.id"), nullable=True, index=True)

    observacoes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_agora_utc)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_agora_utc,
        onupdate=_agora_utc,
    )

    __table_args__ = (
        CheckConstraint(
            "competencia_mes >= 1 AND competencia_mes <= 12",
            name="ck_assinaturas_pet_consumos_competencia_mes_1_12",
        ),
        CheckConstraint(
            "competencia_ano >= 2020",
            name="ck_assinaturas_pet_consumos_competencia_ano_min",
        ),
        CheckConstraint(
            "quantidade >= 1",
            name="ck_assinaturas_pet_consumos_quantidade_min_1",
        ),
        CheckConstraint(
            "origem IN ('MANUAL', 'AGENDAMENTO', 'PDV', 'ATENDIMENTO')",
            name="ck_assinaturas_pet_consumos_origem",
        ),
        CheckConstraint(
            "status IN ('PENDENTE', 'CONFIRMADO', 'ESTORNADO', 'CANCELADO')",
            name="ck_assinaturas_pet_consumos_status",
        ),
    )

    assinatura = relationship("AssinaturaPet", back_populates="consumos")
    item = relationship("AssinaturaPetItem")
    empresa = relationship("Empresa")
    cliente = relationship("Cliente")
    pet = relationship("Pet")
    servico = relationship("Servico")
    agendamento = relationship("Agendamento")
    pdv_venda = relationship("PdvVenda")
    pdv_venda_item = relationship("PdvVendaItem")

    @property
    def referencia_competencia(self) -> str:
        return f"{self.competencia_ano:04d}-{self.competencia_mes:02d}"

    def confirmar(self):
        self.status = "CONFIRMADO"
        self.updated_at = _agora_utc()

    def estornar(self):
        self.status = "ESTORNADO"
        self.updated_at = _agora_utc()

    def cancelar(self):
        self.status = "CANCELADO"
        self.updated_at = _agora_utc()

    @classmethod
    def criar_competencia(cls, data_referencia: date | None = None) -> tuple[int, int]:
        data_base = data_referencia or date.today()
        return data_base.year, data_base.month