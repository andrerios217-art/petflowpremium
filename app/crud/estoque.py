import csv
import io
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import and_, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.estoque_deposito import EstoqueDeposito
from app.models.estoque_movimento import EstoqueMovimento
from app.models.estoque_saldo import EstoqueSaldo
from app.models.produto import Produto
from app.models.produto_categoria import ProdutoCategoria
from app.models.produto_codigo_barras import ProdutoCodigoBarras
from app.schemas.estoque import (
    EstoqueDepositoCreate,
    EstoqueDepositoUpdate,
    EstoqueInventarioIn,
    EstoqueMovimentoAjusteIn,
    EstoqueMovimentoEntradaManualIn,
    EstoqueMovimentoSaidaManualIn,
    EstoqueTransferenciaIn,
    ProdutoCategoriaCreate,
    ProdutoCategoriaUpdate,
    ProdutoCodigoBarrasCreate,
    ProdutoCreate,
    ProdutoUpdate,
)

ZERO = Decimal("0")


def _get_categoria_or_404(db: Session, empresa_id: int, categoria_id: int) -> ProdutoCategoria:
    categoria = (
        db.query(ProdutoCategoria)
        .filter(
            ProdutoCategoria.id == categoria_id,
            ProdutoCategoria.empresa_id == empresa_id,
        )
        .first()
    )
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")
    return categoria


def _get_produto_or_404(db: Session, empresa_id: int, produto_id: int) -> Produto:
    produto = (
        db.query(Produto)
        .options(joinedload(Produto.codigos_barras))
        .filter(
            Produto.id == produto_id,
            Produto.empresa_id == empresa_id,
        )
        .first()
    )
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return produto


def _validar_produto_ativo_para_movimentacao(produto: Produto):
    if not bool(produto.ativo):
        raise HTTPException(
            status_code=400,
            detail="Produto inativo não pode ser usado em novas movimentações manuais.",
        )


def _get_deposito_or_404(db: Session, empresa_id: int, deposito_id: int) -> EstoqueDeposito:
    deposito = (
        db.query(EstoqueDeposito)
        .filter(
            EstoqueDeposito.id == deposito_id,
            EstoqueDeposito.empresa_id == empresa_id,
        )
        .first()
    )
    if not deposito:
        raise HTTPException(status_code=404, detail="Depósito não encontrado.")
    return deposito


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


def _normalizar_texto(valor: str | None) -> str | None:
    if valor is None:
        return None
    texto = valor.strip()
    return texto or None


def _sincronizar_codigo_barras_principal(
    db: Session,
    empresa_id: int,
    produto: Produto,
    codigo_principal: str | None,
):
    codigo_normalizado = _normalizar_texto(codigo_principal)

    if not codigo_normalizado:
        (
            db.query(ProdutoCodigoBarras)
            .filter(
                ProdutoCodigoBarras.empresa_id == empresa_id,
                ProdutoCodigoBarras.produto_id == produto.id,
                ProdutoCodigoBarras.principal.is_(True),
            )
            .update({"principal": False}, synchronize_session=False)
        )
        produto.codigo_barras_principal = None
        return

    codigo_existente = (
        db.query(ProdutoCodigoBarras)
        .filter(
            ProdutoCodigoBarras.empresa_id == empresa_id,
            ProdutoCodigoBarras.codigo == codigo_normalizado,
            ProdutoCodigoBarras.produto_id != produto.id,
        )
        .first()
    )
    if codigo_existente:
        raise HTTPException(status_code=400, detail="Código de barras principal já cadastrado em outro produto.")

    (
        db.query(ProdutoCodigoBarras)
        .filter(
            ProdutoCodigoBarras.empresa_id == empresa_id,
            ProdutoCodigoBarras.produto_id == produto.id,
        )
        .update({"principal": False}, synchronize_session=False)
    )

    codigo_produto = (
        db.query(ProdutoCodigoBarras)
        .filter(
            ProdutoCodigoBarras.empresa_id == empresa_id,
            ProdutoCodigoBarras.produto_id == produto.id,
            ProdutoCodigoBarras.codigo == codigo_normalizado,
        )
        .first()
    )

    if codigo_produto:
        codigo_produto.principal = True
        codigo_produto.ativo = True
    else:
        db.add(
            ProdutoCodigoBarras(
                empresa_id=empresa_id,
                produto_id=produto.id,
                codigo=codigo_normalizado,
                tipo="PRINCIPAL",
                principal=True,
                ativo=True,
            )
        )

    produto.codigo_barras_principal = codigo_normalizado


