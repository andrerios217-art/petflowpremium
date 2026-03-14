from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship

from app.core.database import Base


class PetProntuario(Base):
    __tablename__ = "pet_prontuarios"

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

    exame_fisico = Column(Text, nullable=True)
    diagnostico = Column(Text, nullable=True)
    conduta = Column(Text, nullable=True)
    observacoes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    atendimento = relationship(
        "AtendimentoClinico",
        back_populates="prontuario",
    )

    pet = relationship("Pet")

    def __repr__(self):
        return f"<PetProntuario id={self.id} atendimento_id={self.atendimento_id} pet_id={self.pet_id}>"