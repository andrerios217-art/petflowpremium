from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.empresa_categoria_precificacao import EmpresaCategoriaPrecificacao
from app.models.empresa_precificacao_config import EmpresaPrecificacaoConfig
from app.models.produto import Produto
from app.models.produto_categoria import ProdutoCategoria
from app.schemas.precificacao import (
    EmpresaCategoriaPrecificacaoUpsertIn,
    EmpresaPrecificacaoConfigUpsertIn,
    ReprecificacaoLoteIn,
    ReprecificacaoLoteOut,
    ReprecificacaoProdutoPreviewOut,
)
from app.services.precificacao import (
    RegraPrecificacaoAplicada,
    calcular_preco_venda_por_regra,
    obter_regra_precificacao,
)

ZERO = Decimal("0.00")


def obter_config_padrao(db: Session, empresa_id: int) -> EmpresaPrecificacaoConfig | None:
    return (
        db.query(EmpresaPrecificacaoConfig)
        .filter(EmpresaPrecificacaoConfig.empresa_id == empresa_id)
        .first()
    )


def salvar_config_padrao(
    db: Session,
    empresa_id: int,
    payload: EmpresaPrecificacaoConfigUpsertIn,
) -> EmpresaPrecificacaoConfig:
    config = obter_config_padrao(db, empresa_id)

    if config is None:
        config = EmpresaPrecificacaoConfig(empresa_id=empresa_id)
        db.add(config)

    config.modo_padrao = payload.modo_padrao
    config.percentual_padrao = payload.percentual_padrao
    config.ativo = payload.ativo

    db.commit()
    db.refresh(config)
    return config


def listar_regras_categoria(db: Session, empresa_id: int) -> list[EmpresaCategoriaPrecificacao]:
    regras = (
        db.query(EmpresaCategoriaPrecificacao)
        .filter(EmpresaCategoriaPrecificacao.empresa_id == empresa_id)
        .all()
    )

    for regra in regras:
        categoria = (
            db.query(ProdutoCategoria)
            .filter(
                ProdutoCategoria.id == regra.categoria_id,
                ProdutoCategoria.empresa_id == empresa_id,
            )
            .first()
        )
        regra.categoria_nome = categoria.nome if categoria else None

    regras.sort(key=lambda x: (x.categoria_nome or "").lower())
    return regras


def salvar_regra_categoria(
    db: Session,
    empresa_id: int,
    payload: EmpresaCategoriaPrecificacaoUpsertIn,
) -> EmpresaCategoriaPrecificacao:
    categoria = (
        db.query(ProdutoCategoria)
        .filter(
            ProdutoCategoria.id == payload.categoria_id,
            ProdutoCategoria.empresa_id == empresa_id,
        )
        .first()
    )

    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")

    regra = (
        db.query(EmpresaCategoriaPrecificacao)
        .filter(
            EmpresaCategoriaPrecificacao.empresa_id == empresa_id,
            EmpresaCategoriaPrecificacao.categoria_id == payload.categoria_id,
        )
        .first()
    )

    if regra is None:
        regra = EmpresaCategoriaPrecificacao(
            empresa_id=empresa_id,
            categoria_id=payload.categoria_id,
        )
        db.add(regra)

    regra.modo = payload.modo
    regra.percentual = payload.percentual
    regra.ativo = payload.ativo

    db.commit()
    db.refresh(regra)
    regra.categoria_nome = categoria.nome
    return regra


def excluir_regra_categoria(
    db: Session,
    empresa_id: int,
    categoria_id: int,
) -> None:
    regra = (
        db.query(EmpresaCategoriaPrecificacao)
        .filter(
            EmpresaCategoriaPrecificacao.empresa_id == empresa_id,
            EmpresaCategoriaPrecificacao.categoria_id == categoria_id,
        )
        .first()
    )

    if not regra:
        raise HTTPException(status_code=404, detail="Regra da categoria não encontrada.")

    db.delete(regra)
    db.commit()


def _decimal(valor) -> Decimal:
    if valor is None:
        return ZERO
    return Decimal(str(valor))


def _obter_categoria_map(db: Session, empresa_id: int) -> dict[int, str]:
    categorias = (
        db.query(ProdutoCategoria)
        .filter(ProdutoCategoria.empresa_id == empresa_id)
        .all()
    )
    return {categoria.id: categoria.nome for categoria in categorias}


