from sqlalchemy import Column, Integer, ForeignKey, String, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class AtendimentoClinicoItem(Base):
    __tablename__ = "atendimento_clinico_itens"

    id = Column(Integer, primary_key=True, index=True)

    atendimento_id = Column(
        Integer,
        ForeignKey("atendimentos_clinicos.id"),
        nullable=False
    )

    servico_id = Column(
        Integer,
        ForeignKey("servicos.id"),
        nullable=True
    )

    descricao = Column(String(255), nullable=False)

    quantidade = Column(Integer, default=1)

    valor_unitario = Column(Float, default=0)

    valor_total = Column(Float, default=0)

    tipo_item = Column(
        String(50),
        nullable=True
    )

    created_at = Column(DateTime, default=datetime.utcnow)

    # RELACIONAMENTOS

    atendimento = relationship(
        "AtendimentoClinico",
        back_populates="itens"
    )

    servico = relationship("Servico")

    def calcular_total(self):
        self.valor_total = (self.quantidade or 0) * (self.valor_unitario or 0)