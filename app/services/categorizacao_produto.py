from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.produto_categoria import ProdutoCategoria


CATEGORIA_RACAO = "RACAO"
CATEGORIA_PETISCOS = "PETISCOS"
CATEGORIA_BRINQUEDOS = "BRINQUEDOS"
CATEGORIA_MEDICAMENTOS = "MEDICAMENTOS"
CATEGORIA_HIGIENE = "PRODUTOS_HIGIENE"
CATEGORIA_LIMPEZA = "PRODUTOS_LIMPEZA"

CATEGORIAS_SUPORTADAS = {
    CATEGORIA_RACAO: "Ração",
    CATEGORIA_PETISCOS: "Petiscos",
    CATEGORIA_BRINQUEDOS: "Brinquedos",
    CATEGORIA_MEDICAMENTOS: "Medicamentos",
    CATEGORIA_HIGIENE: "Produtos de higiene",
    CATEGORIA_LIMPEZA: "Produtos de limpeza",
}

CATEGORIAS_DESCRICAO = {
    CATEGORIA_RACAO: "Alimentos completos ou complementares para cães, gatos, aves, peixes e outros pets.",
    CATEGORIA_PETISCOS: "Snacks, biscoitos, ossinhos, sachês de recompensa e itens mastigáveis de agrado.",
    CATEGORIA_BRINQUEDOS: "Bolas, mordedores, pelúcias, arranhadores, cordas e brinquedos interativos.",
    CATEGORIA_MEDICAMENTOS: "Medicamentos, antiparasitários, suplementos terapêuticos e produtos veterinários de tratamento.",
    CATEGORIA_HIGIENE: "Shampoos, condicionadores, tapetes higiênicos, lenços, areias, fraldas e cuidados de higiene.",
    CATEGORIA_LIMPEZA: "Desinfetantes, limpadores de ambiente, removedores de odor e produtos de limpeza do espaço.",
}

CATEGORIAS_ORDEM = [
    CATEGORIA_RACAO,
    CATEGORIA_PETISCOS,
    CATEGORIA_BRINQUEDOS,
    CATEGORIA_MEDICAMENTOS,
    CATEGORIA_HIGIENE,
    CATEGORIA_LIMPEZA,
]

REGRAS_PALAVRAS_CHAVE = {
    CATEGORIA_RACAO: [
        "racao",
        "ração",
        "alimento completo",
        "alimento umido",
        "alimento úmido",
        "alimento seco",
        "sache",
        "sachê",
        "granulado alimentar",
        "renal canine",
        "gastrointestinal",
        "urinary",
        "filhotes",
        "adultos",
        "senior",
    ],
    CATEGORIA_PETISCOS: [
        "petisco",
        "petiscos",
        "bifinho",
        "biscoito",
        "snack",
        "snacks",
        "ossinho",
        "osso mastigavel",
        "osso mastigável",
        "palito mastigavel",
        "palito mastigável",
        "agrado",
        "recompensa",
        "stick dental",
        "dental stick",
    ],
    CATEGORIA_BRINQUEDOS: [
        "brinquedo",
        "brinquedos",
        "bola",
        "mordedor",
        "corda",
        "pelucia",
        "pelúcia",
        "arranhador",
        "ratinho",
        "disco",
        "lancador",
        "lançador",
        "interativo",
        "kong",
        "varinha",
        "tunel",
        "túnel",
    ],
    CATEGORIA_MEDICAMENTOS: [
        "medicamento",
        "medicamentos",
        "antibiotico",
        "antibiótico",
        "antiinflamatorio",
        "anti-inflamatorio",
        "anti-inflamatório",
        "vermifugo",
        "vermífugo",
        "antipulgas",
        "antiparasitario",
        "antiparasitário",
        "antisseptico",
        "antisséptico",
        "suplemento",
        "vitamina",
        "otologico",
        "otológico",
        "colirio",
        "colírio",
        "pomada",
        "spray terapeutico",
        "spray terapêutico",
        "capsula",
        "cápsula",
        "comprimido",
        "solucao oral",
        "solução oral",
        "xarope",
    ],
    CATEGORIA_HIGIENE: [
        "higiene",
        "shampoo",
        "condicionador",
        "sabonete",
        "perfume",
        "colonia",
        "colônia",
        "lenço",
        "lenco",
        "umedecido",
        "tapete higienico",
        "tapete higiênico",
        "areia higienica",
        "areia higiênica",
        "fralda",
        "banho a seco",
        "banho seco",
        "desodorizador corporal",
        "hidratante",
    ],
    CATEGORIA_LIMPEZA: [
        "limpeza",
        "desinfetante",
        "sanitizante",
        "limpador",
        "removedor de odor",
        "removedor odor",
        "eliminador de odores",
        "limpa piso",
        "limpa canil",
        "limpa gatil",
        "lava ambiente",
        "higienizador de ambiente",
        "detergente",
        "amaciante",
        "cloro",
    ],
}

