from __future__ import annotations

from typing import Optional

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.nota_entrada import NotaEntrada
from app.models.nota_entrada_item import NotaEntradaItem
from app.models.produto import Produto
from app.models.produto_codigo_barras import ProdutoCodigoBarras
from app.models.produto_fornecedor_vinculo import ProdutoFornecedorVinculo
from app.services.nfe_importacao import importar_nfe_do_xml


MATCH_CODIGO_BARRAS = "CODIGO_BARRAS"
MATCH_VINCULO_FORNECEDOR = "VINCULO_FORNECEDOR"
MATCH_CODIGO_FORNECEDOR = "CODIGO_FORNECEDOR"
MATCH_MANUAL = "MANUAL"
MATCH_SEM = "SEM_MATCH"


def _buscar_produto_por_codigo_barras(
    db: Session,
    empresa_id: int,
    codigo: str | None,
) -> Optional[Produto]:
    if not codigo:
        return None

    produto = (
        db.query(Produto)
        .filter(
            Produto.empresa_id == empresa_id,
            Produto.codigo_barras_principal == codigo,
        )
        .first()
    )
    if produto:
        return produto

    codigo_barra = (
        db.query(ProdutoCodigoBarras)
        .join(Produto, Produto.id == ProdutoCodigoBarras.produto_id)
        .filter(
            ProdutoCodigoBarras.empresa_id == empresa_id,
            ProdutoCodigoBarras.codigo == codigo,
            Produto.empresa_id == empresa_id,
        )
        .first()
    )
    if codigo_barra:
        return codigo_barra.produto

    return None


def _buscar_vinculo_fornecedor(
    db: Session,
    empresa_id: int,
    fornecedor_cnpj: str | None,
    codigo_fornecedor: str | None,
    codigo_barras: str | None,
) -> Optional[ProdutoFornecedorVinculo]:
    if not fornecedor_cnpj:
        return None

    if codigo_fornecedor:
        vinculo = (
            db.query(ProdutoFornecedorVinculo)
            .filter(
                ProdutoFornecedorVinculo.empresa_id == empresa_id,
                ProdutoFornecedorVinculo.fornecedor_cnpj == fornecedor_cnpj,
                ProdutoFornecedorVinculo.codigo_fornecedor == codigo_fornecedor,
            )
            .first()
        )
        if vinculo:
            return vinculo

    if codigo_barras:
        vinculo = (
            db.query(ProdutoFornecedorVinculo)
            .filter(
                ProdutoFornecedorVinculo.empresa_id == empresa_id,
                ProdutoFornecedorVinculo.fornecedor_cnpj == fornecedor_cnpj,
                ProdutoFornecedorVinculo.codigo_barras_fornecedor == codigo_barras,
            )
            .first()
        )
        if vinculo:
            return vinculo

    return None


def _build_observacao_match(produto: Produto, origem: str) -> str:
    if origem == MATCH_CODIGO_BARRAS:
        return (
            "Match automático por código de barras."
            if produto.ativo
            else "Produto encontrado por código de barras, mas está inativo."
        )

    if origem in {MATCH_VINCULO_FORNECEDOR, MATCH_CODIGO_FORNECEDOR}:
        return (
            "Match automático por vínculo fornecedor/produto."
            if produto.ativo
            else "Produto encontrado por vínculo fornecedor/produto, mas está inativo."
        )

    if origem == MATCH_MANUAL:
        return (
            "Vínculo manual realizado com produto ativo."
            if produto.ativo
            else "Vínculo manual realizado com produto inativo. Revise antes de confirmar a nota."
        )

    return "Produto não localizado automaticamente."


