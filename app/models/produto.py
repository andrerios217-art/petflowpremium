from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    categoria_id = Column(Integer, ForeignKey("produto_categorias.id"), nullable=True, index=True)

    sku = Column(String(60), nullable=False)
    nome = Column(String(150), nullable=False)
    descricao = Column(Text, nullable=True)
    unidade = Column(String(20), nullable=False, default="UN", server_default="UN")

    ativo = Column(Boolean, nullable=False, default=True, server_default="true")
    aceita_fracionado = Column(Boolean, nullable=False, default=False, server_default="false")

    codigo_barras_principal = Column(String(60), nullable=True, index=True)

    preco_venda_atual = Column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )
    custo_medio_atual = Column(
        Numeric(10, 4),
        nullable=False,
        default=Decimal("0.0000"),
        server_default="0",
    )
    estoque_minimo = Column(
        Numeric(10, 3),
        nullable=False,
        default=Decimal("0.000"),
        server_default="0",
    )

    # Fiscal / tributário base
    ncm = Column(String(20), nullable=True, index=True)
    cest = Column(String(20), nullable=True)
    cfop_padrao = Column(String(10), nullable=True)
    origem_fiscal = Column(String(1), nullable=True)  # 0 a 8

    cst_icms = Column(String(4), nullable=True)
    csosn = Column(String(4), nullable=True)
    cst_pis = Column(String(4), nullable=True)
    cst_cofins = Column(String(4), nullable=True)

    aliquota_icms = Column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )
    aliquota_pis = Column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )
    aliquota_cofins = Column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )

    observacao = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("empresa_id", "sku", name="uq_produtos_empresa_sku"),
        UniqueConstraint(
            "empresa_id",
            "codigo_barras_principal",
            name="uq_produtos_empresa_codigo_barras_principal",
        ),
        CheckConstraint(
            "preco_venda_atual >= 0",
            name="ck_produtos_preco_venda_atual_non_negative",
        ),
        CheckConstraint(
            "custo_medio_atual >= 0",
            name="ck_produtos_custo_medio_atual_non_negative",
        ),
        CheckConstraint(
            "estoque_minimo >= 0",
            name="ck_produtos_estoque_minimo_non_negative",
        ),
        CheckConstraint(
            "aliquota_icms >= 0 AND aliquota_icms <= 100",
            name="ck_produtos_aliquota_icms_range",
        ),
        CheckConstraint(
            "aliquota_pis >= 0 AND aliquota_pis <= 100",
            name="ck_produtos_aliquota_pis_range",
        ),
        CheckConstraint(
            "aliquota_cofins >= 0 AND aliquota_cofins <= 100",
            name="ck_produtos_aliquota_cofins_range",
        ),
        CheckConstraint(
            "origem_fiscal IS NULL OR origem_fiscal IN ('0', '1', '2', '3', '4', '5', '6', '7', '8')",
            name="ck_produtos_origem_fiscal_valida",
        ),
    )

    categoria = relationship("ProdutoCategoria", back_populates="produtos")
    codigos_barras = relationship(
        "ProdutoCodigoBarras",
        back_populates="produto",
        cascade="all, delete-orphan",
    )
    saldos = relationship("EstoqueSaldo", back_populates="produto")
    movimentos = relationship("EstoqueMovimento", back_populates="produto")

    @property
    def esta_ativo(self) -> bool:
        return bool(self.ativo)

    def ativar(self):
        self.ativo = True
        self.updated_at = datetime.utcnow()

    def desativar(self):
        self.ativo = False
        self.updated_at = datetime.utcnow()

    def definir_preco_venda(self, valor: Decimal | float | str):
        valor_decimal = Decimal(str(valor))
        if valor_decimal < Decimal("0.00"):
            raise ValueError("O preço de venda não pode ser negativo.")

        self.preco_venda_atual = valor_decimal
        self.updated_at = datetime.utcnow()

    def definir_custo_medio(self, valor: Decimal | float | str):
        valor_decimal = Decimal(str(valor))
        if valor_decimal < Decimal("0.00"):
            raise ValueError("O custo médio não pode ser negativo.")

        self.custo_medio_atual = valor_decimal
        self.updated_at = datetime.utcnow()

    def definir_estoque_minimo(self, valor: Decimal | float | str):
        valor_decimal = Decimal(str(valor))
        if valor_decimal < Decimal("0.000"):
            raise ValueError("O estoque mínimo não pode ser negativo.")

        self.estoque_minimo = valor_decimal
        self.updated_at = datetime.utcnow()

    def definir_codigo_barras_principal(self, codigo: str | None):
        codigo_limpo = (codigo or "").strip()
        self.codigo_barras_principal = codigo_limpo or None
        self.updated_at = datetime.utcnow()

    def definir_dados_fiscais(
        self,
        ncm: str | None = None,
        cest: str | None = None,
        cfop_padrao: str | None = None,
        origem_fiscal: str | None = None,
        cst_icms: str | None = None,
        csosn: str | None = None,
        cst_pis: str | None = None,
        cst_cofins: str | None = None,
        aliquota_icms: Decimal | float | str = Decimal("0.00"),
        aliquota_pis: Decimal | float | str = Decimal("0.00"),
        aliquota_cofins: Decimal | float | str = Decimal("0.00"),
    ):
        aliquota_icms_decimal = Decimal(str(aliquota_icms))
        aliquota_pis_decimal = Decimal(str(aliquota_pis))
        aliquota_cofins_decimal = Decimal(str(aliquota_cofins))

        if aliquota_icms_decimal < Decimal("0.00") or aliquota_icms_decimal > Decimal("100.00"):
            raise ValueError("A alíquota de ICMS deve estar entre 0 e 100.")

        if aliquota_pis_decimal < Decimal("0.00") or aliquota_pis_decimal > Decimal("100.00"):
            raise ValueError("A alíquota de PIS deve estar entre 0 e 100.")

        if aliquota_cofins_decimal < Decimal("0.00") or aliquota_cofins_decimal > Decimal("100.00"):
            raise ValueError("A alíquota de COFINS deve estar entre 0 e 100.")

        origem = (origem_fiscal or "").strip()
        if origem and origem not in {"0", "1", "2", "3", "4", "5", "6", "7", "8"}:
            raise ValueError("A origem fiscal deve estar entre 0 e 8.")

        self.ncm = (ncm or "").strip() or None
        self.cest = (cest or "").strip() or None
        self.cfop_padrao = (cfop_padrao or "").strip() or None
        self.origem_fiscal = origem or None
        self.cst_icms = (cst_icms or "").strip() or None
        self.csosn = (csosn or "").strip() or None
        self.cst_pis = (cst_pis or "").strip() or None
        self.cst_cofins = (cst_cofins or "").strip() or None
        self.aliquota_icms = aliquota_icms_decimal
        self.aliquota_pis = aliquota_pis_decimal
        self.aliquota_cofins = aliquota_cofins_decimal
        self.updated_at = datetime.utcnow()