def listar_categorias(db: Session, empresa_id: int):
    return (
        db.query(ProdutoCategoria)
        .filter(ProdutoCategoria.empresa_id == empresa_id)
        .order_by(ProdutoCategoria.nome.asc())
        .all()
    )


def criar_categoria(db: Session, empresa_id: int, payload: ProdutoCategoriaCreate):
    categoria = ProdutoCategoria(
        empresa_id=empresa_id,
        nome=payload.nome.strip(),
        descricao=payload.descricao,
        margem_padrao_pct=payload.margem_padrao_pct,
        ativo=payload.ativo,
    )
    db.add(categoria)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Já existe uma categoria com esse nome.")

    db.refresh(categoria)
    return categoria


def atualizar_categoria(
    db: Session,
    empresa_id: int,
    categoria_id: int,
    payload: ProdutoCategoriaUpdate,
):
    categoria = _get_categoria_or_404(db, empresa_id, categoria_id)
    data = payload.model_dump(exclude_unset=True)

    if "nome" in data and data["nome"] is not None:
        categoria.nome = data["nome"].strip()
    if "descricao" in data:
        categoria.descricao = data["descricao"]
    if "margem_padrao_pct" in data:
        categoria.margem_padrao_pct = data["margem_padrao_pct"]
    if "ativo" in data:
        categoria.ativo = data["ativo"]

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Já existe uma categoria com esse nome.")

    db.refresh(categoria)
    return categoria


def listar_produtos(
    db: Session,
    empresa_id: int,
    busca: str | None = None,
    incluir_inativos: bool = False,
):
    query = (
        db.query(Produto)
        .options(joinedload(Produto.codigos_barras))
        .filter(Produto.empresa_id == empresa_id)
    )

    if not incluir_inativos:
        query = query.filter(Produto.ativo.is_(True))

    if busca:
        like = f"%{busca.strip()}%"
        query = query.filter(
            or_(
                Produto.nome.ilike(like),
                Produto.sku.ilike(like),
                Produto.descricao.ilike(like),
                Produto.codigo_barras_principal.ilike(like),
            )
        )

    return query.order_by(Produto.nome.asc()).all()


def criar_produto(db: Session, empresa_id: int, payload: ProdutoCreate):
    if payload.categoria_id:
        _get_categoria_or_404(db, empresa_id, payload.categoria_id)

    produto = Produto(
        empresa_id=empresa_id,
        categoria_id=payload.categoria_id,
        sku=payload.sku.strip(),
        nome=payload.nome.strip(),
        descricao=payload.descricao,
        unidade=payload.unidade.strip(),
        ativo=payload.ativo,
        aceita_fracionado=payload.aceita_fracionado,
        codigo_barras_principal=_normalizar_texto(payload.codigo_barras_principal),
        preco_venda_atual=payload.preco_venda_atual,
        custo_medio_atual=payload.custo_medio_atual,
        estoque_minimo=payload.estoque_minimo,
        ncm=_normalizar_texto(payload.ncm),
        cest=_normalizar_texto(payload.cest),
        cfop_padrao=_normalizar_texto(payload.cfop_padrao),
        origem_fiscal=_normalizar_texto(payload.origem_fiscal),
        cst_icms=_normalizar_texto(payload.cst_icms),
        csosn=_normalizar_texto(payload.csosn),
        cst_pis=_normalizar_texto(payload.cst_pis),
        cst_cofins=_normalizar_texto(payload.cst_cofins),
        aliquota_icms=payload.aliquota_icms,
        aliquota_pis=payload.aliquota_pis,
        aliquota_cofins=payload.aliquota_cofins,
        observacao=payload.observacao,
    )
    db.add(produto)

    try:
        db.flush()
        _sincronizar_codigo_barras_principal(
            db=db,
            empresa_id=empresa_id,
            produto=produto,
            codigo_principal=payload.codigo_barras_principal,
        )
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Já existe um produto com esse SKU ou código de barras principal.",
        )

    db.refresh(produto)
    return _get_produto_or_404(db, empresa_id, produto.id)


