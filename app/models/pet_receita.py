from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class PetReceita(Base):
    __tablename__ = "pet_receitas"

    id = Column(Integer, primary_key=True, index=True)

    atendimento_id = Column(
        Integer,
        ForeignKey("atendimentos_clinicos.id"),
        nullable=False,
        index=True,
    )

    descricao = Column(Text, nullable=True)
    orientacoes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    atendimento = relationship("AtendimentoClinico", back_populates="receitas")