from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from app.core.database import Base


class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    cnpj = Column(String(18), unique=True, nullable=True)
    ativa = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())