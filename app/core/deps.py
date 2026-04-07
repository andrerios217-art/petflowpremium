from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import ALGORITHM
from app.models.funcionario import Funcionario
from app.models.usuario import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
        ) from exc


def get_current_actor(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> dict:
    payload = _decode_access_token(token)
    sub = payload.get("sub")

    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido.",
        )

    if isinstance(sub, str) and sub.startswith("funcionario:"):
        funcionario_id_raw = sub.split(":", 1)[1]

        if not funcionario_id_raw.isdigit():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido.",
            )

        funcionario = (
            db.query(Funcionario)
            .filter(Funcionario.id == int(funcionario_id_raw))
            .first()
        )

        if not funcionario or not getattr(funcionario, "ativo", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Funcionário não encontrado ou inativo.",
            )

        return {
            "tipo": "funcionario",
            "id": funcionario.id,
            "empresa_id": funcionario.empresa_id,
            "nome": funcionario.nome,
        }

    if not str(sub).isdigit():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido.",
        )

    usuario = db.query(Usuario).filter(Usuario.id == int(sub)).first()

    if not usuario or not getattr(usuario, "ativo", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo.",
        )

    return {
        "tipo": "usuario",
        "id": usuario.id,
        "empresa_id": usuario.empresa_id,
        "nome": usuario.nome,
    }


def get_empresa_id_atual(
    current_actor: dict = Depends(get_current_actor),
) -> int:
    empresa_id = current_actor.get("empresa_id")

    if not empresa_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário sem empresa vinculada.",
        )

    return int(empresa_id)


def get_usuario_id_atual(
    current_actor: dict = Depends(get_current_actor),
) -> int:
    usuario_id = current_actor.get("id")

    if not usuario_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário autenticado inválido.",
        )

    return int(usuario_id)


def get_usuario_admin_id_atual(
    current_actor: dict = Depends(get_current_actor),
) -> int:
    if current_actor.get("tipo") != "usuario":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ação permitida apenas para usuário administrador.",
        )

    return int(current_actor["id"])