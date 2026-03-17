from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class PetExame(Base):
    __tablename__ = "pet_exames"

    id = Column(Integer, primary_key=True, index=True)

    atendimento_id = Column(
        Integer,
        ForeignKey("atendimentos_clinicos.id"),
        nullable=False,
        index=True,
    )

    nome = Column(String(150), nullable=True)
    tipo = Column(String(100), nullable=True)
    descricao = Column(Text, nullable=True)
    resultado = Column(Text, nullable=True)
    observacoes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    atendimento = relationship("AtendimentoClinico", back_populates="exames")