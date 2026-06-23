from datetime import datetime, date

from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.core.database import Base


class ConciliacaoBancaria(Base):
    __tablename__ = "conciliacoes_bancarias"

    id = Column(Integer, primary_key=True, index=True)

    empresa_id = Column(
        Integer,
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    nome_arquivo = Column(String(255), nullable=False)
    tipo_arquivo = Column(String(20), nullable=False)

    data_inicio = Column(Date, nullable=False, index=True)
    data_fim = Column(Date, nullable=False, index=True)

    movimentos_banco = Column(Integer, nullable=False, default=0)
    movimentos_sistema = Column(Integer, nullable=False, default=0)
    conciliados = Column(Integer, nullable=False, default=0)
    pendentes_banco = Column(Integer, nullable=False, default=0)
    pendentes_sistema = Column(Integer, nullable=False, default=0)

    total_banco_entradas = Column(Numeric(12, 2), nullable=False, default=0)
    total_banco_saidas = Column(Numeric(12, 2), nullable=False, default=0)
    total_sistema_entradas = Column(Numeric(12, 2), nullable=False, default=0)
    total_sistema_saidas = Column(Numeric(12, 2), nullable=False, default=0)

    diferenca_entradas = Column(Numeric(12, 2), nullable=False, default=0)
    diferenca_saidas = Column(Numeric(12, 2), nullable=False, default=0)

    tolerancia_centavos = Column(Integer, nullable=False, default=2)
    tolerancia_dias = Column(Integer, nullable=False, default=2)

    resultado_json = Column(JSONB, nullable=False)

    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
