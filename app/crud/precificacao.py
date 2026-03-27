from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.empresa_categoria_precificacao import EmpresaCategoriaPrecificacao
from app.models.empresa_precificacao_config import EmpresaPrecificacaoConfig
from app.models.produto_categoria import ProdutoCategoria
from app.schemas.precificacao import (
    EmpresaCategoriaPrecificacaoUpsertIn,
    EmpresaPrecificacaoConfigUpsertIn,
)


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