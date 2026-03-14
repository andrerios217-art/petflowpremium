from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship

from app.core.database import Base


class PetAnamnese(Base):
    __tablename__ = "pet_anamneses"

    id = Column(Integer, primary_key=True, index=True)

    atendimento_id = Column(
        Integer,
        ForeignKey("atendimentos_clinicos.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    pet_id = Column(
        Integer,
        ForeignKey("pets.id"),
        nullable=False,
        index=True,
    )

    queixa_principal = Column(Text, nullable=True)
    historico_atual = Column(Text, nullable=True)
    alimentacao = Column(Text, nullable=True)
    alergias = Column(Text, nullable=True)
    uso_medicacao_atual = Column(Text, nullable=True)
    observacoes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    atendimento = relationship(
        "AtendimentoClinico",
        back_populates="anamnese",
    )

    pet = relationship("Pet")

    def __repr__(self):
        return f"<PetAnamnese id={self.id} atendimento_id={self.atendimento_id} pet_id={self.pet_id}>"