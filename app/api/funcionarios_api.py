from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import funcionario as funcionario_crud
from app.schemas.funcionario import FuncionarioCreate, FuncionarioOut, FUNCOES_VALIDAS

router = APIRouter(prefix="/api/funcionarios", tags=["funcionarios"])


def serializar_funcionario(funcionario):
    return {
        "id": funcionario.id,
        "empresa_id": funcionario.empresa_id,
        "nome": funcionario.nome,
        "cpf": funcionario.cpf,
        "email": funcionario.email,
        "telefone": funcionario.telefone,
        "funcao": funcionario.funcao,
        "acesso_dashboard": funcionario.acesso_dashboard,
        "acesso_clientes": funcionario.acesso_clientes,
        "acesso_pets": funcionario.acesso_pets,
        "acesso_servicos": funcionario.acesso_servicos,
        "acesso_funcionarios": funcionario.acesso_funcionarios,
        "acesso_agenda": funcionario.acesso_agenda,
        "acesso_producao": funcionario.acesso_producao,
        "acesso_estoque": funcionario.acesso_estoque,
        "acesso_financeiro": funcionario.acesso_financeiro,
        "acesso_crm": funcionario.acesso_crm,
        "acesso_relatorios": funcionario.acesso_relatorios,
        "acesso_configuracoes": funcionario.acesso_configuracoes,
        "ativo": funcionario.ativo,
    }


@router.get("/")
def listar(
    q: str | None = Query(default=None),
    empresa_id: int | None = Query(default=None),
    apenas_ativos: bool = Query(default=True),
    apenas_producao: bool = Query(default=False),
    db: Session = Depends(get_db)
):
    funcionarios = funcionario_crud.list_all(db, q=q)

    if empresa_id is not None:
        funcionarios = [f for f in funcionarios if f.empresa_id == empresa_id]

    if apenas_ativos:
        funcionarios = [f for f in funcionarios if f.ativo]

    if apenas_producao:
        funcionarios = [f for f in funcionarios if f.acesso_producao]

    return [serializar_funcionario(funcionario) for funcionario in funcionarios]


@router.get("/{funcionario_id}")
def obter(funcionario_id: int, db: Session = Depends(get_db)):
    funcionario = funcionario_crud.get_by_id(db, funcionario_id)
    if not funcionario:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado.")

    return serializar_funcionario(funcionario)


@router.post("/", response_model=FuncionarioOut)
def criar(payload: FuncionarioCreate, db: Session = Depends(get_db)):
    existente = funcionario_crud.get_by_email(db, payload.email)
    if existente:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado para outro funcionário.")

    return funcionario_crud.create(db, payload)


@router.put("/{funcionario_id}")
def editar(funcionario_id: int, payload: dict, db: Session = Depends(get_db)):
    funcionario = funcionario_crud.get_by_id(db, funcionario_id)
    if not funcionario:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado.")

    outro = funcionario_crud.get_by_email(db, payload.get("email"))
    if outro and outro.id != funcionario_id:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado para outro funcionário.")

    funcao = (payload.get("funcao") or "").strip()
    if funcao not in FUNCOES_VALIDAS:
        raise HTTPException(status_code=400, detail="Função inválida.")

    payload["funcao"] = funcao

    funcionario = funcionario_crud.update(db, funcionario, payload)
    return {"id": funcionario.id, "message": "Funcionário atualizado com sucesso."}


@router.patch("/{funcionario_id}/toggle")
def toggle(funcionario_id: int, db: Session = Depends(get_db)):
    funcionario = funcionario_crud.get_by_id(db, funcionario_id)
    if not funcionario:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado.")

    funcionario = funcionario_crud.toggle_ativo(db, funcionario)
    return {"id": funcionario.id, "ativo": funcionario.ativo}