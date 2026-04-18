from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import empresa as empresa_crud
from app.schemas.empresa import EmpresaCreate, EmpresaOut

router = APIRouter(prefix="/empresas", tags=["empresas"])

UPLOAD_DIR = Path("app/static/uploads/empresas")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".svg"}


def _remover_logo_local_antigo(logo_url: str | None) -> None:
    if not logo_url:
        return

    logo_url = str(logo_url).strip()
    if not logo_url.startswith("/static/uploads/empresas/"):
        return

    relative_path = logo_url.replace("/static/", "", 1)
    file_path = Path("app/static") / relative_path.replace("uploads/", "uploads/", 1).split("static/")[-1]
    if file_path.exists() and file_path.is_file():
        try:
            file_path.unlink()
        except Exception:
            pass


@router.get("/", response_model=list[EmpresaOut])
def listar(db: Session = Depends(get_db)):
    return empresa_crud.list_all(db)


@router.get("/{empresa_id}", response_model=EmpresaOut)
def obter(empresa_id: int, db: Session = Depends(get_db)):
    empresa = empresa_crud.get_by_id(db, empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    return empresa


@router.post("/", response_model=EmpresaOut)
def criar(payload: EmpresaCreate, db: Session = Depends(get_db)):
    return empresa_crud.create(db, payload)


@router.put("/{empresa_id}", response_model=EmpresaOut)
def atualizar(empresa_id: int, payload: EmpresaCreate, db: Session = Depends(get_db)):
    empresa = empresa_crud.get_by_id(db, empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    return empresa_crud.update(db, empresa, payload)


@router.post("/{empresa_id}/logo", response_model=EmpresaOut)
async def upload_logo_empresa(
    empresa_id: int,
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    empresa = empresa_crud.get_by_id(db, empresa_id)
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")

    nome_original = (arquivo.filename or "").strip()
    ext = Path(nome_original).suffix.lower()

    if not ext or ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Arquivo inválido. Envie PNG, JPG, JPEG, WEBP ou SVG.",
        )

    conteudo = await arquivo.read()
    if not conteudo:
        raise HTTPException(status_code=400, detail="Arquivo vazio.")

    if len(conteudo) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="O logo deve ter no máximo 5MB.")

    novo_nome = f"empresa_{empresa_id}_{uuid4().hex}{ext}"
    destino = UPLOAD_DIR / novo_nome
    destino.write_bytes(conteudo)

    _remover_logo_local_antigo(getattr(empresa, "logo_url", None))

    logo_url = f"/static/uploads/empresas/{novo_nome}"
    return empresa_crud.update_logo_url(db, empresa, logo_url)