def _validar_categoria_filtro(
    db: Session,
    empresa_id: int,
    categoria_id: int | None,
) -> None:
    if not categoria_id:
        return

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


def _buscar_produtos_reprecificacao(
    db: Session,
    empresa_id: int,
    payload: ReprecificacaoLoteIn,
) -> list[Produto]:
    query = db.query(Produto).filter(Produto.empresa_id == empresa_id)

    if payload.categoria_id:
        query = query.filter(Produto.categoria_id == payload.categoria_id)

    if payload.somente_ativos:
        query = query.filter(Produto.ativo.is_(True))

    if payload.somente_sem_preco:
        query = query.filter(Produto.preco_venda_atual <= ZERO)

    return (
        query.order_by(Produto.id.desc())
        .limit(payload.limitar)
        .all()
    )


def _montar_preview_reprecificacao(
    produto: Produto,
    categoria_nome: str | None,
    regra: RegraPrecificacaoAplicada,
    preco_sugerido: Decimal,
) -> ReprecificacaoProdutoPreviewOut:
    return ReprecificacaoProdutoPreviewOut(
        produto_id=produto.id,
        sku=produto.sku,
        nome=produto.nome,
        categoria_id=produto.categoria_id,
        categoria_nome=categoria_nome,
        custo_medio_atual=_decimal(produto.custo_medio_atual),
        preco_venda_atual=_decimal(produto.preco_venda_atual),
        preco_sugerido=preco_sugerido,
        regra_origem=regra.origem,
        regra_modo=regra.modo,
        regra_percentual=regra.percentual,
    )


def _coletar_reprecificacao(
    db: Session,
    empresa_id: int,
    payload: ReprecificacaoLoteIn,
) -> tuple[list[Produto], list[ReprecificacaoProdutoPreviewOut], set[int]]:
    _validar_categoria_filtro(db, empresa_id, payload.categoria_id)

    categoria_map = _obter_categoria_map(db, empresa_id)
    produtos = _buscar_produtos_reprecificacao(db, empresa_id, payload)

    itens: list[ReprecificacaoProdutoPreviewOut] = []
    produto_ids_atualizaveis: set[int] = set()

    for produto in produtos:
        custo_medio = _decimal(produto.custo_medio_atual)
        if custo_medio <= ZERO:
            continue

        try:
            regra = obter_regra_precificacao(
                db=db,
                empresa_id=empresa_id,
                categoria_id=produto.categoria_id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        if not regra:
            continue

        try:
            preco_sugerido = calcular_preco_venda_por_regra(
                custo=custo_medio,
                modo=regra.modo,
                percentual=regra.percentual,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        item = _montar_preview_reprecificacao(
            produto=produto,
            categoria_nome=categoria_map.get(produto.categoria_id) if produto.categoria_id else None,
            regra=regra,
            preco_sugerido=preco_sugerido,
        )
        itens.append(item)

        if item.preco_sugerido != item.preco_venda_atual:
            produto_ids_atualizaveis.add(produto.id)

    return produtos, itens, produto_ids_atualizaveis


def simular_reprecificacao_lote(
    db: Session,
    empresa_id: int,
    payload: ReprecificacaoLoteIn,
) -> ReprecificacaoLoteOut:
    produtos, itens, produto_ids_atualizaveis = _coletar_reprecificacao(
        db=db,
        empresa_id=empresa_id,
        payload=payload,
    )

    return ReprecificacaoLoteOut(
        total_analisado=len(produtos),
        total_elegiveis=len(itens),
        total_atualizados=len(produto_ids_atualizaveis),
        itens=itens,
    )


def aplicar_reprecificacao_lote(
    db: Session,
    empresa_id: int,
    payload: ReprecificacaoLoteIn,
) -> ReprecificacaoLoteOut:
    produtos, itens, produto_ids_atualizaveis = _coletar_reprecificacao(
        db=db,
        empresa_id=empresa_id,
        payload=payload,
    )

    itens_por_produto_id = {item.produto_id: item for item in itens}
    total_atualizados = 0

    for produto in produtos:
        if produto.id not in produto_ids_atualizaveis:
            continue

        item = itens_por_produto_id.get(produto.id)
        if item is None:
            continue

        produto.preco_venda_atual = item.preco_sugerido
        total_atualizados += 1

    if total_atualizados > 0:
        db.commit()

    return ReprecificacaoLoteOut(
        total_analisado=len(produtos),
        total_elegiveis=len(itens),
        total_atualizados=total_atualizados,
        itens=itens,
    )