def obter_produto(db: Session, empresa_id: int, produto_id: int):
    return _get_produto_or_404(db, empresa_id, produto_id)


def atualizar_produto(
    db: Session,
    empresa_id: int,
    produto_id: int,
    payload: ProdutoUpdate,
):
    produto = _get_produto_or_404(db, empresa_id, produto_id)
    data = payload.model_dump(exclude_unset=True)

    if "categoria_id" in data:
        categoria_id = data["categoria_id"]
        if categoria_id:
            _get_categoria_or_404(db, empresa_id, categoria_id)
        produto.categoria_id = categoria_id

    if "sku" in data and data["sku"] is not None:
        produto.sku = data["sku"].strip()
    if "nome" in data and data["nome"] is not None:
        produto.nome = data["nome"].strip()
    if "descricao" in data:
        produto.descricao = data["descricao"]
    if "unidade" in data and data["unidade"] is not None:
        produto.unidade = data["unidade"].strip()
    if "ativo" in data:
        produto.ativo = data["ativo"]
    if "aceita_fracionado" in data:
        produto.aceita_fracionado = data["aceita_fracionado"]
    if "preco_venda_atual" in data:
        produto.preco_venda_atual = data["preco_venda_atual"]
    if "custo_medio_atual" in data:
        produto.custo_medio_atual = data["custo_medio_atual"]
    if "estoque_minimo" in data:
        produto.estoque_minimo = data["estoque_minimo"]

    if "ncm" in data:
        produto.ncm = _normalizar_texto(data["ncm"])
    if "cest" in data:
        produto.cest = _normalizar_texto(data["cest"])
    if "cfop_padrao" in data:
        produto.cfop_padrao = _normalizar_texto(data["cfop_padrao"])
    if "origem_fiscal" in data:
        produto.origem_fiscal = _normalizar_texto(data["origem_fiscal"])
    if "cst_icms" in data:
        produto.cst_icms = _normalizar_texto(data["cst_icms"])
    if "csosn" in data:
        produto.csosn = _normalizar_texto(data["csosn"])
    if "cst_pis" in data:
        produto.cst_pis = _normalizar_texto(data["cst_pis"])
    if "cst_cofins" in data:
        produto.cst_cofins = _normalizar_texto(data["cst_cofins"])

    if "aliquota_icms" in data:
        produto.aliquota_icms = data["aliquota_icms"]
    if "aliquota_pis" in data:
        produto.aliquota_pis = data["aliquota_pis"]
    if "aliquota_cofins" in data:
        produto.aliquota_cofins = data["aliquota_cofins"]

    if "observacao" in data:
        produto.observacao = data["observacao"]

    try:
        if "codigo_barras_principal" in data:
            _sincronizar_codigo_barras_principal(
                db=db,
                empresa_id=empresa_id,
                produto=produto,
                codigo_principal=data["codigo_barras_principal"],
            )
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Já existe um produto com esse SKU ou código de barras principal.",
        )

    db.refresh(produto)
    return _get_produto_or_404(db, empresa_id, produto.id)


def ativar_produto(
    db: Session,
    empresa_id: int,
    produto_id: int,
):
    produto = _get_produto_or_404(db, empresa_id, produto_id)
    produto.ativo = True
    db.commit()
    db.refresh(produto)
    return _get_produto_or_404(db, empresa_id, produto.id)


def desativar_produto(
    db: Session,
    empresa_id: int,
    produto_id: int,
):
    produto = _get_produto_or_404(db, empresa_id, produto_id)
    produto.ativo = False
    db.commit()
    db.refresh(produto)
    return _get_produto_or_404(db, empresa_id, produto.id)


