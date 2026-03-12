from sqlalchemy import Column, ForeignKey, Integer, String
from app.core.database import Base


class Endereco(Base):
    __tablename__ = "enderecos"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)

    cep = Column(String(9), nullable=True)
    rua = Column(String(150), nullable=True)
    numero = Column(String(20), nullable=True)
    bairro = Column(String(100), nullable=True)
    cidade = Column(String(100), nullable=True)
    uf = Column(String(2), nullable=True)
    complemento = Column(String(120), nullable=True)