def _aplicar_match_automatico(
    db: Session,
    empresa_id: int,
    fornecedor_cnpj: str | None,
    item: NotaEntradaItem,
) -> None:
    codigo_barras_prioridade = item.codigo_barras_tributavel_nf or item.codigo_barras_nf

    produto_por_barcode = _buscar_produto_por_codigo_barras(
        db=db,
        empresa_id=empresa_id,
        codigo=codigo_barras_prioridade,
    )
    if produto_por_barcode:
        item.produto_id = produto_por_barcode.id
        item.match_tipo = MATCH_CODIGO_BARRAS
        item.match_confiavel = bool(produto_por_barcode.ativo)
        item.observacao_match = _build_observacao_match(produto_por_barcode, MATCH_CODIGO_BARRAS)
        return

    vinculo = _buscar_vinculo_fornecedor(
        db=db,
        empresa_id=empresa_id,
        fornecedor_cnpj=fornecedor_cnpj,
        codigo_fornecedor=item.codigo_fornecedor,
        codigo_barras=codigo_barras_prioridade,
    )
    if vinculo:
        produto = (
            db.query(Produto)
            .filter(
                Produto.id == vinculo.produto_id,
                Produto.empresa_id == empresa_id,
            )
            .first()
        )
        if produto:
            item.produto_id = produto.id
            item.match_tipo = (
                MATCH_CODIGO_FORNECEDOR
                if item.codigo_fornecedor and item.codigo_fornecedor == vinculo.codigo_fornecedor
                else MATCH_VINCULO_FORNECEDOR
            )
            item.match_confiavel = bool(produto.ativo)
            item.observacao_match = _build_observacao_match(produto, item.match_tipo)
            return

    item.produto_id = None
    item.match_tipo = MATCH_SEM
    item.match_confiavel = False
    item.observacao_match = "Produto não localizado automaticamente."