def criar_codigo_barras(db: Session, empresa_id: int, payload: ProdutoCodigoBarrasCreate):
    produto = _get_produto_or_404(db, empresa_id, payload.produto_id)

    if payload.principal:
        (
            db.query(ProdutoCodigoBarras)
            .filter(
                ProdutoCodigoBarras.empresa_id == empresa_id,
                ProdutoCodigoBarras.produto_id == payload.produto_id,
                ProdutoCodigoBarras.principal.is_(True),
            )
            .update({"principal": False}, synchronize_session=False)
        )

    codigo = ProdutoCodigoBarras(
        empresa_id=empresa_id,
        produto_id=payload.produto_id,
        codigo=payload.codigo.strip(),
        tipo=payload.tipo.strip(),
        principal=payload.principal,
        ativo=payload.ativo,
    )
    db.add(codigo)

    try:
        db.flush()

        if payload.principal:
            produto.codigo_barras_principal = payload.codigo.strip()

        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Código de barras já cadastrado.")

    db.refresh(codigo)
    return codigo


def listar_depositos(db: Session, empresa_id: int):
    return (
        db.query(EstoqueDeposito)
        .filter(EstoqueDeposito.empresa_id == empresa_id)
        .order_by(EstoqueDeposito.padrao.desc(), EstoqueDeposito.nome.asc())
        .all()
    )


def criar_deposito(db: Session, empresa_id: int, payload: EstoqueDepositoCreate):
    total_depositos = (
        db.query(EstoqueDeposito)
        .filter(EstoqueDeposito.empresa_id == empresa_id)
        .count()
    )

    padrao = payload.padrao or total_depositos == 0

    if padrao:
        (
            db.query(EstoqueDeposito)
            .filter(EstoqueDeposito.empresa_id == empresa_id)
            .update({"padrao": False}, synchronize_session=False)
        )

    deposito = EstoqueDeposito(
        empresa_id=empresa_id,
        nome=payload.nome.strip(),
        descricao=payload.descricao,
        padrao=padrao,
        ativo=payload.ativo,
    )
    db.add(deposito)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Já existe um depósito com esse nome.")

    db.refresh(deposito)
    return deposito


def atualizar_deposito(
    db: Session,
    empresa_id: int,
    deposito_id: int,
    payload: EstoqueDepositoUpdate,
):
    deposito = _get_deposito_or_404(db, empresa_id, deposito_id)
    data = payload.model_dump(exclude_unset=True)

    if data.get("padrao") is True:
        (
            db.query(EstoqueDeposito)
            .filter(
                EstoqueDeposito.empresa_id == empresa_id,
                EstoqueDeposito.id != deposito_id,
            )
            .update({"padrao": False}, synchronize_session=False)
        )
        deposito.padrao = True

    if "nome" in data and data["nome"] is not None:
        deposito.nome = data["nome"].strip()
    if "descricao" in data:
        deposito.descricao = data["descricao"]
    if "ativo" in data:
        deposito.ativo = data["ativo"]
    if "padrao" in data and data["padrao"] is False:
        deposito.padrao = False

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Já existe um depósito com esse nome.")

    db.refresh(deposito)
    return deposito


def listar_saldos(
    db: Session,
    empresa_id: int,
    deposito_id: int | None = None,
    produto_id: int | None = None,
):
    query = db.query(EstoqueSaldo).filter(EstoqueSaldo.empresa_id == empresa_id)

    if deposito_id:
        query = query.filter(EstoqueSaldo.deposito_id == deposito_id)
    if produto_id:
        query = query.filter(EstoqueSaldo.produto_id == produto_id)

    return query.order_by(EstoqueSaldo.id.desc()).all()


def listar_movimentos(
    db: Session,
    empresa_id: int,
    deposito_id: int | None = None,
    produto_id: int | None = None,
):
    query = db.query(EstoqueMovimento).filter(EstoqueMovimento.empresa_id == empresa_id)

    if deposito_id:
        query = query.filter(EstoqueMovimento.deposito_id == deposito_id)
    if produto_id:
        query = query.filter(EstoqueMovimento.produto_id == produto_id)

    return query.order_by(EstoqueMovimento.id.desc()).all()


