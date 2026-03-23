from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.schemas.auth import LoginIn, TokenOut
from app.services.auth_service import login

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def auth_login(payload: LoginIn, db: Session = Depends(get_db)):
    result = login(db, payload.email, payload.senha)
    if not result:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    return result