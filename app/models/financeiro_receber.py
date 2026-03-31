from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


def _agora_utc():
    return datetime.now(timezone.utc)


class FinanceiroReceber(Base):
    __tablename__ = "financeiro_receber"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True, index=True)

    origem_tipo = Column(String(50), nullable=True, index=True)
    origem_id = Column(Integer, nullable=True, index=True)

    descricao = Column(String(255), nullable=False)
    observacao = Column(Text, nullable=True)

    valor = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    valor_pago = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))

    vencimento = Column(Date, nullable=False, index=True)
    data_pagamento = Column(Date, nullable=True, index=True)

    status = Column(String(20), nullable=False, default="PENDENTE", index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_agora_utc)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_agora_utc,
        onupdate=_agora_utc,
    )

    empresa = relationship("Empresa")
    cliente = relationship("Cliente")

    @property
    def esta_vencido(self) -> bool:
        if self.status in ("PAGO", "CANCELADO"):
            return False
        return self.vencimento < date.today()

    @property
    def status_atual(self) -> str:
        if self.status == "PAGO":
            return "PAGO"
        if self.status == "CANCELADO":
            return "CANCELADO"
        if self.vencimento < date.today():
            return "VENCIDO"
        return "PENDENTE"