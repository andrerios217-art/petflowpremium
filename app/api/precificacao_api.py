from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_empresa_id_atual
from app.crud import estoque as estoque_crud
from app.crud import precificacao as precificacao_crud
from app.schemas.estoque import ProdutoCategoriaOut
from app.schemas.precificacao import (
    EmpresaCategoriaPrecificacaoOut,
    EmpresaCategoriaPrecificacaoUpsertIn,
    EmpresaPrecificacaoConfigOut,
    EmpresaPrecificacaoConfigUpsertIn,
    PrecificacaoConfigTelaOut,
    ReprecificacaoLoteIn,
    ReprecificacaoLoteOut,
)

router = APIRouter(prefix="/api/precificacao", tags=["Precificação"])


@router.get("/config", response_model=PrecificacaoConfigTelaOut)
def obter_configuracao_precificacao(
    empresa_id: int = Depends(get_empresa_id_atual),
    db: Session = Depends(get_db),
):
    config = precificacao_crud.obter_config_padrao(db, empresa_id)
    regras = precificacao_crud.listar_regras_categoria(db, empresa_id)
    return {
        "config_padrao": config,
        "regras_categoria": regras,
    }


@router.put("/config/padrao", response_model=EmpresaPrecificacaoConfigOut)
def salvar_configuracao_padrao(
    payload: EmpresaPrecificacaoConfigUpsertIn,
    empresa_id: int = Depends(get_empresa_id_atual),
    db: Session = Depends(get_db),
):
    return precificacao_crud.salvar_config_padrao(db, empresa_id, payload)


@router.get("/categorias", response_model=list[ProdutoCategoriaOut])
def listar_categorias_precificacao(
    empresa_id: int = Depends(get_empresa_id_atual),
    db: Session = Depends(get_db),
):
    return estoque_crud.listar_categorias(db, empresa_id)


@router.put("/categorias", response_model=EmpresaCategoriaPrecificacaoOut)
def salvar_regra_categoria(
    payload: EmpresaCategoriaPrecificacaoUpsertIn,
    empresa_id: int = Depends(get_empresa_id_atual),
    db: Session = Depends(get_db),
):
    return precificacao_crud.salvar_regra_categoria(db, empresa_id, payload)


@router.delete("/categorias/{categoria_id}")
def excluir_regra_categoria(
    categoria_id: int,
    empresa_id: int = Depends(get_empresa_id_atual),
    db: Session = Depends(get_db),
):
    precificacao_crud.excluir_regra_categoria(db, empresa_id, categoria_id)
    return {"ok": True}


@router.post("/reprecificar/simular", response_model=ReprecificacaoLoteOut)
def simular_reprecificacao(
    payload: ReprecificacaoLoteIn,
    empresa_id: int = Depends(get_empresa_id_atual),
    db: Session = Depends(get_db),
):
    return precificacao_crud.simular_reprecificacao_lote(db, empresa_id, payload)


@router.post("/reprecificar/aplicar", response_model=ReprecificacaoLoteOut)
def aplicar_reprecificacao(
    payload: ReprecificacaoLoteIn,
    empresa_id: int = Depends(get_empresa_id_atual),
    db: Session = Depends(get_db),
):
    return precificacao_crud.aplicar_reprecificacao_lote(db, empresa_id, payload)