from pathlib import Path
from uuid import uuid4
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json
import re

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


def _somente_digitos(valor: str | None) -> str:
    return re.sub(r"\D", "", str(valor or ""))


def _formatar_cnpj(valor: str | None) -> str | None:
    cnpj = _somente_digitos(valor)
    if len(cnpj) != 14:
        return None
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"


def _formatar_cep(valor: str | None) -> str | None:
    cep = _somente_digitos(valor)
    if len(cep) != 8:
        return valor or None
    return f"{cep[:5]}-{cep[5:]}"


def _extrair_email_principal(payload: dict) -> str | None:
    if payload.get("email"):
        return str(payload.get("email")).strip() or None

    emails = payload.get("emails")
    if isinstance(emails, list) and emails:
        primeiro = emails[0]
        if isinstance(primeiro, dict):
            return str(primeiro.get("address") or primeiro.get("email") or "").strip() or None
        return str(primeiro).strip() or None

    return None


def _extrair_telefone_principal(payload: dict) -> str | None:
    if payload.get("ddd_telefone_1"):
        return str(payload.get("ddd_telefone_1")).strip() or None

    if payload.get("telefone"):
        return str(payload.get("telefone")).strip() or None

    telefones = payload.get("phones")
    if isinstance(telefones, list) and telefones:
        primeiro = telefones[0]
        if isinstance(primeiro, dict):
            return str(
                primeiro.get("number")
                or primeiro.get("phone")
                or primeiro.get("full_number")
                or ""
            ).strip() or None
        return str(primeiro).strip() or None

    return None


def _normalizar_payload_cnpj(payload: dict) -> dict:
    numero = _somente_digitos(payload.get("cnpj") or payload.get("cnpj_raiz") or "")
    cnpj_formatado = _formatar_cnpj(numero)

    logradouro_partes = [
        payload.get("descricao_tipo_de_logradouro"),
        payload.get("logradouro"),
    ]
    logradouro = " ".join([str(item).strip() for item in logradouro_partes if str(item or "").strip()]) or None

    return {
        "cnpj": cnpj_formatado,
        "nome": payload.get("nome_fantasia") or payload.get("razao_social") or payload.get("nome") or "",
        "razao_social": payload.get("razao_social") or payload.get("nome") or None,
        "nome_fantasia": payload.get("nome_fantasia") or None,
        "telefone": _extrair_telefone_principal(payload),
        "email": _extrair_email_principal(payload),
        "cep": _formatar_cep(payload.get("cep")),
        "logradouro": logradouro,
        "numero": str(payload.get("numero") or "").strip() or None,
        "complemento": str(payload.get("complemento") or "").strip() or None,
        "bairro": str(payload.get("bairro") or "").strip() or None,
        "cidade": str(payload.get("municipio") or payload.get("cidade") or "").strip() or None,
        "uf": str(payload.get("uf") or "").strip() or None,
    }


def _buscar_dados_cnpj_externo(cnpj: str) -> dict:
    cnpj_numerico = _somente_digitos(cnpj)
    if len(cnpj_numerico) != 14:
        raise HTTPException(status_code=400, detail="CNPJ inválido. Informe 14 dígitos.")

    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_numerico}"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "petflowpremium/1.0",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=15) as response:
            raw = response.read().decode("utf-8")
            data = json.loads(raw) if raw else {}
    except HTTPError as exc:
        try:
            raw = exc.read().decode("utf-8")
            error_data = json.loads(raw) if raw else {}
            detail = error_data.get("message") or error_data.get("detail") or "Falha ao consultar CNPJ."
        except Exception:
            detail = "Falha ao consultar CNPJ."
        raise HTTPException(status_code=exc.code or 502, detail=detail) from exc
    except URLError as exc:
        raise HTTPException(
            status_code=502,
            detail="Não foi possível consultar o serviço externo de CNPJ no momento.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Erro inesperado ao consultar o CNPJ.",
        ) from exc

    if not isinstance(data, dict) or not data:
        raise HTTPException(status_code=404, detail="CNPJ não encontrado.")

    return _normalizar_payload_cnpj(data)


@router.get("/", response_model=list[EmpresaOut])
def listar(db: Session = Depends(get_db)):
    return empresa_crud.list_all(db)


@router.get("/buscar-cnpj/{cnpj}")
def buscar_cnpj(cnpj: str):
    return _buscar_dados_cnpj_externo(cnpj)


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