REGRAS_NCM = {
    "2309": CATEGORIA_RACAO,
    "3307": CATEGORIA_HIGIENE,
    "3402": CATEGORIA_LIMPEZA,
    "3808": CATEGORIA_MEDICAMENTOS,
    "9503": CATEGORIA_BRINQUEDOS,
}

SCHEMA_CLASSIFICACAO_API = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "categoria_slug": {
            "type": "string",
            "enum": CATEGORIAS_ORDEM,
        },
        "confianca": {
            "type": "number",
        },
        "motivo_curto": {
            "type": "string",
        },
    },
    "required": ["categoria_slug", "confianca", "motivo_curto"],
}


@dataclass
class ResultadoCategorizacaoProduto:
    categoria_slug: str
    categoria_nome: str
    categoria_id: Optional[int]
    confianca: float
    origem: str
    motivo: str

    @property
    def encontrado(self) -> bool:
        return self.categoria_id is not None


def _normalizar_texto(valor: str | None) -> str:
    texto = (valor or "").strip().lower()
    if not texto:
        return ""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _somente_digitos(valor: str | None) -> str:
    return re.sub(r"\D+", "", valor or "")


def _montar_texto_base(
    *,
    descricao: str | None,
    codigo_fornecedor: str | None = None,
    fornecedor_nome: str | None = None,
    codigo_barras: str | None = None,
    ncm: str | None = None,
) -> str:
    partes = [
        descricao or "",
        codigo_fornecedor or "",
        fornecedor_nome or "",
        codigo_barras or "",
        ncm or "",
    ]
    return _normalizar_texto(" | ".join(partes))


def _pontuar_por_palavras_chave(texto_base: str) -> dict[str, int]:
    pontuacoes = {slug: 0 for slug in CATEGORIAS_ORDEM}

    for slug, palavras in REGRAS_PALAVRAS_CHAVE.items():
        for palavra in palavras:
            termo = _normalizar_texto(palavra)
            if not termo:
                continue

            if f" {termo} " in f" {texto_base} ":
                pontuacoes[slug] += 3

            partes = termo.split()
            if len(partes) > 1 and all(parte in texto_base for parte in partes):
                pontuacoes[slug] += 1

    return pontuacoes


def _pontuar_por_ncm(ncm: str | None, pontuacoes: dict[str, int]) -> None:
    ncm_digitos = _somente_digitos(ncm)
    if len(ncm_digitos) < 4:
        return

    prefixo = ncm_digitos[:4]
    categoria = REGRAS_NCM.get(prefixo)
    if categoria:
        pontuacoes[categoria] += 4


def _resolver_melhor_categoria_local(
    *,
    descricao: str | None,
    codigo_fornecedor: str | None = None,
    fornecedor_nome: str | None = None,
    codigo_barras: str | None = None,
    ncm: str | None = None,
) -> Optional[tuple[str, float, str]]:
    texto_base = _montar_texto_base(
        descricao=descricao,
        codigo_fornecedor=codigo_fornecedor,
        fornecedor_nome=fornecedor_nome,
        codigo_barras=codigo_barras,
        ncm=ncm,
    )
    if not texto_base:
        return None

    pontuacoes = _pontuar_por_palavras_chave(texto_base)
    _pontuar_por_ncm(ncm, pontuacoes)

    melhor_slug = None
    melhor_pontuacao = 0
    segundo_lugar = 0

    for slug in CATEGORIAS_ORDEM:
        score = pontuacoes.get(slug, 0)
        if score > melhor_pontuacao:
            segundo_lugar = melhor_pontuacao
            melhor_pontuacao = score
            melhor_slug = slug
        elif score > segundo_lugar:
            segundo_lugar = score

    if not melhor_slug or melhor_pontuacao <= 0:
        return None

    margem = max(0, melhor_pontuacao - segundo_lugar)
    confianca = min(0.98, 0.45 + (melhor_pontuacao * 0.08) + (margem * 0.06))
    motivo = f"Classificação local por descrição/NCM ({melhor_pontuacao} pontos)."
    return melhor_slug, round(confianca, 4), motivo


def _timeout_api_externa() -> int:
    valor = settings.CATEGORIZACAO_API_TIMEOUT
    try:
        return max(3, int(valor))
    except (TypeError, ValueError):
        return 20


def _provider_api_externa() -> str:
    return (settings.CATEGORIZACAO_API_PROVIDER or "").strip().lower()