def registrar_entrada_manual(
    db: Session,
    empresa_id: int,
    usuario_id: int | None,
    payload: EstoqueMovimentoEntradaManualIn,
):
    _get_deposito_or_404(db, empresa_id, payload.deposito_id)
    produto = _get_produto_or_404(db, empresa_id, payload.produto_id)
    _validar_produto_ativo_para_movimentacao(produto)

    saldo = _get_or_create_saldo(
        db=db,
        empresa_id=empresa_id,
        deposito_id=payload.deposito_id,
        produto_id=payload.produto_id,
    )

    saldo_antes = Decimal(str(saldo.quantidade_atual))
    quantidade = Decimal(str(payload.quantidade))
    saldo_depois = saldo_antes + quantidade

    saldo.quantidade_atual = saldo_depois

    if payload.custo_unitario is not None:
        produto.custo_medio_atual = payload.custo_unitario

    movimento = EstoqueMovimento(
        empresa_id=empresa_id,
        deposito_id=payload.deposito_id,
        produto_id=payload.produto_id,
        usuario_id=usuario_id,
        tipo_movimento="ENTRADA",
        origem="MANUAL",
        origem_id=None,
        quantidade=quantidade,
        saldo_antes=saldo_antes,
        saldo_depois=saldo_depois,
        custo_unitario=payload.custo_unitario,
        documento_referencia=payload.documento_referencia,
        observacao=payload.observacao,
    )
    db.add(movimento)
    db.commit()
    db.refresh(movimento)
    return movimento


def registrar_saida_manual(
    db: Session,
    empresa_id: int,
    usuario_id: int | None,
    payload: EstoqueMovimentoSaidaManualIn,
):
    _get_deposito_or_404(db, empresa_id, payload.deposito_id)
    produto = _get_produto_or_404(db, empresa_id, payload.produto_id)
    _validar_produto_ativo_para_movimentacao(produto)

    saldo = _get_or_create_saldo(
        db=db,
        empresa_id=empresa_id,
        deposito_id=payload.deposito_id,
        produto_id=payload.produto_id,
    )

    saldo_antes = Decimal(str(saldo.quantidade_atual))
    quantidade = Decimal(str(payload.quantidade))
    saldo_depois = saldo_antes - quantidade

    if saldo_depois < ZERO:
        raise HTTPException(
            status_code=400,
            detail="Saldo insuficiente para saída manual.",
        )

    saldo.quantidade_atual = saldo_depois

    movimento = EstoqueMovimento(
        empresa_id=empresa_id,
        deposito_id=payload.deposito_id,
        produto_id=payload.produto_id,
        usuario_id=usuario_id,
        tipo_movimento="SAIDA",
        origem="MANUAL",
        origem_id=None,
        quantidade=quantidade,
        saldo_antes=saldo_antes,
        saldo_depois=saldo_depois,
        custo_unitario=None,
        documento_referencia=payload.documento_referencia,
        observacao=payload.observacao,
    )
    db.add(movimento)
    db.commit()
    db.refresh(movimento)
    return movimento


def registrar_ajuste_manual(
    db: Session,
    empresa_id: int,
    usuario_id: int | None,
    payload: EstoqueMovimentoAjusteIn,
):
    _get_deposito_or_404(db, empresa_id, payload.deposito_id)
    produto = _get_produto_or_404(db, empresa_id, payload.produto_id)
    _validar_produto_ativo_para_movimentacao(produto)

    saldo = _get_or_create_saldo(
        db=db,
        empresa_id=empresa_id,
        deposito_id=payload.deposito_id,
        produto_id=payload.produto_id,
    )

    saldo_antes = Decimal(str(saldo.quantidade_atual))
    quantidade_ajuste = Decimal(str(payload.quantidade_ajuste))
    saldo_depois = saldo_antes + quantidade_ajuste

    if saldo_depois < ZERO:
        raise HTTPException(
            status_code=400,
            detail="O ajuste não pode deixar o saldo negativo.",
        )

    saldo.quantidade_atual = saldo_depois

    movimento = EstoqueMovimento(
        empresa_id=empresa_id,
        deposito_id=payload.deposito_id,
        produto_id=payload.produto_id,
        usuario_id=usuario_id,
        tipo_movimento="AJUSTE",
        origem="MANUAL",
        origem_id=None,
        quantidade=quantidade_ajuste,
        saldo_antes=saldo_antes,
        saldo_depois=saldo_depois,
        custo_unitario=None,
        documento_referencia=payload.documento_referencia,
        observacao=payload.observacao,
    )
    db.add(movimento)
    db.commit()
    db.refresh(movimento)
    return movimento


