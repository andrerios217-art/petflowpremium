from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime
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

    pet_id = Column(
        Integer,
        ForeignKey("pets.id"),
        nullable=False,
        index=True,
    )

    nome = Column(String(255), nullable=False)
    tipo = Column(String(100), nullable=True)
    status = Column(String(50), nullable=True, default="SOLICITADO")
    resultado = Column(Text, nullable=True)
    observacoes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    atendimento = relationship(
        "AtendimentoClinico",
        back_populates="exames",
    )

    pet = relationship("Pet")

    def __repr__(self):
        return f"<PetExame id={self.id} atendimento_id={self.atendimento_id} nome={self.nome}>"