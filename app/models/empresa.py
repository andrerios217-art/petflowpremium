from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.core.database import Base


class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)

    nome = Column(String(150), nullable=False)
    cnpj = Column(String(18), nullable=True)

    # 🔥 NOVO: logo configurável por loja
    logo_url = Column(String(255), nullable=True)

    ativa = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)