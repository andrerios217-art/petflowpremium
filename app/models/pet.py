from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from app.core.database import Base


class Pet(Base):
    __tablename__ = "pets"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)

    nome = Column(String(120), nullable=False)
    nascimento = Column(Date, nullable=True)
    raca = Column(String(120), nullable=True)
    sexo = Column(String(20), nullable=True)
    temperamento = Column(String(30), nullable=True)
    peso = Column(Numeric(10, 2), nullable=True)
    porte = Column(String(10), nullable=True)
    observacoes = Column(Text, nullable=True)

    pode_perfume = Column(Boolean, default=True, nullable=False)
    pode_acessorio = Column(Boolean, default=True, nullable=False)
    castrado = Column(Boolean, default=False, nullable=False)

    foto = Column(String(255), nullable=True)
    ativo = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())