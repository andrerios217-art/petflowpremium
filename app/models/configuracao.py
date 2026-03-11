from sqlalchemy import Column, ForeignKey, Integer, String
from app.core.database import Base


class Configuracao(Base):
    __tablename__ = "configuracao"


    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    chave = Column(String(100), nullable=False)
    valor = Column(String(255), nullable=False)