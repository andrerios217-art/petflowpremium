from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from app.core.database import Base


class Auditoria(Base):
    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    acao = Column(String(100), nullable=False)
    tabela = Column(String(100), nullable=False)
    registro_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())