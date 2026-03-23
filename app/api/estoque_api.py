from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import estoque as estoque_crud
from app.schemas.estoque import (
    EstoqueDepositoCreate,
    EstoqueDepositoOut,
    EstoqueDepositoUpdate,
    EstoqueInventarioIn,
    EstoqueMovimentoAjusteIn,
    EstoqueMovimentoEntradaManualIn,
    EstoqueMovimentoOut,
    EstoqueMovimentoSaidaManualIn,
    EstoquePosicaoProdutoOut,
    EstoqueRelatorioDepositoOut,
    EstoqueRelatorioPosicaoOut,
    EstoqueSaldoOut,
    EstoqueTransferenciaIn,
    ProdutoCategoriaCreate,
    ProdutoCategoriaOut,
    ProdutoCategoriaUpdate,
    ProdutoCodigoBarrasCreate,
    ProdutoCodigoBarrasOut,
    ProdutoCreate,
    ProdutoOut,
    ProdutoUpdate,
)

router = APIRouter(prefix="/api/estoque", tags=["Estoque"])


def _empresa_id_header(x_empresa_id: Optional[int]) -> int:
    if not x_empresa_id:
        raise HTTPException(status_code=400, detail="X-Empresa-Id é obrigatório.")
    return x_empresa_id


@router.get("/categorias", response_model=list[ProdutoCategoriaOut])
def listar_categorias(
    x_empresa_id: Optional[int] = Header(default=None, alias="X-Empresa-Id"),
    db: Session = Depends(get_db),
):
    empresa_id = _empresa_id_header(x_empresa_id)
    return estoque_crud.listar_categorias(db, empresa_id)


@router.post("/categorias", response_model=ProdutoCategoriaOut)
def criar_categoria(
    payload: ProdutoCategoriaCreate,
    x_empresa_id: Optional[int] = Header(default=None, alias="X-Empresa-Id"),
    db: Session = Depends(get_db),
):
    empresa_id = _empresa_id_header(x_empresa_id)
    return estoque_crud.criar_categoria(db, empresa_id, payload)


@router.put("/categorias/{categoria_id}", response_model=ProdutoCategoriaOut)
def atualizar_categoria(
    categoria_id: int,
    payload: ProdutoCategoriaUpdate,
    x_empresa_id: Optional[int] = Header(default=None, alias="X-Empresa-Id"),
    db: Session = Depends(get_db),
):
    empresa_id = _empresa_id_header(x_empresa_id)
    return estoque_crud.atualizar_categoria(db, empresa_id, categoria_id, payload)


@router.get("/produtos", response_model=list[ProdutoOut])
def listar_produtos(
    busca: Optional[str] = None,
    x_empresa_id: Optional[int] = Header(default=None, alias="X-Empresa-Id"),
    db: Session = Depends(get_db),
):
    empresa_id = _empresa_id_header(x_empresa_id)
    return estoque_crud.listar_produtos(db, empresa_id, busca)


@router.post("/produtos", response_model=ProdutoOut)
def criar_produto(
    payload: ProdutoCreate,
    x_empresa_id: Optional[int] = Header(default=None, alias="X-Empresa-Id"),
    db: Session = Depends(get_db),
):
    empresa_id = _empresa_id_header(x_empresa_id)
    return estoque_crud.criar_produto(db, empresa_id, payload)


@router.get("/produtos/{produto_id}", response_model=ProdutoOut)
def obter_produto(
    produto_id: int,
    x_empresa_id: Optional[int] = Header(default=None, alias="X-Empresa-Id"),
    db: Session = Depends(get_db),
):
    empresa_id = _empresa_id_header(x_empresa_id)
    return estoque_crud.obter_produto(db, empresa_id, produto_id)


@router.get("/posicao/{produto_id}", response_model=EstoquePosicaoProdutoOut)
def obter_posicao_produto(
    produto_id: int,
    x_empresa_id: Optional[int] = Header(default=None, alias="X-Empresa-Id"),
    db: Session = Depends(get_db),
):
    empresa_id = _empresa_id_header(x_empresa_id)
    return estoque_crud.obter_posicao_produto(db, empresa_id, produto_id)


