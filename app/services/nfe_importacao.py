from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Optional
import xml.etree.ElementTree as ET


NAMESPACE_NFE = {"nfe": "http://www.portalfiscal.inf.br/nfe"}
ZERO = Decimal("0")


@dataclass
class NFeItemImportado:
    item_numero: int
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


@dataclass
class NFeImportada:
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
    xml_original: str
    itens: list[NFeItemImportado]


def _text(node: Optional[ET.Element]) -> Optional[str]:
    if node is None or node.text is None:
        return None
    value = node.text.strip()
    return value or None


def _find_text(parent: Optional[ET.Element], path: str) -> Optional[str]:
    if parent is None:
        return None
    return _text(parent.find(path, NAMESPACE_NFE))


def _parse_decimal(value: Optional[str], default: Decimal = ZERO) -> Decimal:
    if value is None or str(value).strip() == "":
        return default
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return default


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None

    value = value.strip()
    try:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _limpar_codigo_barras(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    codigo = value.strip()
    if not codigo or codigo.upper() == "SEM GTIN":
        return None
    return codigo


def _obter_root(xml_content: str) -> ET.Element:
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as exc:
        raise ValueError("XML da NF-e inválido.") from exc

    if root.tag.endswith("nfeProc"):
        nfe = root.find("nfe:NFe", NAMESPACE_NFE)
        if nfe is None:
            raise ValueError("XML da NF-e inválido: tag NFe não encontrada.")
        return nfe

    if root.tag.endswith("NFe"):
        return root

    raise ValueError("XML informado não parece ser uma NF-e válida.")


def _obter_inf_nfe(root: ET.Element) -> ET.Element:
    inf_nfe = root.find("nfe:infNFe", NAMESPACE_NFE)
    if inf_nfe is None:
        raise ValueError("XML da NF-e inválido: tag infNFe não encontrada.")
    return inf_nfe


def _extrair_chave_acesso(root: ET.Element, inf_nfe: ET.Element) -> str:
    prot_chave = _find_text(root, "nfe:protNFe/nfe:infProt/nfe:chNFe")
    if prot_chave:
        return prot_chave

    inf_id = inf_nfe.attrib.get("Id", "").strip()
    if inf_id.startswith("NFe") and len(inf_id) >= 47:
        return inf_id[3:]

    raise ValueError("Não foi possível identificar a chave de acesso da NF-e.")


def _extrair_icms(imposto_node: Optional[ET.Element]) -> dict[str, Any]:
    resultado = {
        "origem_fiscal": None,
        "cst_icms": None,
        "csosn": None,
        "aliquota_icms": ZERO,
        "valor_icms": ZERO,
    }

    if imposto_node is None:
        return resultado

    icms_node = imposto_node.find("nfe:ICMS", NAMESPACE_NFE)
    if icms_node is None:
        return resultado

    grupo = next(iter(list(icms_node)), None)
    if grupo is None:
        return resultado

    resultado["origem_fiscal"] = _find_text(grupo, "nfe:orig")
    resultado["cst_icms"] = _find_text(grupo, "nfe:CST")
    resultado["csosn"] = _find_text(grupo, "nfe:CSOSN")
    resultado["aliquota_icms"] = _parse_decimal(_find_text(grupo, "nfe:pICMS"))
    resultado["valor_icms"] = _parse_decimal(_find_text(grupo, "nfe:vICMS"))
    return resultado


def _extrair_pis(imposto_node: Optional[ET.Element]) -> dict[str, Any]:
    resultado = {
        "cst_pis": None,
        "aliquota_pis": ZERO,
        "valor_pis": ZERO,
    }

    if imposto_node is None:
        return resultado

    pis_node = imposto_node.find("nfe:PIS", NAMESPACE_NFE)
    if pis_node is None:
        return resultado

    grupo = next(iter(list(pis_node)), None)
    if grupo is None:
        return resultado

    resultado["cst_pis"] = _find_text(grupo, "nfe:CST")
    resultado["aliquota_pis"] = _parse_decimal(_find_text(grupo, "nfe:pPIS"))
    resultado["valor_pis"] = _parse_decimal(_find_text(grupo, "nfe:vPIS"))
    return resultado


def _extrair_cofins(imposto_node: Optional[ET.Element]) -> dict[str, Any]:
    resultado = {
        "cst_cofins": None,
        "aliquota_cofins": ZERO,
        "valor_cofins": ZERO,
    }

    if imposto_node is None:
        return resultado

    cofins_node = imposto_node.find("nfe:COFINS", NAMESPACE_NFE)
    if cofins_node is None:
        return resultado

    grupo = next(iter(list(cofins_node)), None)
    if grupo is None:
        return resultado

    resultado["cst_cofins"] = _find_text(grupo, "nfe:CST")
    resultado["aliquota_cofins"] = _parse_decimal(_find_text(grupo, "nfe:pCOFINS"))
    resultado["valor_cofins"] = _parse_decimal(_find_text(grupo, "nfe:vCOFINS"))
    return resultado


def importar_nfe_do_xml(xml_content: str) -> NFeImportada:
    xml_content = (xml_content or "").strip()
    if not xml_content:
        raise ValueError("O XML da NF-e não foi informado.")

    root = _obter_root(xml_content)
    inf_nfe = _obter_inf_nfe(root)

    ide = inf_nfe.find("nfe:ide", NAMESPACE_NFE)
    emit = inf_nfe.find("nfe:emit", NAMESPACE_NFE)
    total = inf_nfe.find("nfe:total/nfe:ICMSTot", NAMESPACE_NFE)

    chave_acesso = _extrair_chave_acesso(root, inf_nfe)
    numero = _find_text(ide, "nfe:nNF")
    serie = _find_text(ide, "nfe:serie")
    modelo = _find_text(ide, "nfe:mod")

    data_emissao = _parse_datetime(_find_text(ide, "nfe:dhEmi") or _find_text(ide, "nfe:dEmi"))
    data_entrada = _parse_datetime(_find_text(ide, "nfe:dhSaiEnt") or _find_text(ide, "nfe:dSaiEnt"))

    fornecedor_cnpj = _find_text(emit, "nfe:CNPJ") or _find_text(emit, "nfe:CPF")
    fornecedor_nome = _find_text(emit, "nfe:xNome")

    valor_total_produtos = _parse_decimal(_find_text(total, "nfe:vProd"))
    valor_total_nota = _parse_decimal(_find_text(total, "nfe:vNF"))
    valor_frete = _parse_decimal(_find_text(total, "nfe:vFrete"))
    valor_seguro = _parse_decimal(_find_text(total, "nfe:vSeg"))
    valor_desconto = _parse_decimal(_find_text(total, "nfe:vDesc"))
    valor_outras_despesas = _parse_decimal(_find_text(total, "nfe:vOutro"))

    itens: list[NFeItemImportado] = []

    for det in inf_nfe.findall("nfe:det", NAMESPACE_NFE):
        prod = det.find("nfe:prod", NAMESPACE_NFE)
        imposto = det.find("nfe:imposto", NAMESPACE_NFE)

        if prod is None:
            continue

        icms = _extrair_icms(imposto)
        pis = _extrair_pis(imposto)
        cofins = _extrair_cofins(imposto)

        item = NFeItemImportado(
            item_numero=int(det.attrib.get("nItem", "0") or 0),
            codigo_fornecedor=_find_text(prod, "nfe:cProd"),
            codigo_barras_nf=_limpar_codigo_barras(_find_text(prod, "nfe:cEAN")),
            codigo_barras_tributavel_nf=_limpar_codigo_barras(_find_text(prod, "nfe:cEANTrib")),
            descricao_nf=_find_text(prod, "nfe:xProd") or "ITEM SEM DESCRIÇÃO",
            ncm=_find_text(prod, "nfe:NCM"),
            cest=_find_text(prod, "nfe:CEST"),
            cfop=_find_text(prod, "nfe:CFOP"),
            unidade_comercial=_find_text(prod, "nfe:uCom"),
            unidade_tributavel=_find_text(prod, "nfe:uTrib"),
            quantidade_comercial=_parse_decimal(_find_text(prod, "nfe:qCom")),
            quantidade_tributavel=_parse_decimal(_find_text(prod, "nfe:qTrib")),
            valor_unitario_comercial=_parse_decimal(_find_text(prod, "nfe:vUnCom")),
            valor_unitario_tributavel=_parse_decimal(_find_text(prod, "nfe:vUnTrib")),
            valor_total_bruto=_parse_decimal(_find_text(prod, "nfe:vProd")),
            desconto=_parse_decimal(_find_text(prod, "nfe:vDesc")),
            frete=_parse_decimal(_find_text(prod, "nfe:vFrete")),
            seguro=_parse_decimal(_find_text(prod, "nfe:vSeg")),
            outras_despesas=_parse_decimal(_find_text(prod, "nfe:vOutro")),
            origem_fiscal=icms["origem_fiscal"],
            cst_icms=icms["cst_icms"],
            csosn=icms["csosn"],
            cst_pis=pis["cst_pis"],
            cst_cofins=cofins["cst_cofins"],
            aliquota_icms=icms["aliquota_icms"],
            aliquota_pis=pis["aliquota_pis"],
            aliquota_cofins=cofins["aliquota_cofins"],
            valor_icms=icms["valor_icms"],
            valor_pis=pis["valor_pis"],
            valor_cofins=cofins["valor_cofins"],
        )
        itens.append(item)

    if not itens:
        raise ValueError("Nenhum item foi encontrado no XML da NF-e.")

    return NFeImportada(
        chave_acesso=chave_acesso,
        numero=numero,
        serie=serie,
        modelo=modelo,
        data_emissao=data_emissao,
        data_entrada=data_entrada,
        fornecedor_cnpj=fornecedor_cnpj,
        fornecedor_nome=fornecedor_nome,
        valor_total_produtos=valor_total_produtos,
        valor_total_nota=valor_total_nota,
        valor_frete=valor_frete,
        valor_seguro=valor_seguro,
        valor_desconto=valor_desconto,
        valor_outras_despesas=valor_outras_despesas,
        xml_original=xml_content,
        itens=itens,
    )