def registrar_transferencia(
    db: Session,
    empresa_id: int,
    usuario_id: int | None,
    payload: EstoqueTransferenciaIn,
):
    if payload.deposito_origem_id == payload.deposito_destino_id:
        raise HTTPException(
            status_code=400,
            detail="Depósito de origem e destino não podem ser iguais.",
        )

    _get_deposito_or_404(db, empresa_id, payload.deposito_origem_id)
    _get_deposito_or_404(db, empresa_id, payload.deposito_destino_id)
    produto = _get_produto_or_404(db, empresa_id, payload.produto_id)
    _validar_produto_ativo_para_movimentacao(produto)

    saldo_origem = _get_or_create_saldo(
        db=db,
        empresa_id=empresa_id,
        deposito_id=payload.deposito_origem_id,
        produto_id=payload.produto_id,
    )

    quantidade = Decimal(str(payload.quantidade))
    saldo_origem_antes = Decimal(str(saldo_origem.quantidade_atual))
    saldo_origem_depois = saldo_origem_antes - quantidade

    if saldo_origem_depois < ZERO:
        raise HTTPException(
            status_code=400,
            detail="Saldo insuficiente no depósito de origem.",
        )

    saldo_destino = _get_or_create_saldo(
        db=db,
        empresa_id=empresa_id,
        deposito_id=payload.deposito_destino_id,
        produto_id=payload.produto_id,
    )

    saldo_destino_antes = Decimal(str(saldo_destino.quantidade_atual))
    saldo_destino_depois = saldo_destino_antes + quantidade

    saldo_origem.quantidade_atual = saldo_origem_depois
    saldo_destino.quantidade_atual = saldo_destino_depois

    referencia = payload.documento_referencia
    if not referencia:
        referencia = (
            f"TRANSF-{payload.deposito_origem_id}-"
            f"{payload.deposito_destino_id}-{payload.produto_id}"
        )

    movimento_saida = EstoqueMovimento(
        empresa_id=empresa_id,
        deposito_id=payload.deposito_origem_id,
        produto_id=payload.produto_id,
        usuario_id=usuario_id,
        tipo_movimento="SAIDA",
        origem="TRANSFERENCIA",
        origem_id=None,
        quantidade=quantidade,
        saldo_antes=saldo_origem_antes,
        saldo_depois=saldo_origem_depois,
        custo_unitario=None,
        documento_referencia=referencia,
        observacao=payload.observacao,
    )

    movimento_entrada = EstoqueMovimento(
        empresa_id=empresa_id,
        deposito_id=payload.deposito_destino_id,
        produto_id=payload.produto_id,
        usuario_id=usuario_id,
        tipo_movimento="ENTRADA",
        origem="TRANSFERENCIA",
        origem_id=None,
        quantidade=quantidade,
        saldo_antes=saldo_destino_antes,
        saldo_depois=saldo_destino_depois,
        custo_unitario=None,
        documento_referencia=referencia,
        observacao=payload.observacao,
    )

    db.add(movimento_saida)
    db.add(movimento_entrada)
    db.commit()
    db.refresh(movimento_saida)
    db.refresh(movimento_entrada)

    return {
        "saida": movimento_saida,
        "entrada": movimento_entrada,
        "documento_referencia": referencia,
    }


def registrar_inventario(
    db: Session,
    empresa_id: int,
    usuario_id: int | None,
    payload: EstoqueInventarioIn,
):
    _get_deposito_or_404(db, empresa_id, payload.deposito_id)
    produto = _get_produto_or_404(db, empresa_id, payload.produto_id)
    _validar_produto_ativo_para_movimentacao(produto)

    saldo = _get_or_create_saldo(
        db=db,
        empresa_id=empresa_id,
        deposito_id=payload.deposito_id,
        produto_id=payload.produto_id,
    )

    saldo_antes = Decimal(str(saldo.quantidade_atual))
    quantidade_contada = Decimal(str(payload.quantidade_contada))
    diferenca = quantidade_contada - saldo_antes
    saldo_depois = quantidade_contada

    saldo.quantidade_atual = saldo_depois

    movimento = EstoqueMovimento(
        empresa_id=empresa_id,
        deposito_id=payload.deposito_id,
        produto_id=payload.produto_id,
        usuario_id=usuario_id,
        tipo_movimento="AJUSTE",
        origem="INVENTARIO",
        origem_id=None,
        quantidade=diferenca,
        saldo_antes=saldo_antes,
        saldo_depois=saldo_depois,
        custo_unitario=None,
        documento_referencia=payload.documento_referencia,
        observacao=payload.observacao,
    )
    db.add(movimento)
    db.commit()
    db.refresh(movimento)
    return movimento