@router.get("/relatorios/posicao-resumida", response_model=EstoqueRelatorioPosicaoOut)
def relatorio_posicao_resumida(
    busca: Optional[str] = None,
    somente_abaixo_minimo: bool = False,
    x_empresa_id: Optional[int] = Header(default=None, alias="X-Empresa-Id"),
    db: Session = Depends(get_db),
):
    empresa_id = _empresa_id_header(x_empresa_id)
    return estoque_crud.relatorio_posicao_resumida(
        db=db,
        empresa_id=empresa_id,
        busca=busca,
        somente_abaixo_minimo=somente_abaixo_minimo,
    )


@router.get("/relatorios/posicao-resumida.csv")
def relatorio_posicao_resumida_csv(
    busca: Optional[str] = None,
    somente_abaixo_minimo: bool = False,
    x_empresa_id: Optional[int] = Header(default=None, alias="X-Empresa-Id"),
    db: Session = Depends(get_db),
):
    empresa_id = _empresa_id_header(x_empresa_id)
    csv_content = estoque_crud.gerar_csv_relatorio_posicao_resumida(
        db=db,
        empresa_id=empresa_id,
        busca=busca,
        somente_abaixo_minimo=somente_abaixo_minimo,
    )

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="estoque_posicao_resumida.csv"'
        },
    )


@router.get("/relatorios/posicao-por-deposito/{deposito_id}", response_model=EstoqueRelatorioDepositoOut)
def relatorio_posicao_por_deposito(
    deposito_id: int,
    busca: Optional[str] = None,
    somente_abaixo_minimo: bool = False,
    x_empresa_id: Optional[int] = Header(default=None, alias="X-Empresa-Id"),
    db: Session = Depends(get_db),
):
    empresa_id = _empresa_id_header(x_empresa_id)
    return estoque_crud.relatorio_posicao_por_deposito(
        db=db,
        empresa_id=empresa_id,
        deposito_id=deposito_id,
        busca=busca,
        somente_abaixo_minimo=somente_abaixo_minimo,
    )


@router.get("/relatorios/posicao-por-deposito/{deposito_id}/csv")
def relatorio_posicao_por_deposito_csv(
    deposito_id: int,
    busca: Optional[str] = None,
    somente_abaixo_minimo: bool = False,
    x_empresa_id: Optional[int] = Header(default=None, alias="X-Empresa-Id"),
    db: Session = Depends(get_db),
):
    empresa_id = _empresa_id_header(x_empresa_id)
    csv_content = estoque_crud.gerar_csv_relatorio_posicao_por_deposito(
        db=db,
        empresa_id=empresa_id,
        deposito_id=deposito_id,
        busca=busca,
        somente_abaixo_minimo=somente_abaixo_minimo,
    )

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="estoque_posicao_deposito_{deposito_id}.csv"'
        },
    )


@router.put("/produtos/{produto_id}", response_model=ProdutoOut)
def atualizar_produto(
    produto_id: int,
    payload: ProdutoUpdate,
    x_empresa_id: Optional[int] = Header(default=None, alias="X-Empresa-Id"),
    db: Session = Depends(get_db),
):
    empresa_id = _empresa_id_header(x_empresa_id)
    return estoque_crud.atualizar_produto(db, empresa_id, produto_id, payload)


@router.post("/produtos/codigos-barras", response_model=ProdutoCodigoBarrasOut)
def criar_codigo_barras(
    payload: ProdutoCodigoBarrasCreate,
    x_empresa_id: Optional[int] = Header(default=None, alias="X-Empresa-Id"),
    db: Session = Depends(get_db),
):
    empresa_id = _empresa_id_header(x_empresa_id)
    return estoque_crud.criar_codigo_barras(db, empresa_id, payload)


@router.get("/depositos", response_model=list[EstoqueDepositoOut])
def listar_depositos(
    x_empresa_id: Optional[int] = Header(default=None, alias="X-Empresa-Id"),
    db: Session = Depends(get_db),
):
    empresa_id = _empresa_id_header(x_empresa_id)
    return estoque_crud.listar_depositos(db, empresa_id)


@router.post("/depositos", response_model=EstoqueDepositoOut)
def criar_deposito(
    payload: EstoqueDepositoCreate,
    x_empresa_id: Optional[int] = Header(default=None, alias="X-Empresa-Id"),
    db: Session = Depends(get_db),
):
    empresa_id = _empresa_id_header(x_empresa_id)
    return estoque_crud.criar_deposito(db, empresa_id, payload)


