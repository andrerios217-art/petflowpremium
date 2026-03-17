from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Date,
    DateTime,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class ComissaoFechamento(Base):
    __tablename__ = "comissao_fechamentos"
    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "funcionario_id",
            "competencia",
            name="uq_comissao_fechamento_empresa_funcionario_competencia",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    funcionario_id = Column(Integer, ForeignKey("funcionarios.id"), nullable=False, index=True)

    competencia = Column(Date, nullable=False, index=True)

    pontos_total = Column(Integer, nullable=False, default=0)
    valor_final = Column(Numeric(10, 2), nullable=False, default=0)

    status = Column(String(30), nullable=False, default="FECHADO", index=True)

    aprovado_por = Column(Integer, nullable=True)
    aprovado_em = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    funcionario = relationship("Funcionario")