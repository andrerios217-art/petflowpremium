from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.core.database import Base


class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)

    nome = Column(String(150), nullable=False)
    cnpj = Column(String(18), nullable=True)

    razao_social = Column(String(180), nullable=True)
    nome_fantasia = Column(String(180), nullable=True)

    telefone = Column(String(25), nullable=True)
    email = Column(String(150), nullable=True)

    cep = Column(String(10), nullable=True)
    logradouro = Column(String(180), nullable=True)
    numero = Column(String(20), nullable=True)
    complemento = Column(String(120), nullable=True)
    bairro = Column(String(120), nullable=True)
    cidade = Column(String(120), nullable=True)
    uf = Column(String(2), nullable=True)

    # Endereço exibido/operacional da loja
    endereco_loja = Column(String(255), nullable=True)

    # logo configurável por loja
    logo_url = Column(String(255), nullable=True)

    ativa = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)