def obter_posicao_produto(db: Session, empresa_id: int, produto_id: int):
    produto = _get_produto_or_404(db, empresa_id, produto_id)

    depositos_com_saldo = (
        db.query(EstoqueDeposito, EstoqueSaldo)
        .outerjoin(
            EstoqueSaldo,
            and_(
                EstoqueSaldo.empresa_id == empresa_id,
                EstoqueSaldo.deposito_id == EstoqueDeposito.id,
                EstoqueSaldo.produto_id == produto_id,
            ),
        )
        .filter(EstoqueDeposito.empresa_id == empresa_id)
        .order_by(EstoqueDeposito.nome.asc())
        .all()
    )

    depositos = []
    saldo_total = ZERO

    for deposito, saldo in depositos_com_saldo:
        quantidade = (
            Decimal(str(saldo.quantidade_atual))
            if saldo and saldo.quantidade_atual is not None
            else ZERO
        )
        saldo_total += quantidade
        depositos.append(
            {
                "deposito_id": deposito.id,
                "deposito_nome": deposito.nome,
                "quantidade": quantidade,
            }
        )

    return {
        "produto_id": produto.id,
        "sku": produto.sku,
        "nome": produto.nome,
        "unidade": produto.unidade,
        "saldo_total": saldo_total,
        "depositos": depositos,
    }


def relatorio_posicao_resumida(
    db: Session,
    empresa_id: int,
    busca: str | None = None,
    somente_abaixo_minimo: bool = False,
):
    saldo_total_expr = func.coalesce(func.sum(EstoqueSaldo.quantidade_atual), 0)

    query = (
        db.query(
            Produto.id.label("produto_id"),
            Produto.sku.label("sku"),
            Produto.nome.label("nome"),
            Produto.unidade.label("unidade"),
            Produto.estoque_minimo.label("estoque_minimo"),
            saldo_total_expr.label("saldo_total"),
        )
        .outerjoin(
            EstoqueSaldo,
            and_(
                EstoqueSaldo.empresa_id == empresa_id,
                EstoqueSaldo.produto_id == Produto.id,
            ),
        )
        .filter(
            Produto.empresa_id == empresa_id,
            Produto.ativo.is_(True),
        )
        .group_by(
            Produto.id,
            Produto.sku,
            Produto.nome,
            Produto.unidade,
            Produto.estoque_minimo,
        )
    )

    if busca:
        like = f"%{busca.strip()}%"
        query = query.filter(
            or_(
                Produto.nome.ilike(like),
                Produto.sku.ilike(like),
                Produto.descricao.ilike(like),
                Produto.codigo_barras_principal.ilike(like),
            )
        )

    if somente_abaixo_minimo:
        query = query.having(
            saldo_total_expr < func.coalesce(Produto.estoque_minimo, 0)
        )

    rows = query.order_by(Produto.nome.asc()).all()

    itens = []
    total_abaixo_minimo = 0

    for row in rows:
        estoque_minimo = Decimal(str(row.estoque_minimo or 0))
        saldo_total = Decimal(str(row.saldo_total or 0))
        abaixo_minimo = saldo_total < estoque_minimo

        if abaixo_minimo:
            total_abaixo_minimo += 1

        itens.append(
            {
                "produto_id": row.produto_id,
                "sku": row.sku,
                "nome": row.nome,
                "unidade": row.unidade,
                "estoque_minimo": estoque_minimo,
                "saldo_total": saldo_total,
                "abaixo_minimo": abaixo_minimo,
            }
        )

    return {
        "total_produtos": len(itens),
        "total_abaixo_minimo": total_abaixo_minimo,
        "itens": itens,
    }


