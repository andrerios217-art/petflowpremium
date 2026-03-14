from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime
from sqlalchemy.orm import relationship

from app.core.database import Base


class PetAlergia(Base):
    __tablename__ = "pet_alergias"

    id = Column(Integer, primary_key=True, index=True)

    pet_id = Column(
        Integer,
        ForeignKey("pets.id"),
        nullable=False,
        index=True,
    )

    nome = Column(String(255), nullable=False)
    tipo = Column(String(100), nullable=True)
    gravidade = Column(String(50), nullable=True)
    observacoes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    pet = relationship("Pet")

    def __repr__(self):
        return f"<PetAlergia id={self.id} pet_id={self.pet_id} nome={self.nome}>"