from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProdutoResumoOut(BaseModel):
    id: int
    sku: str
    nome: str
    unidade: str
    ativo: bool
    codigo_barras_principal: Optional[str] = None
    preco_venda_atual: Decimal
    custo_medio_atual: Decimal

    model_config = ConfigDict(from_attributes=True)


class NotaEntradaItemOut(BaseModel):
    id: int
    nota_entrada_id: int
    item_numero: int
    produto_id: Optional[int]

    codigo_fornecedor: Optional[str]
    codigo_barras_nf: Optional[str]
    codigo_barras_tributavel_nf: Optional[str]
    descricao_nf: str

    ncm: Optional[str]
    cest: Optional[str]
    cfop: Optional[str]

    unidade_comercial: Optional[str]
    unidade_tributavel: Optional[str]

    quantidade_comercial: Decimal
    quantidade_tributavel: Decimal
    valor_unitario_comercial: Decimal
    valor_unitario_tributavel: Decimal

    valor_total_bruto: Decimal
    desconto: Decimal
    frete: Decimal
    seguro: Decimal
    outras_despesas: Decimal

    origem_fiscal: Optional[str]
    cst_icms: Optional[str]
    csosn: Optional[str]
    cst_pis: Optional[str]
    cst_cofins: Optional[str]

    aliquota_icms: Decimal
    aliquota_pis: Decimal
    aliquota_cofins: Decimal

    valor_icms: Decimal
    valor_pis: Decimal
    valor_cofins: Decimal

    match_tipo: str
    match_confiavel: bool
    observacao_match: Optional[str]

    created_at: datetime
    updated_at: datetime

    produto: Optional[ProdutoResumoOut] = None

    model_config = ConfigDict(from_attributes=True)


class NotaEntradaOut(BaseModel):
    id: int
    empresa_id: int

    chave_acesso: str
    numero: Optional[str]
    serie: Optional[str]
    modelo: Optional[str]

    data_emissao: Optional[datetime]
    data_entrada: Optional[datetime]

    fornecedor_cnpj: Optional[str]
    fornecedor_nome: Optional[str]

    valor_total_produtos: Decimal
    valor_total_nota: Decimal
    valor_frete: Decimal
    valor_seguro: Decimal
    valor_desconto: Decimal
    valor_outras_despesas: Decimal

    status: str
    xml_original: str

    created_at: datetime
    updated_at: datetime

    itens: list[NotaEntradaItemOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class NotaEntradaResumoOut(BaseModel):
    id: int
    empresa_id: int

    chave_acesso: str
    numero: Optional[str]
    serie: Optional[str]
    modelo: Optional[str]

    data_emissao: Optional[datetime]
    data_entrada: Optional[datetime]

    fornecedor_cnpj: Optional[str]
    fornecedor_nome: Optional[str]

    valor_total_produtos: Decimal
    valor_total_nota: Decimal
    status: str

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotaEntradaItemVincularIn(BaseModel):
    item_id: int
    produto_id: int
    salvar_vinculo_fornecedor: bool = True


class ProdutoBuscaOut(BaseModel):
    id: int
    sku: str
    nome: str
    unidade: str
    ativo: bool
    codigo_barras_principal: Optional[str] = None
    preco_venda_atual: Decimal
    custo_medio_atual: Decimal

    model_config = ConfigDict(from_attributes=True)