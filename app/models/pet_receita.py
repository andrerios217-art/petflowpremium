
from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime
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

    pet_id = Column(
        Integer,
        ForeignKey("pets.id"),
        nullable=False,
        index=True,
    )

    descricao = Column(Text, nullable=False)
    orientacoes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    atendimento = relationship(
        "AtendimentoClinico",
        back_populates="receitas",
    )

    pet = relationship("Pet")

    def __repr__(self):
        return f"<PetReceita id={self.id} atendimento_id={self.atendimento_id}>"