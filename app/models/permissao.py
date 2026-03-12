from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from app.core.database import Base


class Permissao(Base):
    __tablename__ = "permissao"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    modulo = Column(String(50), nullable=False)
    pode_visualizar = Column(Boolean, default=False, nullable=False)
    pode_editar = Column(Boolean, default=False, nullable=False)
    pode_excluir = Column(Boolean, default=False, nullable=False)