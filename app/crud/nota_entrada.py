from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.crud.estoque import _sincronizar_codigo_barras_principal
from app.models.estoque_deposito import EstoqueDeposito
from app.models.estoque_movimento import EstoqueMovimento
from app.models.estoque_saldo import EstoqueSaldo
from app.models.nota_entrada import NotaEntrada
from app.models.nota_entrada_item import NotaEntradaItem
from app.models.produto import Produto
from app.models.produto_codigo_barras import ProdutoCodigoBarras
from app.models.produto_fornecedor_vinculo import ProdutoFornecedorVinculo
from app.services.categorizacao_produto import classificar_categoria_produto
from app.services.nfe_importacao import importar_nfe_do_xml
from app.services.precificacao import calcular_preco_venda_sugerido

MATCH_CODIGO_BARRAS = "CODIGO_BARRAS"
MATCH_VINCULO_FORNECEDOR = "VINCULO_FORNECEDOR"
MATCH_CODIGO_FORNECEDOR = "CODIGO_FORNECEDOR"
MATCH_MANUAL = "MANUAL"
MATCH_CRIADO_NF = "CRIADO_NF"
MATCH_SEM = "SEM_MATCH"

STATUS_IMPORTADA = "IMPORTADA"
STATUS_CONFIRMADA = "CONFIRMADA"

TIPO_ENTRADA = "ENTRADA"
ORIGEM_NF_ENTRADA = "NF_ENTRADA"

ZERO = Decimal("0")
QTD_3 = Decimal("0.001")
CUSTO_4 = Decimal("0.0001")
PRECO_2 = Decimal("0.01")


def _decimal(value) -> Decimal:
    if value is None:
        return ZERO
    return Decimal(str(value))


def _qtd(value) -> Decimal:
    return _decimal(value).quantize(QTD_3, rounding=ROUND_HALF_UP)


def _custo(value) -> Decimal:
    return _decimal(value).quantize(CUSTO_4, rounding=ROUND_HALF_UP)


def _preco(value) -> Decimal:
    return _decimal(value).quantize(PRECO_2, rounding=ROUND_HALF_UP)


def _somente_digitos(valor: str | None) -> str:
    return re.sub(r"\D+", "", valor or "")


def _slug_curto(valor: str | None) -> str:
    texto = (valor or "").upper().strip()
    texto = re.sub(r"[^A-Z0-9]+", "-", texto)
    texto = re.sub(r"-{2,}", "-", texto).strip("-")
    return texto[:40]


def _normalizar_unidade(unidade: str | None) -> str:
    valor = (unidade or "").strip().upper()
    return valor[:20] if valor else "UN"


def _normalizar_texto(valor: str | None) -> str | None:
    if valor is None:
        return None
    texto = valor.strip()
    return texto or None


def _normalizar_codigo_barras(valor: str | None) -> str | None:
    texto = (valor or "").strip()
    return texto or None


