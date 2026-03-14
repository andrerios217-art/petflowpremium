from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import servico as servico_crud
from app.schemas.servico import ServicoCreate, ServicoOut

router = APIRouter(prefix="/api/servicos", tags=["servicos"])


@router.get("/", response_model=list[ServicoOut])
def listar(
    q: str | None = Query(default=None),
    tipo_servico: str | None = Query(default=None),
    db: Session = Depends(get_db)
):
    return servico_crud.list_all(db, q=q, tipo_servico=tipo_servico)


@router.get("/{servico_id}")
def obter(servico_id: int, db: Session = Depends(get_db)):
    servico = servico_crud.get_by_id(db, servico_id)
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado.")

    return {
        "id": servico.id,
        "empresa_id": servico.empresa_id,
        "nome": servico.nome,
        "tipo_servico": servico.tipo_servico,
        "porte_referencia": servico.porte_referencia,
        "custo": float(servico.custo) if servico.custo is not None else None,
        "venda": float(servico.venda) if servico.venda is not None else None,
        "tempo_minutos": servico.tempo_minutos,
        "ativo": servico.ativo
    }


@router.post("/", response_model=ServicoOut)
def criar(payload: ServicoCreate, db: Session = Depends(get_db)):
    return servico_crud.create(db, payload)


@router.put("/{servico_id}")
def editar(servico_id: int, payload: dict, db: Session = Depends(get_db)):
    servico = servico_crud.get_by_id(db, servico_id)
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado.")

    servico = servico_crud.update(db, servico, payload)
    return {"id": servico.id, "message": "Serviço atualizado com sucesso."}


@router.patch("/{servico_id}/toggle")
def toggle(servico_id: int, db: Session = Depends(get_db)):
    servico = servico_crud.get_by_id(db, servico_id)
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado.")

    servico = servico_crud.toggle_ativo(db, servico)
    return {"id": servico.id, "ativo": servico.ativo}


@router.delete("/{servico_id}")
def excluir(servico_id: int, db: Session = Depends(get_db)):
    servico = servico_crud.get_by_id(db, servico_id)
    if not servico:
        raise HTTPException(status_code=404, detail="Serviço não encontrado.")

    servico_crud.delete(db, servico)
    return {"message": "Serviço excluído com sucesso."}