def importar_xml_nota_entrada(
    db: Session,
    empresa_id: int,
    xml_content: str,
) -> NotaEntrada:
    try:
        nfe = importar_nfe_do_xml(xml_content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    nota_existente = (
        db.query(NotaEntrada)
        .filter(
            NotaEntrada.empresa_id == empresa_id,
            NotaEntrada.chave_acesso == nfe.chave_acesso,
        )
        .first()
    )
    if nota_existente:
        raise HTTPException(
            status_code=400,
            detail="Já existe uma nota de entrada importada com esta chave de acesso.",
        )

    nota = NotaEntrada(
        empresa_id=empresa_id,
        chave_acesso=nfe.chave_acesso,
        numero=nfe.numero,
        serie=nfe.serie,
        modelo=nfe.modelo,
        data_emissao=nfe.data_emissao,
        data_entrada=nfe.data_entrada,
        fornecedor_cnpj=nfe.fornecedor_cnpj,
        fornecedor_nome=nfe.fornecedor_nome,
        valor_total_produtos=nfe.valor_total_produtos,
        valor_total_nota=nfe.valor_total_nota,
        valor_frete=nfe.valor_frete,
        valor_seguro=nfe.valor_seguro,
        valor_desconto=nfe.valor_desconto,
        valor_outras_despesas=nfe.valor_outras_despesas,
        status="IMPORTADA",
        xml_original=nfe.xml_original,
    )

    db.add(nota)
    db.flush()

    for item_importado in nfe.itens:
        item = NotaEntradaItem(
            nota_entrada_id=nota.id,
            item_numero=item_importado.item_numero,
            codigo_fornecedor=item_importado.codigo_fornecedor,
            codigo_barras_nf=item_importado.codigo_barras_nf,
            codigo_barras_tributavel_nf=item_importado.codigo_barras_tributavel_nf,
            descricao_nf=item_importado.descricao_nf,
            ncm=item_importado.ncm,
            cest=item_importado.cest,
            cfop=item_importado.cfop,
            unidade_comercial=item_importado.unidade_comercial,
            unidade_tributavel=item_importado.unidade_tributavel,
            quantidade_comercial=item_importado.quantidade_comercial,
            quantidade_tributavel=item_importado.quantidade_tributavel,
            valor_unitario_comercial=item_importado.valor_unitario_comercial,
            valor_unitario_tributavel=item_importado.valor_unitario_tributavel,
            valor_total_bruto=item_importado.valor_total_bruto,
            desconto=item_importado.desconto,
            frete=item_importado.frete,
            seguro=item_importado.seguro,
            outras_despesas=item_importado.outras_despesas,
            origem_fiscal=item_importado.origem_fiscal,
            cst_icms=item_importado.cst_icms,
            csosn=item_importado.csosn,
            cst_pis=item_importado.cst_pis,
            cst_cofins=item_importado.cst_cofins,
            aliquota_icms=item_importado.aliquota_icms,
            aliquota_pis=item_importado.aliquota_pis,
            aliquota_cofins=item_importado.aliquota_cofins,
            valor_icms=item_importado.valor_icms,
            valor_pis=item_importado.valor_pis,
            valor_cofins=item_importado.valor_cofins,
            match_tipo=MATCH_SEM,
            match_confiavel=False,
        )
        _aplicar_match_automatico(
            db=db,
            empresa_id=empresa_id,
            fornecedor_cnpj=nfe.fornecedor_cnpj,
            item=item,
        )
        db.add(item)

    db.commit()

    return obter_nota_entrada(db, empresa_id, nota.id)


def listar_notas_entrada(
    db: Session,
    empresa_id: int,
) -> list[NotaEntrada]:
    return (
        db.query(NotaEntrada)
        .filter(NotaEntrada.empresa_id == empresa_id)
        .order_by(NotaEntrada.id.desc())
        .all()
    )


def obter_nota_entrada(
    db: Session,
    empresa_id: int,
    nota_entrada_id: int,
) -> NotaEntrada:
    nota = (
        db.query(NotaEntrada)
        .options(joinedload(NotaEntrada.itens).joinedload(NotaEntradaItem.produto))
        .filter(
            NotaEntrada.id == nota_entrada_id,
            NotaEntrada.empresa_id == empresa_id,
        )
        .first()
    )
    if not nota:
        raise HTTPException(status_code=404, detail="Nota de entrada não encontrada.")
    return nota


def buscar_produtos_para_vinculo(
    db: Session,
    empresa_id: int,
    termo: str,
    incluir_inativos: bool = True,
    limite: int = 20,
) -> list[Produto]:
    termo = (termo or "").strip()
    if len(termo) < 2:
        return []

    query = db.query(Produto).filter(Produto.empresa_id == empresa_id)

    if not incluir_inativos:
        query = query.filter(Produto.ativo.is_(True))

    like = f"%{termo}%"
    query = query.filter(
        or_(
            Produto.nome.ilike(like),
            Produto.sku.ilike(like),
            Produto.codigo_barras_principal.ilike(like),
        )
    )

    return (
        query.order_by(Produto.ativo.desc(), Produto.nome.asc())
        .limit(max(1, min(limite, 50)))
        .all()
    )


def vincular_item_nota_entrada(
    db: Session,
    empresa_id: int,
    nota_entrada_id: int,
    item_id: int,
    produto_id: int,
    salvar_vinculo_fornecedor: bool = True,
) -> NotaEntrada:
    nota = (
        db.query(NotaEntrada)
        .filter(
            NotaEntrada.id == nota_entrada_id,
            NotaEntrada.empresa_id == empresa_id,
        )
        .first()
    )
    if not nota:
        raise HTTPException(status_code=404, detail="Nota de entrada não encontrada.")

    item = (
        db.query(NotaEntradaItem)
        .filter(
            NotaEntradaItem.id == item_id,
            NotaEntradaItem.nota_entrada_id == nota.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item da nota não encontrado.")

    produto = (
        db.query(Produto)
        .filter(
            Produto.id == produto_id,
            Produto.empresa_id == empresa_id,
        )
        .first()
    )
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    item.produto_id = produto.id
    item.match_tipo = MATCH_MANUAL
    item.match_confiavel = bool(produto.ativo)
    item.observacao_match = _build_observacao_match(produto, MATCH_MANUAL)

    if salvar_vinculo_fornecedor and nota.fornecedor_cnpj:
        vinculo = (
            db.query(ProdutoFornecedorVinculo)
            .filter(
                ProdutoFornecedorVinculo.empresa_id == empresa_id,
                ProdutoFornecedorVinculo.fornecedor_cnpj == nota.fornecedor_cnpj,
                ProdutoFornecedorVinculo.produto_id == produto.id,
            )
            .first()
        )

        if not vinculo:
            vinculo = ProdutoFornecedorVinculo(
                empresa_id=empresa_id,
                fornecedor_cnpj=nota.fornecedor_cnpj,
                produto_id=produto.id,
            )
            db.add(vinculo)

        vinculo.codigo_fornecedor = item.codigo_fornecedor
        vinculo.codigo_barras_fornecedor = item.codigo_barras_tributavel_nf or item.codigo_barras_nf
        vinculo.ultima_descricao_nf = item.descricao_nf
        vinculo.ultimo_ncm = item.ncm
        vinculo.ultimo_cest = item.cest
        vinculo.ultimo_cfop = item.cfop

    db.commit()

    return obter_nota_entrada(db, empresa_id, nota_entrada_id)