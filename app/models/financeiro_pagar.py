from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


def _agora_utc():
    return datetime.now(timezone.utc)


class FinanceiroPagar(Base):
    __tablename__ = "financeiro_pagar"

    id = Column(Integer, primary_key=True, index=True)

    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)

    descricao = Column(String(255), nullable=False)
    fornecedor = Column(String(255), nullable=True)
    observacao = Column(Text, nullable=True)

    valor = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    valor_pago = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))

    vencimento = Column(Date, nullable=False, index=True)
    data_pagamento = Column(Date, nullable=True, index=True)

    status = Column(String(20), nullable=False, default="PENDENTE", index=True)

    created_at = Column(DateTime(timezone=True), default=_agora_utc)
    updated_at = Column(DateTime(timezone=True), default=_agora_utc, onupdate=_agora_utc)

    empresa = relationship("Empresa")

    @property
    def esta_vencido(self):
        if self.status == "PAGO":
            return False
        return self.vencimento < date.today()

    @property
    def status_atual(self):
        if self.status == "PAGO":
            return "PAGO"
        if self.vencimento < date.today():
            return "VENCIDO"
        return "PENDENTE"