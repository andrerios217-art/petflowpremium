from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.crud import permissao as permissao_crud
from app.crud import usuario as usuario_crud
from app.schemas.usuario import UsuarioCreate, UsuarioOut

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("/", response_model=list[UsuarioOut])
def listar(db: Session = Depends(get_db)):
    return usuario_crud.list_all(db)


@router.post("/", response_model=UsuarioOut)
def criar(payload: UsuarioCreate, db: Session = Depends(get_db)):
    usuario = usuario_crud.create(db, payload)
    permissao_crud.create_default_permissions(db, usuario.id)
    return usuario