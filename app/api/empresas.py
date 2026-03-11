from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.crud import empresa as empresa_crud
from app.schemas.empresa import EmpresaCreate, EmpresaOut

router = APIRouter(prefix="/empresas", tags=["empresas"])


@router.get("/", response_model=list[EmpresaOut])
def listar(db: Session = Depends(get_db)):
    return empresa_crud.list_all(db)


@router.post("/", response_model=EmpresaOut)
def criar(payload: EmpresaCreate, db: Session = Depends(get_db)):
    return empresa_crud.create(db, payload)