from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class PetReceitaEmitida(Base):
    __tablename__ = "pet_receitas_emitidas"

    id = Column(Integer, primary_key=True, index=True)

    empresa_id = Column(
        Integer,
        ForeignKey("empresas.id"),
        nullable=False,
        index=True,
    )

    atendimento_id = Column(
        Integer,
        ForeignKey("atendimentos_clinicos.id"),
        nullable=False,
        index=True,
    )

    pet_id = Column(
        Integer,
        ForeignKey("pets.id"),
        nullable=False,
        index=True,
    )

    cliente_id = Column(
        Integer,
        ForeignKey("clientes.id"),
        nullable=False,
        index=True,
    )

    veterinario_id = Column(
        Integer,
        ForeignKey("funcionarios.id"),
        nullable=True,
        index=True,
    )

    codigo_verificacao = Column(String(32), nullable=False, unique=True, index=True)
    hash_documento = Column(String(128), nullable=False, index=True)

    snapshot_json = Column(Text, nullable=False)
    snapshot_texto_canonico = Column(Text, nullable=False)

    emitido_em = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    cancelado_em = Column(DateTime, nullable=True)
    cancelado_motivo = Column(Text, nullable=True)

    empresa = relationship("Empresa")
    atendimento = relationship("AtendimentoClinico", back_populates="receitas_emitidas")
    pet = relationship("Pet")
    cliente = relationship("Cliente")
    veterinario = relationship("Funcionario")

    @property
    def ativo(self) -> bool:
        return self.cancelado_em is None