def gerar_csv_relatorio_posicao_resumida(
    db: Session,
    empresa_id: int,
    busca: str | None = None,
    somente_abaixo_minimo: bool = False,
) -> str:
    relatorio = relatorio_posicao_resumida(
        db=db,
        empresa_id=empresa_id,
        busca=busca,
        somente_abaixo_minimo=somente_abaixo_minimo,
    )

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    output.write("\ufeff")
    writer.writerow(
        [
            "produto_id",
            "sku",
            "nome",
            "unidade",
            "estoque_minimo",
            "saldo_total",
            "abaixo_minimo",
        ]
    )

    for item in relatorio["itens"]:
        writer.writerow(
            [
                item["produto_id"],
                item["sku"],
                item["nome"],
                item["unidade"],
                str(item["estoque_minimo"]),
                str(item["saldo_total"]),
                "SIM" if item["abaixo_minimo"] else "NAO",
            ]
        )

    return output.getvalue()


def relatorio_posicao_por_deposito(
    db: Session,
    empresa_id: int,
    deposito_id: int,
    busca: str | None = None,
    somente_abaixo_minimo: bool = False,
):
    deposito = _get_deposito_or_404(db, empresa_id, deposito_id)

    quantidade_expr = func.coalesce(EstoqueSaldo.quantidade_atual, 0)

    query = (
        db.query(
            Produto.id.label("produto_id"),
            Produto.sku.label("sku"),
            Produto.nome.label("nome"),
            Produto.unidade.label("unidade"),
            Produto.estoque_minimo.label("estoque_minimo"),
            quantidade_expr.label("quantidade"),
        )
        .outerjoin(
            EstoqueSaldo,
            and_(
                EstoqueSaldo.empresa_id == empresa_id,
                EstoqueSaldo.deposito_id == deposito_id,
                EstoqueSaldo.produto_id == Produto.id,
            ),
        )
        .filter(
            Produto.empresa_id == empresa_id,
            Produto.ativo.is_(True),
        )
    )

    if busca:
        like = f"%{busca.strip()}%"
        query = query.filter(
            or_(
                Produto.nome.ilike(like),
                Produto.sku.ilike(like),
                Produto.descricao.ilike(like),
                Produto.codigo_barras_principal.ilike(like),
            )
        )

    rows = query.order_by(Produto.nome.asc()).all()

    itens = []
    total_abaixo_minimo = 0

    for row in rows:
        estoque_minimo = Decimal(str(row.estoque_minimo or 0))
        quantidade = Decimal(str(row.quantidade or 0))
        abaixo_minimo = quantidade < estoque_minimo

        if somente_abaixo_minimo and not abaixo_minimo:
            continue

        if abaixo_minimo:
            total_abaixo_minimo += 1

        itens.append(
            {
                "produto_id": row.produto_id,
                "sku": row.sku,
                "nome": row.nome,
                "unidade": row.unidade,
                "estoque_minimo": estoque_minimo,
                "quantidade": quantidade,
                "abaixo_minimo": abaixo_minimo,
            }
        )

    return {
        "deposito_id": deposito.id,
        "deposito_nome": deposito.nome,
        "total_produtos": len(itens),
        "total_abaixo_minimo": total_abaixo_minimo,
        "itens": itens,
    }


def gerar_csv_relatorio_posicao_por_deposito(
    db: Session,
    empresa_id: int,
    deposito_id: int,
    busca: str | None = None,
    somente_abaixo_minimo: bool = False,
) -> str:
    relatorio = relatorio_posicao_por_deposito(
        db=db,
        empresa_id=empresa_id,
        deposito_id=deposito_id,
        busca=busca,
        somente_abaixo_minimo=somente_abaixo_minimo,
    )

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    output.write("\ufeff")
    writer.writerow(
        [
            "deposito_id",
            "deposito_nome",
            "produto_id",
            "sku",
            "nome",
            "unidade",
            "estoque_minimo",
            "quantidade",
            "abaixo_minimo",
        ]
    )

    for item in relatorio["itens"]:
        writer.writerow(
            [
                relatorio["deposito_id"],
                relatorio["deposito_nome"],
                item["produto_id"],
                item["sku"],
                item["nome"],
                item["unidade"],
                str(item["estoque_minimo"]),
                str(item["quantidade"]),
                "SIM" if item["abaixo_minimo"] else "NAO",
            ]
        )

    return output.getvalue()