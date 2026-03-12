from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from app.core.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)

    nome = Column(String(150), nullable=False)
    cpf = Column(String(14), unique=True, nullable=True)
    email = Column(String(150), nullable=True)
    telefone = Column(String(20), nullable=True)
    telefone_fixo = Column(String(20), nullable=True)

    ativo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())