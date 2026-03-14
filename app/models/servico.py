from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, func
from app.core.database import Base


class Servico(Base):
    __tablename__ = "servicos"

    id = Column(Integer, primary_key=True, index=True)

    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)

    nome = Column(String(120), nullable=False)

    # PETSHOP ou VETERINARIO
    tipo_servico = Column(String(20), nullable=False, default="PETSHOP", index=True)

    # G1 - Mini até G5 - Gigante
    porte_referencia = Column(String(10), nullable=False)

    custo = Column(Numeric(10, 2), nullable=False)
    venda = Column(Numeric(10, 2), nullable=False)

    tempo_minutos = Column(Integer, nullable=False)

    ativo = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())