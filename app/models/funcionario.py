from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func

from app.core.database import Base


class Funcionario(Base):
    __tablename__ = "funcionarios"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)

    nome = Column(String(150), nullable=False)
    cpf = Column(String(14), nullable=False, unique=True)
    email = Column(String(150), nullable=False, unique=True)
    telefone = Column(String(20), nullable=False)
    funcao = Column(String(30), nullable=False)
    crmv = Column(String(30), nullable=True)

    senha_hash = Column(String(255), nullable=False)

    acesso_dashboard = Column(Boolean, default=False, nullable=False)
    acesso_clientes = Column(Boolean, default=False, nullable=False)
    acesso_pets = Column(Boolean, default=False, nullable=False)
    acesso_servicos = Column(Boolean, default=False, nullable=False)
    acesso_funcionarios = Column(Boolean, default=False, nullable=False)
    acesso_agenda = Column(Boolean, default=False, nullable=False)
    acesso_producao = Column(Boolean, default=False, nullable=False)
    acesso_estoque = Column(Boolean, default=False, nullable=False)
    acesso_financeiro = Column(Boolean, default=False, nullable=False)
    acesso_crm = Column(Boolean, default=False, nullable=False)
    acesso_relatorios = Column(Boolean, default=False, nullable=False)
    acesso_configuracoes = Column(Boolean, default=False, nullable=False)

    # NOVO
    acesso_pdv = Column(Boolean, default=False, nullable=False, server_default="false")

    ativo = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())