def _buscar_produto_por_codigo_barras(
    db: Session,
    empresa_id: int,
    codigo: str | None,
) -> Optional[Produto]:
    codigo_normalizado = _normalizar_codigo_barras(codigo)
    if not codigo_normalizado:
        return None

    codigos_teste = [codigo_normalizado]
    codigo_digitos = _somente_digitos(codigo_normalizado)
    if codigo_digitos and codigo_digitos not in codigos_teste:
        codigos_teste.append(codigo_digitos)

    produto = (
        db.query(Produto)
        .filter(
            Produto.empresa_id == empresa_id,
            Produto.codigo_barras_principal.in_(codigos_teste),
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
            ProdutoCodigoBarras.codigo.in_(codigos_teste),
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

    codigo_barras_normalizado = _normalizar_codigo_barras(codigo_barras)
    if codigo_barras_normalizado:
        codigos_teste = [codigo_barras_normalizado]
        codigo_digitos = _somente_digitos(codigo_barras_normalizado)
        if codigo_digitos and codigo_digitos not in codigos_teste:
            codigos_teste.append(codigo_digitos)

        vinculo = (
            db.query(ProdutoFornecedorVinculo)
            .filter(
                ProdutoFornecedorVinculo.empresa_id == empresa_id,
                ProdutoFornecedorVinculo.fornecedor_cnpj == fornecedor_cnpj,
                ProdutoFornecedorVinculo.codigo_barras_fornecedor.in_(codigos_teste),
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

    if origem == MATCH_CRIADO_NF:
        return "Produto criado automaticamente a partir do item da NF."

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


def _get_or_create_saldo(
    db: Session,
    empresa_id: int,
    deposito_id: int,
    produto_id: int,
) -> EstoqueSaldo:
    saldo = (
        db.query(EstoqueSaldo)
        .filter(
            EstoqueSaldo.empresa_id == empresa_id,
            EstoqueSaldo.deposito_id == deposito_id,
            EstoqueSaldo.produto_id == produto_id,
        )
        .first()
    )
    if saldo:
        return saldo

    saldo = EstoqueSaldo(
        empresa_id=empresa_id,
        deposito_id=deposito_id,
        produto_id=produto_id,
        quantidade_atual=ZERO,
    )
    db.add(saldo)
    db.flush()
    return saldo


def _get_deposito_padrao_ativo(db: Session, empresa_id: int) -> EstoqueDeposito:
    deposito = (
        db.query(EstoqueDeposito)
        .filter(
            EstoqueDeposito.empresa_id == empresa_id,
            EstoqueDeposito.ativo.is_(True),
        )
        .order_by(EstoqueDeposito.padrao.desc(), EstoqueDeposito.nome.asc())
        .first()
    )
    if not deposito:
        raise HTTPException(
            status_code=400,
            detail="Nenhum depósito ativo encontrado para lançar a entrada da nota.",
        )
    return deposito


def _get_quantidade_item(item: NotaEntradaItem) -> Decimal:
    quantidade = _decimal(item.quantidade_comercial)
    if quantidade <= ZERO:
        quantidade = _decimal(item.quantidade_tributavel)
    quantidade = _qtd(quantidade)
    if quantidade <= ZERO:
        raise HTTPException(
            status_code=400,
            detail=f"Item {item.item_numero} possui quantidade inválida para confirmação.",
        )
    return quantidade


def _get_custo_unitario_item(item: NotaEntradaItem) -> Decimal:
    custo = _decimal(item.valor_unitario_comercial)
    if custo <= ZERO:
        custo = _decimal(item.valor_unitario_tributavel)

    if custo <= ZERO:
        quantidade = _get_quantidade_item(item)
        total = _decimal(item.valor_total_bruto) - _decimal(item.desconto)
        if quantidade > ZERO and total > ZERO:
            custo = total / quantidade

    return _custo(custo if custo > ZERO else ZERO)


def _calcular_custo_medio_ponderado(
    saldo_anterior: Decimal,
    custo_medio_anterior: Decimal,
    quantidade_entrada: Decimal,
    custo_entrada: Decimal,
) -> Decimal:
    if quantidade_entrada <= ZERO:
        return _custo(custo_medio_anterior)

    if saldo_anterior <= ZERO:
        return _custo(custo_entrada)

    quantidade_total = saldo_anterior + quantidade_entrada
    if quantidade_total <= ZERO:
        return _custo(custo_entrada)

    valor_anterior = saldo_anterior * custo_medio_anterior
    valor_entrada = quantidade_entrada * custo_entrada
    novo_custo = (valor_anterior + valor_entrada) / quantidade_total
    return _custo(novo_custo)


def _bloquear_se_nota_confirmada(nota: NotaEntrada) -> None:
    if nota.status == STATUS_CONFIRMADA:
        raise HTTPException(
            status_code=409,
            detail="Nota já confirmada. Não é permitido alterar vínculos ou editar itens após gerar entrada no estoque.",
        )


def _validar_itens_para_confirmacao(itens: list[NotaEntradaItem]) -> None:
    if not itens:
        raise HTTPException(
            status_code=400,
            detail="A nota não possui itens para confirmação.",
        )

    itens_sem_vinculo = [item.item_numero for item in itens if not item.produto_id]
    if itens_sem_vinculo:
        itens_txt = ", ".join(str(x) for x in itens_sem_vinculo)
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível confirmar a nota. Itens sem produto vinculado: {itens_txt}.",
        )

    itens_inativos = [
        item.item_numero
        for item in itens
        if item.produto is not None and not bool(item.produto.ativo)
    ]
    if itens_inativos:
        itens_txt = ", ".join(str(x) for x in itens_inativos)
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível confirmar a nota. Há itens vinculados a produtos inativos: {itens_txt}.",
        )


def _enriquecer_nota_com_resumo_estoque(db: Session, nota: NotaEntrada) -> NotaEntrada:
    nota.permite_edicao = nota.status != STATUS_CONFIRMADA
    nota.bloqueada_para_edicao = nota.status == STATUS_CONFIRMADA
    nota.motivo_bloqueio_edicao = (
        "Nota já confirmada. Não é permitido alterar vínculos ou editar itens após gerar entrada no estoque."
        if nota.status == STATUS_CONFIRMADA
        else None
    )

    movimentos = (
        db.query(EstoqueMovimento)
        .options(
            joinedload(EstoqueMovimento.produto),
            joinedload(EstoqueMovimento.deposito),
        )
        .filter(
            EstoqueMovimento.empresa_id == nota.empresa_id,
            EstoqueMovimento.origem == ORIGEM_NF_ENTRADA,
            EstoqueMovimento.origem_id == nota.id,
        )
        .order_by(EstoqueMovimento.id.asc())
        .all()
    )

    nota.movimentacoes_estoque = []
    nota.total_itens_confirmados = 0
    nota.total_quantidade_entrada = ZERO
    nota.total_produtos_afetados = 0
    nota.resumo_estoque_disponivel = False
    nota.confirmada_em = None

    if not movimentos:
        return nota

    produto_ids: set[int] = set()
    total_qtd = ZERO
    confirmada_em = None

    for movimento in movimentos:
        quantidade = _qtd(movimento.quantidade)
        custo_unitario = _custo(movimento.custo_unitario)
        valor_total = (quantidade * custo_unitario).quantize(CUSTO_4, rounding=ROUND_HALF_UP)

        nota.movimentacoes_estoque.append(
            {
                "movimento_id": movimento.id,
                "produto_id": movimento.produto_id,
                "produto_nome": movimento.produto.nome if movimento.produto else None,
                "produto_sku": movimento.produto.sku if movimento.produto else None,
                "deposito_id": movimento.deposito_id,
                "deposito_nome": movimento.deposito.nome if movimento.deposito else None,
                "quantidade": quantidade,
                "saldo_antes": _qtd(movimento.saldo_antes),
                "saldo_depois": _qtd(movimento.saldo_depois),
                "custo_unitario": custo_unitario,
                "valor_total": valor_total,
                "origem": movimento.origem,
                "origem_id": movimento.origem_id,
                "origem_item_id": getattr(movimento, "origem_item_id", None),
                "documento_referencia": movimento.documento_referencia,
                "observacao": movimento.observacao,
                "created_at": movimento.created_at,
            }
        )

        produto_ids.add(movimento.produto_id)
        total_qtd += quantidade

        if confirmada_em is None or (
            movimento.created_at is not None and movimento.created_at > confirmada_em
        ):
            confirmada_em = movimento.created_at

    nota.total_itens_confirmados = len(movimentos)
    nota.total_quantidade_entrada = _qtd(total_qtd)
    nota.total_produtos_afetados = len(produto_ids)
    nota.resumo_estoque_disponivel = True
    nota.confirmada_em = confirmada_em

    return nota


def _sku_ja_existe(db: Session, empresa_id: int, sku: str) -> bool:
    return (
        db.query(Produto.id)
        .filter(
            Produto.empresa_id == empresa_id,
            Produto.sku == sku,
        )
        .first()
        is not None
    )


def _gerar_sku_produto_nf(
    db: Session,
    empresa_id: int,
    item: NotaEntradaItem,
    sku_informado: str | None = None,
) -> str:
    sku_limpo = _slug_curto(sku_informado)
    if sku_limpo:
        if _sku_ja_existe(db, empresa_id, sku_limpo):
            raise HTTPException(status_code=400, detail=f"Já existe produto com SKU '{sku_limpo}'.")
        return sku_limpo

    barcode = _somente_digitos(item.codigo_barras_tributavel_nf or item.codigo_barras_nf)
    codigo_fornecedor = _slug_curto(item.codigo_fornecedor)
    descricao_base = _slug_curto(item.descricao_nf)[:18]

    base = barcode or codigo_fornecedor or descricao_base or f"NFITEM-{item.item_numero}"
    base = f"NF-{base}"[:40]

    sku = base
    sequencia = 2
    while _sku_ja_existe(db, empresa_id, sku):
        sufixo = f"-{sequencia}"
        sku = f"{base[: max(1, 40 - len(sufixo))]}{sufixo}"
        sequencia += 1

    return sku


def _preparar_vinculo_fornecedor(
    db: Session,
    empresa_id: int,
    nota: NotaEntrada,
    item: NotaEntradaItem,
    produto_id: int,
) -> None:
    if not nota.fornecedor_cnpj:
        return

    vinculo = (
        db.query(ProdutoFornecedorVinculo)
        .filter(
            ProdutoFornecedorVinculo.empresa_id == empresa_id,
            ProdutoFornecedorVinculo.fornecedor_cnpj == nota.fornecedor_cnpj,
            ProdutoFornecedorVinculo.produto_id == produto_id,
        )
        .first()
    )
    if not vinculo:
        vinculo = ProdutoFornecedorVinculo(
            empresa_id=empresa_id,
            fornecedor_cnpj=nota.fornecedor_cnpj,
            produto_id=produto_id,
        )
        db.add(vinculo)

    vinculo.codigo_fornecedor = item.codigo_fornecedor
    vinculo.codigo_barras_fornecedor = _normalizar_codigo_barras(
        item.codigo_barras_tributavel_nf or item.codigo_barras_nf
    )
    vinculo.ultima_descricao_nf = item.descricao_nf
    vinculo.ultimo_ncm = item.ncm
    vinculo.ultimo_cest = item.cest
    vinculo.ultimo_cfop = item.cfop


def _resolver_preco_venda_inicial(
    db: Session,
    empresa_id: int,
    custo_inicial: Decimal,
    categoria_id: int | None,
    preco_venda_informado: Decimal | None = None,
) -> Decimal:
    if preco_venda_informado is not None:
        return _preco(preco_venda_informado)

    preco_sugerido = calcular_preco_venda_sugerido(
        db=db,
        empresa_id=empresa_id,
        custo=custo_inicial,
        categoria_id=categoria_id,
    )
    return _preco(preco_sugerido)


def _resolver_categoria_inicial_produto_nf(
    db: Session,
    empresa_id: int,
    nota: NotaEntrada,
    item: NotaEntradaItem,
    codigo_barras: str | None,
) -> int | None:
    resultado = classificar_categoria_produto(
        db=db,
        empresa_id=empresa_id,
        descricao=item.descricao_nf,
        codigo_fornecedor=item.codigo_fornecedor,
        fornecedor_nome=nota.fornecedor_nome,
        codigo_barras=codigo_barras,
        ncm=item.ncm,
        usar_api_externa=True,
    )
    if not resultado or not resultado.categoria_id:
        return None

    return resultado.categoria_id


def _deve_recalcular_preco_venda_na_confirmacao(
    item: NotaEntradaItem,
    produto: Produto,
) -> bool:
    if item.match_tipo == MATCH_CRIADO_NF:
        return True

    return _decimal(produto.preco_venda_atual) <= ZERO


def _recalcular_preco_venda_confirmacao_nf(
    db: Session,
    empresa_id: int,
    produto: Produto,
    custo_base: Decimal,
) -> Decimal:
    preco_sugerido = calcular_preco_venda_sugerido(
        db=db,
        empresa_id=empresa_id,
        custo=custo_base,
        categoria_id=produto.categoria_id,
    )
    return _preco(preco_sugerido)


def _criar_produto_para_item_nota(
    db: Session,
    empresa_id: int,
    nota: NotaEntrada,
    item: NotaEntradaItem,
    sku: str | None = None,
    nome: str | None = None,
    unidade: str | None = None,
    codigo_barras: str | None = None,
    preco_venda: Decimal | None = None,
    custo_inicial: Decimal | None = None,
    salvar_vinculo_fornecedor: bool = True,
) -> Produto:
    if item.produto_id:
        produto_existente = (
            db.query(Produto)
            .filter(
                Produto.id == item.produto_id,
                Produto.empresa_id == empresa_id,
            )
            .first()
        )
        if produto_existente:
            return produto_existente

    codigo_barras_final = _normalizar_codigo_barras(
        codigo_barras or item.codigo_barras_tributavel_nf or item.codigo_barras_nf
    )

    produto_por_barcode = _buscar_produto_por_codigo_barras(
        db=db,
        empresa_id=empresa_id,
        codigo=codigo_barras_final,
    )
    if produto_por_barcode:
        item.produto_id = produto_por_barcode.id
        item.match_tipo = MATCH_CODIGO_BARRAS
        item.match_confiavel = bool(produto_por_barcode.ativo)
        item.observacao_match = _build_observacao_match(produto_por_barcode, MATCH_CODIGO_BARRAS)

        if salvar_vinculo_fornecedor:
            _preparar_vinculo_fornecedor(db, empresa_id, nota, item, produto_por_barcode.id)

        return produto_por_barcode

    nome_final = (nome or item.descricao_nf or "").strip()
    if not nome_final:
        raise HTTPException(
            status_code=400,
            detail=f"Item {item.item_numero} sem descrição válida para criar produto.",
        )

    sku_final = _gerar_sku_produto_nf(
        db=db,
        empresa_id=empresa_id,
        item=item,
        sku_informado=sku,
    )
    unidade_final = _normalizar_unidade(unidade or item.unidade_comercial or item.unidade_tributavel)
    custo_final = _custo(custo_inicial if custo_inicial is not None else _get_custo_unitario_item(item))
    categoria_id_final = _resolver_categoria_inicial_produto_nf(
        db=db,
        empresa_id=empresa_id,
        nota=nota,
        item=item,
        codigo_barras=codigo_barras_final,
    )
    preco_venda_final = _resolver_preco_venda_inicial(
        db=db,
        empresa_id=empresa_id,
        custo_inicial=custo_final,
        categoria_id=categoria_id_final,
        preco_venda_informado=preco_venda,
    )

    produto = Produto(
        empresa_id=empresa_id,
        categoria_id=categoria_id_final,
        sku=sku_final,
        nome=nome_final[:150],
        descricao=item.descricao_nf,
        unidade=unidade_final,
        ativo=True,
        aceita_fracionado=False,
        codigo_barras_principal=codigo_barras_final,
        preco_venda_atual=preco_venda_final,
        custo_medio_atual=custo_final,
        estoque_minimo=_qtd(ZERO),
        ncm=_normalizar_texto(item.ncm),
        cest=_normalizar_texto(item.cest),
        cfop_padrao=_normalizar_texto(item.cfop),
        origem_fiscal=_normalizar_texto(item.origem_fiscal),
        cst_icms=_normalizar_texto(item.cst_icms),
        csosn=_normalizar_texto(item.csosn),
        cst_pis=_normalizar_texto(item.cst_pis),
        cst_cofins=_normalizar_texto(item.cst_cofins),
        aliquota_icms=_preco(item.aliquota_icms),
        aliquota_pis=_preco(item.aliquota_pis),
        aliquota_cofins=_preco(item.aliquota_cofins),
        observacao="Produto criado automaticamente a partir da importação da NF-e.",
    )
    db.add(produto)
    db.flush()

    _sincronizar_codigo_barras_principal(
        db=db,
        empresa_id=empresa_id,
        produto=produto,
        codigo_principal=codigo_barras_final,
    )

    item.produto_id = produto.id
    item.match_tipo = MATCH_CRIADO_NF
    item.match_confiavel = True
    item.observacao_match = _build_observacao_match(produto, MATCH_CRIADO_NF)

    if salvar_vinculo_fornecedor:
        _preparar_vinculo_fornecedor(db, empresa_id, nota, item, produto.id)

    return produto


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
        status=STATUS_IMPORTADA,
        xml_original=nfe.xml_original,
    )

    db.add(nota)
    db.flush()

    try:
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
            db.flush()

            if not item.produto_id:
                _criar_produto_para_item_nota(
                    db=db,
                    empresa_id=empresa_id,
                    nota=nota,
                    item=item,
                    salvar_vinculo_fornecedor=True,
                )

        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise

    return obter_nota_entrada(db, empresa_id, nota.id)


def listar_notas_entrada(
    db: Session,
    empresa_id: int,
) -> list[NotaEntrada]:
    notas = (
        db.query(NotaEntrada)
        .filter(NotaEntrada.empresa_id == empresa_id)
        .order_by(NotaEntrada.id.desc())
        .all()
    )
    return [_enriquecer_nota_com_resumo_estoque(db, nota) for nota in notas]


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

    return _enriquecer_nota_com_resumo_estoque(db, nota)


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

    _bloquear_se_nota_confirmada(nota)

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

    if salvar_vinculo_fornecedor:
        _preparar_vinculo_fornecedor(db, empresa_id, nota, item, produto.id)

    db.commit()
    return obter_nota_entrada(db, empresa_id, nota_entrada_id)


def criar_produto_a_partir_item_nota(
    db: Session,
    empresa_id: int,
    nota_entrada_id: int,
    item_id: int,
    sku: str | None = None,
    nome: str | None = None,
    unidade: str | None = None,
    codigo_barras: str | None = None,
    preco_venda: Decimal | None = None,
    custo_inicial: Decimal | None = None,
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

    _bloquear_se_nota_confirmada(nota)

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

    _criar_produto_para_item_nota(
        db=db,
        empresa_id=empresa_id,
        nota=nota,
        item=item,
        sku=sku,
        nome=nome,
        unidade=unidade,
        codigo_barras=codigo_barras,
        preco_venda=preco_venda,
        custo_inicial=custo_inicial,
        salvar_vinculo_fornecedor=salvar_vinculo_fornecedor,
    )

    db.commit()
    return obter_nota_entrada(db, empresa_id, nota_entrada_id)


def confirmar_nota_entrada(
    db: Session,
    empresa_id: int,
    nota_entrada_id: int,
) -> NotaEntrada:
    nota = (
        db.query(NotaEntrada)
        .options(
            joinedload(NotaEntrada.itens).joinedload(NotaEntradaItem.produto),
        )
        .filter(
            NotaEntrada.id == nota_entrada_id,
            NotaEntrada.empresa_id == empresa_id,
        )
        .first()
    )
    if not nota:
        raise HTTPException(status_code=404, detail="Nota de entrada não encontrada.")

    _bloquear_se_nota_confirmada(nota)

    itens = sorted(nota.itens or [], key=lambda x: x.item_numero)
    _validar_itens_para_confirmacao(itens)

    deposito = _get_deposito_padrao_ativo(db, empresa_id)

    try:
        for item in itens:
            produto = item.produto
            if not produto:
                raise HTTPException(
                    status_code=400,
                    detail=f"Produto do item {item.item_numero} não encontrado para confirmação.",
                )

            quantidade = _get_quantidade_item(item)
            custo_unitario = _get_custo_unitario_item(item)

            saldo = _get_or_create_saldo(
                db=db,
                empresa_id=empresa_id,
                deposito_id=deposito.id,
                produto_id=produto.id,
            )

            saldo_antes = _qtd(saldo.quantidade_atual)
            saldo_depois = _qtd(saldo_antes + quantidade)
            custo_anterior = _custo(produto.custo_medio_atual)
            novo_custo_medio = _calcular_custo_medio_ponderado(
                saldo_anterior=saldo_antes,
                custo_medio_anterior=custo_anterior,
                quantidade_entrada=quantidade,
                custo_entrada=custo_unitario,
            )

            saldo.quantidade_atual = saldo_depois
            produto.custo_medio_atual = novo_custo_medio

            if _deve_recalcular_preco_venda_na_confirmacao(item, produto):
                produto.preco_venda_atual = _recalcular_preco_venda_confirmacao_nf(
                    db=db,
                    empresa_id=empresa_id,
                    produto=produto,
                    custo_base=novo_custo_medio,
                )

            movimento = EstoqueMovimento(
                empresa_id=empresa_id,
                deposito_id=deposito.id,
                produto_id=produto.id,
                usuario_id=None,
                tipo_movimento=TIPO_ENTRADA,
                origem=ORIGEM_NF_ENTRADA,
                origem_id=nota.id,
                origem_item_id=item.id,
                quantidade=quantidade,
                saldo_antes=saldo_antes,
                saldo_depois=saldo_depois,
                custo_unitario=custo_unitario,
                documento_referencia=nota.chave_acesso,
                observacao=f"Entrada gerada pela confirmação da NF-e {nota.numero or '-'} item {item.item_numero}.",
            )
            db.add(movimento)

        nota.status = STATUS_CONFIRMADA
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise

    return obter_nota_entrada(db, empresa_id, nota_entrada_id)