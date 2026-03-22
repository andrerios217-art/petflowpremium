from decimal import Decimal
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.estoque_deposito import EstoqueDeposito
from app.models.estoque_movimento import EstoqueMovimento
from app.models.estoque_saldo import EstoqueSaldo
from app.models.produto import Produto
from app.models.produto_categoria import ProdutoCategoria
from app.models.produto_codigo_barras import ProdutoCodigoBarras
from app.schemas.estoque import (
    EstoqueDepositoCreate,
    EstoqueDepositoUpdate,
    EstoqueMovimentoAjusteIn,
    EstoqueMovimentoEntradaManualIn,
    ProdutoCategoriaCreate,
    ProdutoCategoriaUpdate,
    ProdutoCodigoBarrasCreate,
    ProdutoCreate,
    ProdutoUpdate,
)


def _to_decimal(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _validar_empresa_id(empresa_id: Optional[int]) -> int:
    if not empresa_id:
        raise HTTPException(status_code=400, detail="empresa_id é obrigatório")
    return empresa_id


def obter_produto_or_404(db: Session, empresa_id: int, produto_id: int) -> Produto:
    produto = (
        db.query(Produto)
        .filter(Produto.id == produto_id, Produto.empresa_id == empresa_id)
        .first()
    )
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto


def obter_categoria_or_404(db: Session, empresa_id: int, categoria_id: int) -> ProdutoCategoria:
    categoria = (
        db.query(ProdutoCategoria)
        .filter(ProdutoCategoria.id == categoria_id, ProdutoCategoria.empresa_id == empresa_id)
        .first()
    )
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return categoria


def obter_deposito_or_404(db: Session, empresa_id: int, deposito_id: int) -> EstoqueDeposito:
    deposito = (
        db.query(EstoqueDeposito)
        .filter(EstoqueDeposito.id == deposito_id, EstoqueDeposito.empresa_id == empresa_id)
        .first()
    )
    if not deposito:
        raise HTTPException(status_code=404, detail="Depósito não encontrado")
    return deposito


def obter_ou_criar_deposito_padrao(db: Session, empresa_id: int) -> EstoqueDeposito:
    deposito = (
        db.query(EstoqueDeposito)
        .filter(
            EstoqueDeposito.empresa_id == empresa_id,
            EstoqueDeposito.padrao.is_(True),
        )
        .first()
    )
    if deposito:
        return deposito

    deposito = EstoqueDeposito(
        empresa_id=empresa_id,
        nome="DEPÓSITO PADRÃO",
        descricao="Criado automaticamente pelo sistema",
        padrao=True,
        ativo=True,
    )
    db.add(deposito)
    db.flush()
    return deposito


def listar_categorias(db: Session, empresa_id: int):
    return (
        db.query(ProdutoCategoria)
        .filter(ProdutoCategoria.empresa_id == empresa_id)
        .order_by(ProdutoCategoria.nome.asc())
        .all()
    )


def criar_categoria(db: Session, empresa_id: int, payload: ProdutoCategoriaCreate):
    _validar_empresa_id(empresa_id)

    existente = (
        db.query(ProdutoCategoria)
        .filter(
            ProdutoCategoria.empresa_id == empresa_id,
            ProdutoCategoria.nome == payload.nome.strip(),
        )
        .first()
    )
    if existente:
        raise HTTPException(status_code=400, detail="Já existe categoria com esse nome")

    categoria = ProdutoCategoria(
        empresa_id=empresa_id,
        nome=payload.nome.strip(),
        descricao=payload.descricao,
        margem_padrao_pct=payload.margem_padrao_pct,
        ativo=payload.ativo,
    )
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


def atualizar_categoria(db: Session, empresa_id: int, categoria_id: int, payload: ProdutoCategoriaUpdate):
    categoria = obter_categoria_or_404(db, empresa_id, categoria_id)

    if payload.nome is not None:
        nome = payload.nome.strip()
        existente = (
            db.query(ProdutoCategoria)
            .filter(
                ProdutoCategoria.empresa_id == empresa_id,
                ProdutoCategoria.nome == nome,
                ProdutoCategoria.id != categoria_id,
            )
            .first()
        )
        if existente:
            raise HTTPException(status_code=400, detail="Já existe categoria com esse nome")
        categoria.nome = nome

    if payload.descricao is not None:
        categoria.descricao = payload.descricao
    if payload.margem_padrao_pct is not None:
        categoria.margem_padrao_pct = payload.margem_padrao_pct
    if payload.ativo is not None:
        categoria.ativo = payload.ativo

    db.commit()
    db.refresh(categoria)
    return categoria


def listar_produtos(db: Session, empresa_id: int, busca: Optional[str] = None):
    query = db.query(Produto).filter(Produto.empresa_id == empresa_id)

    if busca:
        termo = f"%{busca.strip()}%"
        query = query.filter(
            (Produto.nome.ilike(termo)) |
            (Produto.sku.ilike(termo))
        )

    return query.order_by(Produto.nome.asc()).all()


def criar_produto(db: Session, empresa_id: int, payload: ProdutoCreate):
    _validar_empresa_id(empresa_id)

    if payload.categoria_id is not None:
        obter_categoria_or_404(db, empresa_id, payload.categoria_id)

    existente = (
        db.query(Produto)
        .filter(Produto.empresa_id == empresa_id, Produto.sku == payload.sku.strip())
        .first()
    )
    if existente:
        raise HTTPException(status_code=400, detail="Já existe produto com esse SKU")

    produto = Produto(
        empresa_id=empresa_id,
        categoria_id=payload.categoria_id,
        sku=payload.sku.strip(),
        nome=payload.nome.strip(),
        descricao=payload.descricao,
        unidade=payload.unidade.strip().upper(),
        ativo=payload.ativo,
        aceita_fracionado=payload.aceita_fracionado,
        preco_venda_atual=payload.preco_venda_atual,
        estoque_minimo=payload.estoque_minimo,
        observacao=payload.observacao,
    )
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


def obter_produto(db: Session, empresa_id: int, produto_id: int):
    return obter_produto_or_404(db, empresa_id, produto_id)


def atualizar_produto(db: Session, empresa_id: int, produto_id: int, payload: ProdutoUpdate):
    produto = obter_produto_or_404(db, empresa_id, produto_id)

    if payload.categoria_id is not None:
        obter_categoria_or_404(db, empresa_id, payload.categoria_id)
        produto.categoria_id = payload.categoria_id

    if payload.sku is not None:
        sku = payload.sku.strip()
        existente = (
            db.query(Produto)
            .filter(
                Produto.empresa_id == empresa_id,
                Produto.sku == sku,
                Produto.id != produto_id,
            )
            .first()
        )
        if existente:
            raise HTTPException(status_code=400, detail="Já existe produto com esse SKU")
        produto.sku = sku

    if payload.nome is not None:
        produto.nome = payload.nome.strip()
    if payload.descricao is not None:
        produto.descricao = payload.descricao
    if payload.unidade is not None:
        produto.unidade = payload.unidade.strip().upper()
    if payload.ativo is not None:
        produto.ativo = payload.ativo
    if payload.aceita_fracionado is not None:
        produto.aceita_fracionado = payload.aceita_fracionado
    if payload.preco_venda_atual is not None:
        produto.preco_venda_atual = payload.preco_venda_atual
    if payload.estoque_minimo is not None:
        produto.estoque_minimo = payload.estoque_minimo
    if payload.observacao is not None:
        produto.observacao = payload.observacao

    db.commit()
    db.refresh(produto)
    return produto


def criar_codigo_barras(db: Session, empresa_id: int, payload: ProdutoCodigoBarrasCreate):
    produto = obter_produto_or_404(db, empresa_id, payload.produto_id)

    existente = (
        db.query(ProdutoCodigoBarras)
        .filter(
            ProdutoCodigoBarras.empresa_id == empresa_id,
            ProdutoCodigoBarras.codigo == payload.codigo.strip(),
        )
        .first()
    )
    if existente:
        raise HTTPException(status_code=400, detail="Código de barras já cadastrado")

    if payload.principal:
        (
            db.query(ProdutoCodigoBarras)
            .filter(
                ProdutoCodigoBarras.empresa_id == empresa_id,
                ProdutoCodigoBarras.produto_id == produto.id,
                ProdutoCodigoBarras.principal.is_(True),
            )
            .update({"principal": False}, synchronize_session=False)
        )

    codigo = ProdutoCodigoBarras(
        empresa_id=empresa_id,
        produto_id=produto.id,
        codigo=payload.codigo.strip(),
        tipo=payload.tipo.strip().upper(),
        principal=payload.principal,
        ativo=payload.ativo,
    )
    db.add(codigo)
    db.commit()
    db.refresh(codigo)
    return codigo


def listar_depositos(db: Session, empresa_id: int):
    return (
        db.query(EstoqueDeposito)
        .filter(EstoqueDeposito.empresa_id == empresa_id)
        .order_by(EstoqueDeposito.nome.asc())
        .all()
    )


def criar_deposito(db: Session, empresa_id: int, payload: EstoqueDepositoCreate):
    existente = (
        db.query(EstoqueDeposito)
        .filter(
            EstoqueDeposito.empresa_id == empresa_id,
            EstoqueDeposito.nome == payload.nome.strip(),
        )
        .first()
    )
    if existente:
        raise HTTPException(status_code=400, detail="Já existe depósito com esse nome")

    if payload.padrao:
        (
            db.query(EstoqueDeposito)
            .filter(EstoqueDeposito.empresa_id == empresa_id, EstoqueDeposito.padrao.is_(True))
            .update({"padrao": False}, synchronize_session=False)
        )

    deposito = EstoqueDeposito(
        empresa_id=empresa_id,
        nome=payload.nome.strip(),
        descricao=payload.descricao,
        padrao=payload.padrao,
        ativo=payload.ativo,
    )
    db.add(deposito)
    db.commit()
    db.refresh(deposito)
    return deposito


def atualizar_deposito(db: Session, empresa_id: int, deposito_id: int, payload: EstoqueDepositoUpdate):
    deposito = obter_deposito_or_404(db, empresa_id, deposito_id)

    if payload.nome is not None:
        nome = payload.nome.strip()
        existente = (
            db.query(EstoqueDeposito)
            .filter(
                EstoqueDeposito.empresa_id == empresa_id,
                EstoqueDeposito.nome == nome,
                EstoqueDeposito.id != deposito_id,
            )
            .first()
        )
        if existente:
            raise HTTPException(status_code=400, detail="Já existe depósito com esse nome")
        deposito.nome = nome

    if payload.descricao is not None:
        deposito.descricao = payload.descricao

    if payload.padrao is not None and payload.padrao:
        (
            db.query(EstoqueDeposito)
            .filter(
                EstoqueDeposito.empresa_id == empresa_id,
                EstoqueDeposito.id != deposito_id,
                EstoqueDeposito.padrao.is_(True),
            )
            .update({"padrao": False}, synchronize_session=False)
        )
        deposito.padrao = True

    if payload.ativo is not None:
        deposito.ativo = payload.ativo

    db.commit()
    db.refresh(deposito)
    return deposito


def listar_saldos(db: Session, empresa_id: int, deposito_id: Optional[int] = None, produto_id: Optional[int] = None):
    query = db.query(EstoqueSaldo).filter(EstoqueSaldo.empresa_id == empresa_id)

    if deposito_id is not None:
        query = query.filter(EstoqueSaldo.deposito_id == deposito_id)

    if produto_id is not None:
        query = query.filter(EstoqueSaldo.produto_id == produto_id)

    return query.order_by(EstoqueSaldo.id.desc()).all()


def listar_movimentos(
    db: Session,
    empresa_id: int,
    deposito_id: Optional[int] = None,
    produto_id: Optional[int] = None,
):
    query = db.query(EstoqueMovimento).filter(EstoqueMovimento.empresa_id == empresa_id)

    if deposito_id is not None:
        query = query.filter(EstoqueMovimento.deposito_id == deposito_id)

    if produto_id is not None:
        query = query.filter(EstoqueMovimento.produto_id == produto_id)

    return query.order_by(EstoqueMovimento.id.desc()).all()


def _obter_ou_criar_saldo_com_lock(
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
        .with_for_update()
        .first()
    )

    if saldo:
        return saldo

    saldo = EstoqueSaldo(
        empresa_id=empresa_id,
        deposito_id=deposito_id,
        produto_id=produto_id,
        quantidade_atual=Decimal("0"),
    )
    db.add(saldo)
    db.flush()

    saldo = (
        db.query(EstoqueSaldo)
        .filter(
            EstoqueSaldo.empresa_id == empresa_id,
            EstoqueSaldo.deposito_id == deposito_id,
            EstoqueSaldo.produto_id == produto_id,
        )
        .with_for_update()
        .first()
    )
    return saldo


def registrar_entrada_manual(
    db: Session,
    empresa_id: int,
    usuario_id: Optional[int],
    payload: EstoqueMovimentoEntradaManualIn,
):
    produto = obter_produto_or_404(db, empresa_id, payload.produto_id)

    deposito = (
        obter_deposito_or_404(db, empresa_id, payload.deposito_id)
        if payload.deposito_id
        else obter_ou_criar_deposito_padrao(db, empresa_id)
    )

    saldo = _obter_ou_criar_saldo_com_lock(db, empresa_id, deposito.id, produto.id)

    saldo_antes = _to_decimal(saldo.quantidade_atual)
    quantidade = _to_decimal(payload.quantidade)
    saldo_depois = saldo_antes + quantidade

    saldo.quantidade_atual = saldo_depois

    movimento = EstoqueMovimento(
        empresa_id=empresa_id,
        deposito_id=deposito.id,
        produto_id=produto.id,
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


def registrar_ajuste_manual(
    db: Session,
    empresa_id: int,
    usuario_id: Optional[int],
    payload: EstoqueMovimentoAjusteIn,
):
    produto = obter_produto_or_404(db, empresa_id, payload.produto_id)

    deposito = (
        obter_deposito_or_404(db, empresa_id, payload.deposito_id)
        if payload.deposito_id
        else obter_ou_criar_deposito_padrao(db, empresa_id)
    )

    saldo = _obter_ou_criar_saldo_com_lock(db, empresa_id, deposito.id, produto.id)

    saldo_antes = _to_decimal(saldo.quantidade_atual)
    quantidade = _to_decimal(payload.quantidade)

    if payload.tipo_movimento == "ENTRADA":
        saldo_depois = saldo_antes + quantidade
    else:
        saldo_depois = saldo_antes - quantidade
        if saldo_depois < 0:
            raise HTTPException(status_code=400, detail="Saldo insuficiente para ajuste de saída")

    saldo.quantidade_atual = saldo_depois

    movimento = EstoqueMovimento(
        empresa_id=empresa_id,
        deposito_id=deposito.id,
        produto_id=produto.id,
        usuario_id=usuario_id,
        tipo_movimento="AJUSTE",
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