def _extrair_output_text_responses(payload: dict) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    for item in payload.get("output", []) or []:
        for content in item.get("content", []) or []:
            if content.get("type") == "output_text":
                texto = (content.get("text") or "").strip()
                if texto:
                    return texto

    return ""


def _post_json(url: str, headers: dict[str, str], body: dict) -> dict:
    data = json.dumps(body).encode("utf-8")
    request = Request(
        url=url,
        data=data,
        headers=headers,
        method="POST",
    )

    try:
        with urlopen(request, timeout=_timeout_api_externa()) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw)
    except HTTPError as exc:
        detalhe = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Falha HTTP na API externa ({exc.code}): {detalhe}") from exc
    except URLError as exc:
        raise RuntimeError(f"Falha de conexão na API externa: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("Resposta inválida da API externa.") from exc


def _classificar_por_openai(
    *,
    descricao: str | None,
    codigo_fornecedor: str | None = None,
    fornecedor_nome: str | None = None,
    codigo_barras: str | None = None,
    ncm: str | None = None,
) -> Optional[tuple[str, float, str]]:
    api_key = (settings.OPENAI_API_KEY or "").strip()
    model = (settings.CATEGORIZACAO_API_MODEL or "").strip()
    if not api_key or not model:
        return None

    descricao = (descricao or "").strip()
    if not descricao:
        return None

    url = (settings.OPENAI_BASE_URL or "https://api.openai.com/v1").rstrip("/") + "/responses"

    system_prompt = (
        "Você classifica produtos pet em apenas uma categoria fixa. "
        "Escolha somente uma entre: RACAO, PETISCOS, BRINQUEDOS, MEDICAMENTOS, "
        "PRODUTOS_HIGIENE, PRODUTOS_LIMPEZA. "
        "Use descrição, NCM, fornecedor e contexto do item. "
        "Se houver dúvida, escolha a categoria mais provável, sem inventar categoria fora da lista."
    )

    user_prompt = {
        "descricao": descricao,
        "codigo_fornecedor": codigo_fornecedor,
        "fornecedor_nome": fornecedor_nome,
        "codigo_barras": codigo_barras,
        "ncm": ncm,
        "categorias": CATEGORIAS_DESCRICAO,
    }

    payload = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": system_prompt,
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": json.dumps(user_prompt, ensure_ascii=False),
                    }
                ],
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "classificacao_categoria_produto",
                "strict": True,
                "schema": SCHEMA_CLASSIFICACAO_API,
            }
        },
    }

    response = _post_json(
        url=url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        body=payload,
    )

    raw_text = _extrair_output_text_responses(response)
    if not raw_text:
        return None

    data = json.loads(raw_text)
    categoria_slug = (data.get("categoria_slug") or "").strip().upper()
    if categoria_slug not in CATEGORIAS_SUPORTADAS:
        return None

    confianca = float(data.get("confianca") or 0)
    confianca = max(0.0, min(1.0, confianca))
    motivo = (data.get("motivo_curto") or "").strip() or "Classificação por API externa."
    return categoria_slug, confianca, motivo


def _classificar_por_webhook_generico(
    *,
    descricao: str | None,
    codigo_fornecedor: str | None = None,
    fornecedor_nome: str | None = None,
    codigo_barras: str | None = None,
    ncm: str | None = None,
) -> Optional[tuple[str, float, str]]:
    url = (settings.CATEGORIZACAO_API_URL or "").strip()
    if not url:
        return None

    token = (settings.CATEGORIZACAO_API_TOKEN or "").strip()

    payload = {
        "descricao": descricao,
        "codigo_fornecedor": codigo_fornecedor,
        "fornecedor_nome": fornecedor_nome,
        "codigo_barras": codigo_barras,
        "ncm": ncm,
        "categorias_permitidas": CATEGORIAS_ORDEM,
    }

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = _post_json(url=url, headers=headers, body=payload)

    categoria_slug = (response.get("categoria_slug") or "").strip().upper()
    if categoria_slug not in CATEGORIAS_SUPORTADAS:
        return None

    confianca = float(response.get("confianca") or 0)
    confianca = max(0.0, min(1.0, confianca))
    motivo = (response.get("motivo_curto") or "").strip() or "Classificação por webhook externo."
    return categoria_slug, confianca, motivo


