from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_usuario_admin_id_atual
from app.models.financeiro_plano_dre import FinanceiroPlanoDRE
from app.schemas.financeiro import (
    FinanceiroPlanoDRECreate,
    FinanceiroPlanoDREListOut,
    FinanceiroPlanoDREOut,
    FinanceiroPlanoDREUpdate,
)

router = APIRouter(prefix="/api/financeiro/dre", tags=["Financeiro - Plano DRE"])


def _serializar(item: FinanceiroPlanoDRE) -> dict:
    return {
        "id": item.id,
        "empresa_id": item.empresa_id,
        "grupo": item.grupo,
        "categoria": item.categoria,
        "subcategoria": item.subcategoria,
        "ordem": item.ordem,
        "ativo": item.ativo,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


def _normalizar_texto(valor: str | None) -> str | None:
    if valor is None:
        return None
    valor = valor.strip()
    return valor or None


@router.get("/", response_model=FinanceiroPlanoDREListOut)
def listar_plano_dre(
    empresa_id: int = Query(..., ge=1),
    ativo: bool | None = Query(None),
    grupo: str | None = Query(None),
    categoria: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(FinanceiroPlanoDRE).filter(FinanceiroPlanoDRE.empresa_id == empresa_id)

    if ativo is not None:
        query = query.filter(FinanceiroPlanoDRE.ativo == ativo)

    if grupo:
        query = query.filter(FinanceiroPlanoDRE.grupo == grupo.strip())

    if categoria:
        query = query.filter(FinanceiroPlanoDRE.categoria == categoria.strip())

    itens = (
        query.order_by(
            FinanceiroPlanoDRE.grupo.asc(),
            FinanceiroPlanoDRE.categoria.asc(),
            FinanceiroPlanoDRE.ordem.asc(),
            FinanceiroPlanoDRE.subcategoria.asc(),
        ).all()
    )

    return {"itens": [_serializar(item) for item in itens]}


@router.get("/opcoes")
def listar_opcoes_dependentes(
    empresa_id: int = Query(..., ge=1),
    grupo: str | None = Query(None),
    categoria: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query = (
        db.query(FinanceiroPlanoDRE)
        .filter(
            FinanceiroPlanoDRE.empresa_id == empresa_id,
            FinanceiroPlanoDRE.ativo.is_(True),
        )
    )

    grupo = _normalizar_texto(grupo)
    categoria = _normalizar_texto(categoria)

    if grupo:
        query = query.filter(FinanceiroPlanoDRE.grupo == grupo)

    if categoria:
        query = query.filter(FinanceiroPlanoDRE.categoria == categoria)

    itens = (
        query.order_by(
            FinanceiroPlanoDRE.grupo.asc(),
            FinanceiroPlanoDRE.categoria.asc(),
            FinanceiroPlanoDRE.ordem.asc(),
            FinanceiroPlanoDRE.subcategoria.asc(),
        ).all()
    )

    grupos = sorted({item.grupo for item in itens if item.grupo})
    categorias = sorted({item.categoria for item in itens if item.categoria})
    subcategorias = [
        {
            "id": item.id,
            "grupo": item.grupo,
            "categoria": item.categoria,
            "subcategoria": item.subcategoria,
            "ordem": item.ordem,
        }
        for item in itens
    ]

    return {
        "grupos": grupos,
        "categorias": categorias,
        "subcategorias": subcategorias,
    }


@router.post(
    "/",
    response_model=FinanceiroPlanoDREOut,
    status_code=status.HTTP_201_CREATED,
)
def criar_item_plano_dre(
    payload: FinanceiroPlanoDRECreate,
    db: Session = Depends(get_db),
    _admin_id: int = Depends(get_usuario_admin_id_atual),
):
    grupo = _normalizar_texto(payload.grupo)
    categoria = _normalizar_texto(payload.categoria)
    subcategoria = _normalizar_texto(payload.subcategoria)

    existente = (
        db.query(FinanceiroPlanoDRE)
        .filter(
            FinanceiroPlanoDRE.empresa_id == payload.empresa_id,
            FinanceiroPlanoDRE.grupo == grupo,
            FinanceiroPlanoDRE.categoria == categoria,
            FinanceiroPlanoDRE.subcategoria == subcategoria,
        )
        .first()
    )

    if existente:
        raise HTTPException(status_code=400, detail="Essa classificação DRE já existe para a empresa.")

    item = FinanceiroPlanoDRE(
        empresa_id=payload.empresa_id,
        grupo=grupo,
        categoria=categoria,
        subcategoria=subcategoria,
        ordem=payload.ordem,
        ativo=payload.ativo,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return _serializar(item)


@router.put("/{item_id}", response_model=FinanceiroPlanoDREOut)
def atualizar_item_plano_dre(
    item_id: int,
    payload: FinanceiroPlanoDREUpdate,
    db: Session = Depends(get_db),
    _admin_id: int = Depends(get_usuario_admin_id_atual),
):
    item = db.query(FinanceiroPlanoDRE).filter(FinanceiroPlanoDRE.id == item_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Classificação DRE não encontrada.")

    novo_grupo = _normalizar_texto(payload.grupo) if payload.grupo is not None else item.grupo
    nova_categoria = (
        _normalizar_texto(payload.categoria) if payload.categoria is not None else item.categoria
    )
    nova_subcategoria = (
        _normalizar_texto(payload.subcategoria)
        if payload.subcategoria is not None
        else item.subcategoria
    )

    conflito = (
        db.query(FinanceiroPlanoDRE)
        .filter(
            FinanceiroPlanoDRE.id != item.id,
            FinanceiroPlanoDRE.empresa_id == item.empresa_id,
            FinanceiroPlanoDRE.grupo == novo_grupo,
            FinanceiroPlanoDRE.categoria == nova_categoria,
            FinanceiroPlanoDRE.subcategoria == nova_subcategoria,
        )
        .first()
    )

    if conflito:
        raise HTTPException(status_code=400, detail="Já existe outra classificação DRE com esses dados.")

    item.grupo = novo_grupo
    item.categoria = nova_categoria
    item.subcategoria = nova_subcategoria

    if payload.ordem is not None:
        item.ordem = payload.ordem

    if payload.ativo is not None:
        item.ativo = payload.ativo

    db.commit()
    db.refresh(item)

    return _serializar(item)