@router.put("/depositos/{deposito_id}", response_model=EstoqueDepositoOut)
def atualizar_deposito(
    deposito_id: int,
    payload: EstoqueDepositoUpdate,
    x_empresa_id: Optional[int] = Header(default=None, alias="X-Empresa-Id"),
    db: Session = Depends(get_db),
):
    empresa_id = _empresa_id_header(x_empresa_id)
    return estoque_crud.atualizar_deposito(db, empresa_id, deposito_id, payload)


@router.get("/saldos", response_model=list[EstoqueSaldoOut])
def listar_saldos(
    deposito_id: Optional[int] = None,
    produto_id: Optional[int] = None,
    x_empresa_id: Optional[int] = Header(default=None, alias="X-Empresa-Id"),
    db: Session = Depends(get_db),
):
    empresa_id = _empresa_id_header(x_empresa_id)
    return estoque_crud.listar_saldos(db, empresa_id, deposito_id, produto_id)


@router.get("/movimentos", response_model=list[EstoqueMovimentoOut])
def listar_movimentos(
    deposito_id: Optional[int] = None,
    produto_id: Optional[int] = None,
    x_empresa_id: Optional[int] = Header(default=None, alias="X-Empresa-Id"),
    db: Session = Depends(get_db),
):
    empresa_id = _empresa_id_header(x_empresa_id)
    return estoque_crud.listar_movimentos(db, empresa_id, deposito_id, produto_id)


@router.post("/movimentos/entrada-manual", response_model=EstoqueMovimentoOut)
def registrar_entrada_manual(
    payload: EstoqueMovimentoEntradaManualIn,
    x_empresa_id: Optional[int] = Header(default=None, alias="X-Empresa-Id"),
    x_usuario_id: Optional[int] = Header(default=None, alias="X-Usuario-Id"),
    db: Session = Depends(get_db),
):
    empresa_id = _empresa_id_header(x_empresa_id)
    return estoque_crud.registrar_entrada_manual(db, empresa_id, x_usuario_id, payload)


@router.post("/movimentos/saida-manual", response_model=EstoqueMovimentoOut)
def registrar_saida_manual(
    payload: EstoqueMovimentoSaidaManualIn,
    x_empresa_id: Optional[int] = Header(default=None, alias="X-Empresa-Id"),
    x_usuario_id: Optional[int] = Header(default=None, alias="X-Usuario-Id"),
    db: Session = Depends(get_db),
):
    empresa_id = _empresa_id_header(x_empresa_id)
    return estoque_crud.registrar_saida_manual(db, empresa_id, x_usuario_id, payload)


@router.post("/movimentos/ajuste", response_model=EstoqueMovimentoOut)
def registrar_ajuste_manual(
    payload: EstoqueMovimentoAjusteIn,
    x_empresa_id: Optional[int] = Header(default=None, alias="X-Empresa-Id"),
    x_usuario_id: Optional[int] = Header(default=None, alias="X-Usuario-Id"),
    db: Session = Depends(get_db),
):
    empresa_id = _empresa_id_header(x_empresa_id)
    return estoque_crud.registrar_ajuste_manual(db, empresa_id, x_usuario_id, payload)


@router.post("/movimentos/transferencia")
def registrar_transferencia(
    payload: EstoqueTransferenciaIn,
    x_empresa_id: Optional[int] = Header(default=None, alias="X-Empresa-Id"),
    x_usuario_id: Optional[int] = Header(default=None, alias="X-Usuario-Id"),
    db: Session = Depends(get_db),
):
    empresa_id = _empresa_id_header(x_empresa_id)
    return estoque_crud.registrar_transferencia(db, empresa_id, x_usuario_id, payload)


@router.post("/movimentos/inventario", response_model=EstoqueMovimentoOut)
def registrar_inventario(
    payload: EstoqueInventarioIn,
    x_empresa_id: Optional[int] = Header(default=None, alias="X-Empresa-Id"),
    x_usuario_id: Optional[int] = Header(default=None, alias="X-Usuario-Id"),
    db: Session = Depends(get_db),
):
    empresa_id = _empresa_id_header(x_empresa_id)
    return estoque_crud.registrar_inventario(db, empresa_id, x_usuario_id, payload)