def _classificar_por_api_externa(
    *,
    descricao: str | None,
    codigo_fornecedor: str | None = None,
    fornecedor_nome: str | None = None,
    codigo_barras: str | None = None,
    ncm: str | None = None,
) -> Optional[tuple[str, float, str]]:
    provider = _provider_api_externa()
    if provider == "openai":
        return _classificar_por_openai(
            descricao=descricao,
            codigo_fornecedor=codigo_fornecedor,
            fornecedor_nome=fornecedor_nome,
            codigo_barras=codigo_barras,
            ncm=ncm,
        )

    if provider in {"webhook", "generic", "generico"}:
        return _classificar_por_webhook_generico(
            descricao=descricao,
            codigo_fornecedor=codigo_fornecedor,
            fornecedor_nome=fornecedor_nome,
            codigo_barras=codigo_barras,
            ncm=ncm,
        )

    return None


def garantir_categorias_base(db: Session, empresa_id: int) -> list[ProdutoCategoria]:
    existentes = (
        db.query(ProdutoCategoria)
        .filter(ProdutoCategoria.empresa_id == empresa_id)
        .all()
    )

    por_nome_normalizado = {
        _normalizar_texto(categoria.nome): categoria
        for categoria in existentes
    }

    criadas = False

    for slug in CATEGORIAS_ORDEM:
        nome = CATEGORIAS_SUPORTADAS[slug]
        descricao = CATEGORIAS_DESCRICAO.get(slug)
        chave = _normalizar_texto(nome)

        categoria = por_nome_normalizado.get(chave)
        if categoria:
            if not categoria.ativo:
                categoria.ativo = True
                criadas = True
            continue

        categoria = ProdutoCategoria(
            empresa_id=empresa_id,
            nome=nome,
            descricao=descricao,
            ativo=True,
        )
        db.add(categoria)
        existentes.append(categoria)
        por_nome_normalizado[chave] = categoria
        criadas = True

    if criadas:
        db.commit()
        for categoria in existentes:
            if categoria.id is None:
                db.refresh(categoria)

    return (
        db.query(ProdutoCategoria)
        .filter(ProdutoCategoria.empresa_id == empresa_id)
        .order_by(func.lower(ProdutoCategoria.nome))
        .all()
    )


def obter_categoria_por_slug(
    db: Session,
    empresa_id: int,
    categoria_slug: str,
) -> Optional[ProdutoCategoria]:
    nome = CATEGORIAS_SUPORTADAS.get((categoria_slug or "").strip().upper())
    if not nome:
        return None

    return (
        db.query(ProdutoCategoria)
        .filter(
            ProdutoCategoria.empresa_id == empresa_id,
            func.lower(ProdutoCategoria.nome) == _normalizar_texto(nome),
        )
        .first()
    )


def classificar_categoria_produto(
    db: Session,
    empresa_id: int,
    *,
    descricao: str | None,
    codigo_fornecedor: str | None = None,
    fornecedor_nome: str | None = None,
    codigo_barras: str | None = None,
    ncm: str | None = None,
    usar_api_externa: bool = True,
    confianca_minima_local: float = 0.78,
) -> Optional[ResultadoCategorizacaoProduto]:
    garantir_categorias_base(db, empresa_id)

    local = _resolver_melhor_categoria_local(
        descricao=descricao,
        codigo_fornecedor=codigo_fornecedor,
        fornecedor_nome=fornecedor_nome,
        codigo_barras=codigo_barras,
        ncm=ncm,
    )

    if local and local[1] >= confianca_minima_local:
        categoria = obter_categoria_por_slug(db, empresa_id, local[0])
        return ResultadoCategorizacaoProduto(
            categoria_slug=local[0],
            categoria_nome=CATEGORIAS_SUPORTADAS[local[0]],
            categoria_id=categoria.id if categoria else None,
            confianca=local[1],
            origem="LOCAL",
            motivo=local[2],
        )

    if usar_api_externa:
        externa = _classificar_por_api_externa(
            descricao=descricao,
            codigo_fornecedor=codigo_fornecedor,
            fornecedor_nome=fornecedor_nome,
            codigo_barras=codigo_barras,
            ncm=ncm,
        )
        if externa:
            categoria = obter_categoria_por_slug(db, empresa_id, externa[0])
            return ResultadoCategorizacaoProduto(
                categoria_slug=externa[0],
                categoria_nome=CATEGORIAS_SUPORTADAS[externa[0]],
                categoria_id=categoria.id if categoria else None,
                confianca=externa[1],
                origem="API_EXTERNA",
                motivo=externa[2],
            )

    if local:
        categoria = obter_categoria_por_slug(db, empresa_id, local[0])
        return ResultadoCategorizacaoProduto(
            categoria_slug=local[0],
            categoria_nome=CATEGORIAS_SUPORTADAS[local[0]],
            categoria_id=categoria.id if categoria else None,
            confianca=local[1],
            origem="LOCAL_BAIXA_CONFIANCA",
            motivo=local[2],
        )

    return None