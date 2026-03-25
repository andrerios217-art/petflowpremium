from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_empresa_id_atual
from app.crud import nota_entrada as nota_entrada_crud
from app.schemas.nota_entrada import (
    NotaEntradaItemVincularIn,
    NotaEntradaOut,
    NotaEntradaResumoOut,
    ProdutoBuscaOut,
)


router = APIRouter(prefix="/api/notas-entrada", tags=["Notas de Entrada"])


@router.post("/importar-xml", response_model=NotaEntradaOut)
async def importar_xml_nota_entrada(
    arquivo: UploadFile = File(...),
    empresa_id: int = Depends(get_empresa_id_atual),
    db: Session = Depends(get_db),
):
    conteudo = await arquivo.read()
    xml_content = conteudo.decode("utf-8-sig", errors="ignore")
    return nota_entrada_crud.importar_xml_nota_entrada(
        db=db,
        empresa_id=empresa_id,
        xml_content=xml_content,
    )


@router.get("", response_model=list[NotaEntradaResumoOut])
def listar_notas_entrada(
    empresa_id: int = Depends(get_empresa_id_atual),
    db: Session = Depends(get_db),
):
    return nota_entrada_crud.listar_notas_entrada(db, empresa_id)


@router.get("/produtos/busca", response_model=list[ProdutoBuscaOut])
def buscar_produtos_para_vinculo(
    q: str = Query(..., min_length=2),
    incluir_inativos: bool = Query(True),
    limite: int = Query(20, ge=1, le=50),
    empresa_id: int = Depends(get_empresa_id_atual),
    db: Session = Depends(get_db),
):
    return nota_entrada_crud.buscar_produtos_para_vinculo(
        db=db,
        empresa_id=empresa_id,
        termo=q,
        incluir_inativos=incluir_inativos,
        limite=limite,
    )


@router.get("/{nota_entrada_id}", response_model=NotaEntradaOut)
def obter_nota_entrada(
    nota_entrada_id: int,
    empresa_id: int = Depends(get_empresa_id_atual),
    db: Session = Depends(get_db),
):
    return nota_entrada_crud.obter_nota_entrada(db, empresa_id, nota_entrada_id)


@router.post("/{nota_entrada_id}/vincular-item", response_model=NotaEntradaOut)
def vincular_item_nota_entrada(
    nota_entrada_id: int,
    payload: NotaEntradaItemVincularIn,
    empresa_id: int = Depends(get_empresa_id_atual),
    db: Session = Depends(get_db),
):
    return nota_entrada_crud.vincular_item_nota_entrada(
        db=db,
        empresa_id=empresa_id,
        nota_entrada_id=nota_entrada_id,
        item_id=payload.item_id,
        produto_id=payload.produto_id,
        salvar_vinculo_fornecedor=payload.salvar_vinculo_fornecedor,
    )