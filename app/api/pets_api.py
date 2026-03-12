from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import pet as pet_crud
from app.schemas.pet import PetCreate, PetOut

router = APIRouter(prefix="/api/pets", tags=["pets"])


@router.get("/", response_model=list[PetOut])
def listar(
    q: str | None = Query(default=None),
    db: Session = Depends(get_db)
):
    return pet_crud.list_all(db, q=q)


@router.post("/", response_model=PetOut)
def criar(payload: PetCreate, db: Session = Depends(get_db)):
    return pet_crud.create(db, payload)


@router.put("/{pet_id}")
def editar_pet(pet_id: int, payload: dict, db: Session = Depends(get_db)):
    pet = pet_crud.get_by_id(db, pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet não encontrado.")

    pet = pet_crud.update(db, pet, payload)
    return {"id": pet.id, "message": "Pet atualizado com sucesso."}


@router.patch("/{pet_id}/toggle")
def toggle_pet(pet_id: int, db: Session = Depends(get_db)):
    pet = pet_crud.get_by_id(db, pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail="Pet não encontrado.")

    pet = pet_crud.toggle_ativo(db, pet)
    return {"id": pet.id, "ativo": pet.ativo}