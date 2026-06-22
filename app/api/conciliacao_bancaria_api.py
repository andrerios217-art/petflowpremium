from datetime import date, datetime, timedelta
from decimal import Decimal
from io import BytesIO, StringIO
from typing import Any
import csv
import re
import unicodedata

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_db
from app.models.financeiro_pagar import FinanceiroPagar
from app.models.financeiro_receber import FinanceiroReceber


router = APIRouter(prefix="/api/conciliacao-bancaria", tags=["Conciliação Bancária"])


CABECALHOS_DATA = [
    "data",
    "dt",
    "data movimento",
    "data do movimento",
    "data lancamento",
    "data lançamento",
    "lancamento",
    "lançamento",
]

CABECALHOS_DESCRICAO = [
    "descricao",
    "descrição",
    "historico",
    "histórico",
    "memo",
    "detalhe",
    "detalhes",
    "nome",
    "favorecido",
    "pagador",
    "fornecedor",
    "cliente",
]

CABECALHOS_VALOR = [
    "valor",
    "vlr",
    "amount",
    "valor lancamento",
    "valor lançamento",
    "valor movimento",
]

CABECALHOS_ENTRADA = [
    "entrada",
    "credito",
    "crédito",
    "credit",
    "receita",
    "recebimento",
]

CABECALHOS_SAIDA = [
    "saida",
    "saída",
    "debito",
    "débito",
    "debit",
    "despesa",
    "pagamento",
]

CABECALHOS_TIPO = [
    "tipo",
    "natureza",
    "operacao",
    "operação",
    "dc",
    "d/c",
    "credito debito",
    "crédito débito",
]

CABECALHOS_DOCUMENTO = [
    "documento",
    "doc",
    "id",
    "identificador",
    "numero",
    "número",
    "nsu",
]

PALAVRAS_ENTRADA = [
    "credito",
    "crédito",
    "entrada",
    "receita",
    "recebimento",
    "deposito",
    "depósito",
    "pix recebido",
    "c",
]

PALAVRAS_SAIDA = [
    "debito",
    "débito",
    "saida",
    "saída",
    "despesa",
    "pagamento",
    "pix enviado",
    "tarifa",
    "d",
]


def _limpar_texto(valor: Any) -> str:
    if valor is None:
        return ""

    texto = str(valor).strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(char for char in texto if unicodedata.category(char) != "Mn")
    texto = texto.lower()
    texto = texto.replace("_", " ").replace("-", " ")
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def _compactar_texto(valor: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", _limpar_texto(valor))


def _texto_para_busca(valor: Any) -> str:
    texto = _limpar_texto(valor)
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def _decimal(valor: Any) -> Decimal:
    if valor is None:
        return Decimal("0.00")

    if isinstance(valor, Decimal):
        return valor

    texto = str(valor).strip()

    if not texto:
        return Decimal("0.00")

    negativo = False

    if texto.startswith("(") and texto.endswith(")"):
        negativo = True
        texto = texto[1:-1]

    texto = texto.replace("R$", "")
    texto = texto.replace("r$", "")
    texto = texto.replace(" ", "")

    if texto.startswith("-"):
        negativo = True
        texto = texto[1:]

    texto = re.sub(r"[^0-9,.-]", "", texto)

    if "," in texto and "." in texto:
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    elif "," in texto:
        texto = texto.replace(".", "").replace(",", ".")

    try:
        valor_decimal = Decimal(texto or "0")
    except Exception:
        valor_decimal = Decimal("0.00")

    return -valor_decimal if negativo else valor_decimal


def _float(valor: Any) -> float:
    return float(_decimal(valor).quantize(Decimal("0.01")))


def _parse_data(valor: Any) -> date | None:
    if valor is None:
        return None

    texto = str(valor).strip()

    if not texto:
        return None

    texto = texto.split(" ")[0].strip()

    formatos = [
        "%d/%m/%Y",
        "%d/%m/%y",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d-%m-%y",
        "%Y/%m/%d",
    ]

    for formato in formatos:
        try:
            return datetime.strptime(texto, formato).date()
        except Exception:
            pass

    return None


def _detectar_coluna(cabecalhos: list[str], candidatos: list[str]) -> str | None:
    mapa = {_compactar_texto(cabecalho): cabecalho for cabecalho in cabecalhos}

    for candidato in candidatos:
        chave = _compactar_texto(candidato)
        if chave in mapa:
            return mapa[chave]

    for cabecalho in cabecalhos:
        cabecalho_limpo = _limpar_texto(cabecalho)
        for candidato in candidatos:
            candidato_limpo = _limpar_texto(candidato)
            if candidato_limpo and candidato_limpo in cabecalho_limpo:
                return cabecalho

    return None


def _status_atual(conta: Any) -> str:
    status = getattr(conta, "status", None) or getattr(conta, "status_atual", None) or "PENDENTE"
    return str(status).upper()


def _valor_realizado(conta: Any) -> Decimal:
    valor_pago = _decimal(getattr(conta, "valor_pago", None))

    if valor_pago > 0:
        return valor_pago

    return _decimal(getattr(conta, "valor", None))


def _descricao_conta(conta: Any) -> str:
    descricao = getattr(conta, "descricao", None)

    if descricao:
        return str(descricao)

    origem_tipo = getattr(conta, "origem_tipo", None)
    origem_id = getattr(conta, "origem_id", None)

    if origem_tipo and origem_id:
        return f"{origem_tipo} #{origem_id}"

    return "Lançamento financeiro"


def _nome_cliente(conta: Any) -> str | None:
    cliente = getattr(conta, "cliente", None)

    if not cliente:
        return None

    for campo in ["nome", "nome_completo", "razao_social", "nome_fantasia"]:
        valor = getattr(cliente, campo, None)
        if valor:
            return str(valor)

    return None


def _nome_fornecedor(conta: Any) -> str | None:
    valor = getattr(conta, "fornecedor", None)
    return str(valor).strip() if valor not in (None, "") else None


def _forma_pagamento(conta: Any) -> str | None:
    for campo in [
        "forma_pagamento_baixa",
        "forma_pagamento",
        "meio_pagamento",
        "metodo_pagamento",
        "tipo_pagamento",
        "pagamento_forma",
    ]:
        if hasattr(conta, campo):
            valor = getattr(conta, campo)
            if valor not in (None, ""):
                return str(valor)

    return None


def _linha_financeiro_receber(conta: FinanceiroReceber) -> dict[str, Any]:
    return {
        "origem": "financeiro_receber",
        "id": conta.id,
        "tipo": "ENTRADA",
        "data": conta.data_pagamento,
        "data_iso": conta.data_pagamento.isoformat() if conta.data_pagamento else None,
        "descricao": _descricao_conta(conta),
        "pessoa": _nome_cliente(conta),
        "forma_pagamento": _forma_pagamento(conta),
        "valor": _valor_realizado(conta),
        "valor_float": _float(_valor_realizado(conta)),
        "status": _status_atual(conta),
        "texto_busca": _texto_para_busca(f"{_descricao_conta(conta)} {_nome_cliente(conta) or ''}"),
    }


def _linha_financeiro_pagar(conta: FinanceiroPagar) -> dict[str, Any]:
    return {
        "origem": "financeiro_pagar",
        "id": conta.id,
        "tipo": "SAIDA",
        "data": conta.data_pagamento,
        "data_iso": conta.data_pagamento.isoformat() if conta.data_pagamento else None,
        "descricao": _descricao_conta(conta),
        "pessoa": _nome_fornecedor(conta),
        "forma_pagamento": _forma_pagamento(conta),
        "valor": _valor_realizado(conta),
        "valor_float": _float(_valor_realizado(conta)),
        "status": _status_atual(conta),
        "texto_busca": _texto_para_busca(f"{_descricao_conta(conta)} {_nome_fornecedor(conta) or ''}"),
    }


def _consultar_financeiro_realizado(
    db: Session,
    empresa_id: int,
    data_inicio: date,
    data_fim: date,
) -> list[dict[str, Any]]:
    recebimentos = (
        db.query(FinanceiroReceber)
        .options(joinedload(FinanceiroReceber.cliente))
        .filter(FinanceiroReceber.empresa_id == empresa_id)
        .filter(FinanceiroReceber.status == "PAGO")
        .filter(FinanceiroReceber.data_pagamento >= data_inicio)
        .filter(FinanceiroReceber.data_pagamento <= data_fim)
        .order_by(FinanceiroReceber.data_pagamento.asc(), FinanceiroReceber.id.asc())
        .all()
    )

    pagamentos = (
        db.query(FinanceiroPagar)
        .filter(FinanceiroPagar.empresa_id == empresa_id)
        .filter(FinanceiroPagar.status == "PAGO")
        .filter(FinanceiroPagar.data_pagamento >= data_inicio)
        .filter(FinanceiroPagar.data_pagamento <= data_fim)
        .order_by(FinanceiroPagar.data_pagamento.asc(), FinanceiroPagar.id.asc())
        .all()
    )

    movimentos = [_linha_financeiro_receber(item) for item in recebimentos]
    movimentos.extend([_linha_financeiro_pagar(item) for item in pagamentos])

    movimentos.sort(
        key=lambda item: (
            item["data"] or date.min,
            item["tipo"],
            item["descricao"] or "",
        )
    )

    return movimentos


def _ler_upload_texto(arquivo: UploadFile) -> str:
    conteudo = arquivo.file.read()

    if not conteudo:
        raise HTTPException(status_code=400, detail="Arquivo vazio.")

    for encoding in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
        try:
            return conteudo.decode(encoding)
        except Exception:
            pass

    raise HTTPException(
        status_code=400,
        detail="Não foi possível ler o arquivo. Envie CSV em UTF-8, ANSI ou Latin-1.",
    )


def _detectar_dialeto_csv(texto: str):
    amostra = texto[:4096]

    try:
        return csv.Sniffer().sniff(amostra, delimiters=";,|\t,")
    except Exception:
        class DialetoFallback(csv.excel):
            delimiter = ";"

        return DialetoFallback


def _parse_csv(texto: str) -> list[dict[str, Any]]:
    texto = texto.replace("\ufeff", "").strip()

    if not texto:
        raise HTTPException(status_code=400, detail="CSV vazio.")

    dialeto = _detectar_dialeto_csv(texto)
    reader = csv.DictReader(StringIO(texto), dialect=dialeto)

    if not reader.fieldnames:
        raise HTTPException(
            status_code=400,
            detail="CSV sem cabeçalho. Use colunas como Data, Descrição e Valor.",
        )

    cabecalhos = [cabecalho for cabecalho in reader.fieldnames if cabecalho]

    coluna_data = _detectar_coluna(cabecalhos, CABECALHOS_DATA)
    coluna_descricao = _detectar_coluna(cabecalhos, CABECALHOS_DESCRICAO)
    coluna_valor = _detectar_coluna(cabecalhos, CABECALHOS_VALOR)
    coluna_entrada = _detectar_coluna(cabecalhos, CABECALHOS_ENTRADA)
    coluna_saida = _detectar_coluna(cabecalhos, CABECALHOS_SAIDA)
    coluna_tipo = _detectar_coluna(cabecalhos, CABECALHOS_TIPO)
    coluna_documento = _detectar_coluna(cabecalhos, CABECALHOS_DOCUMENTO)

    if not coluna_data:
        raise HTTPException(
            status_code=400,
            detail="Não encontrei a coluna de data no CSV.",
        )

    if not coluna_valor and not coluna_entrada and not coluna_saida:
        raise HTTPException(
            status_code=400,
            detail="Não encontrei coluna de valor, entrada ou saída no CSV.",
        )

    movimentos: list[dict[str, Any]] = []

    for numero_linha, linha in enumerate(reader, start=2):
        data_movimento = _parse_data(linha.get(coluna_data))

        if not data_movimento:
            continue

        descricao = str(linha.get(coluna_descricao) or "").strip() if coluna_descricao else ""
        documento = str(linha.get(coluna_documento) or "").strip() if coluna_documento else ""
        tipo_texto = str(linha.get(coluna_tipo) or "").strip() if coluna_tipo else ""

        valor = Decimal("0.00")

        if coluna_entrada or coluna_saida:
            entrada = _decimal(linha.get(coluna_entrada)) if coluna_entrada else Decimal("0.00")
            saida = _decimal(linha.get(coluna_saida)) if coluna_saida else Decimal("0.00")

            if entrada > 0 and saida == 0:
                valor = entrada
            elif saida > 0 and entrada == 0:
                valor = -saida
            else:
                valor = entrada - saida
        elif coluna_valor:
            valor = _decimal(linha.get(coluna_valor))

        tipo_normalizado = _limpar_texto(tipo_texto)

        if tipo_normalizado in [_limpar_texto(item) for item in PALAVRAS_SAIDA] and valor > 0:
            valor = -valor

        if tipo_normalizado in [_limpar_texto(item) for item in PALAVRAS_ENTRADA] and valor < 0:
            valor = abs(valor)

        if valor == 0:
            continue

        tipo = "ENTRADA" if valor > 0 else "SAIDA"

        movimentos.append(
            {
                "linha": numero_linha,
                "data": data_movimento,
                "data_iso": data_movimento.isoformat(),
                "descricao": descricao or "Movimento bancário",
                "documento": documento or None,
                "tipo": tipo,
                "valor": abs(valor),
                "valor_float": _float(abs(valor)),
                "valor_original": _float(valor),
                "texto_busca": _texto_para_busca(f"{descricao} {documento}"),
                "conciliado": False,
                "match": None,
                "score": 0,
                "motivo": None,
            }
        )

    if not movimentos:
        raise HTTPException(
            status_code=400,
            detail="Nenhum movimento válido encontrado no CSV.",
        )

    movimentos.sort(
        key=lambda item: (
            item["data"],
            item["tipo"],
            item["descricao"] or "",
        )
    )

    return movimentos


def _parse_ofx(texto: str) -> list[dict[str, Any]]:
    texto = texto.replace("\r", "\n")
    blocos = re.findall(r"<STMTTRN>(.*?)(?=<STMTTRN>|</BANKTRANLIST>|</CREDITCARDMSGSRSV1>|$)", texto, flags=re.I | re.S)

    movimentos: list[dict[str, Any]] = []

    for numero, bloco in enumerate(blocos, start=1):
        tipo_ofx = _extrair_tag_ofx(bloco, "TRNTYPE") or ""
        data_raw = _extrair_tag_ofx(bloco, "DTPOSTED") or _extrair_tag_ofx(bloco, "DTUSER")
        valor_raw = _extrair_tag_ofx(bloco, "TRNAMT")
        descricao = (
            _extrair_tag_ofx(bloco, "MEMO")
            or _extrair_tag_ofx(bloco, "NAME")
            or _extrair_tag_ofx(bloco, "PAYEE")
            or "Movimento bancário"
        )
        documento = _extrair_tag_ofx(bloco, "FITID") or _extrair_tag_ofx(bloco, "CHECKNUM")

        data_movimento = _parse_data_ofx(data_raw)
        valor = _decimal(valor_raw)

        if not data_movimento or valor == 0:
            continue

        tipo_limpo = _limpar_texto(tipo_ofx)

        if tipo_limpo in ["debit", "debito", "payment", "pagamento"] and valor > 0:
            valor = -valor

        if tipo_limpo in ["credit", "credito", "dep", "deposit", "deposito"] and valor < 0:
            valor = abs(valor)

        tipo = "ENTRADA" if valor > 0 else "SAIDA"

        movimentos.append(
            {
                "linha": numero,
                "data": data_movimento,
                "data_iso": data_movimento.isoformat(),
                "descricao": descricao.strip(),
                "documento": documento.strip() if documento else None,
                "tipo": tipo,
                "valor": abs(valor),
                "valor_float": _float(abs(valor)),
                "valor_original": _float(valor),
                "texto_busca": _texto_para_busca(f"{descricao} {documento or ''}"),
                "conciliado": False,
                "match": None,
                "score": 0,
                "motivo": None,
            }
        )

    if not movimentos:
        raise HTTPException(
            status_code=400,
            detail="Nenhum movimento válido encontrado no OFX.",
        )

    movimentos.sort(
        key=lambda item: (
            item["data"],
            item["tipo"],
            item["descricao"] or "",
        )
    )

    return movimentos


def _extrair_tag_ofx(bloco: str, tag: str) -> str | None:
    padrao_fechado = re.search(rf"<{tag}>(.*?)</{tag}>", bloco, flags=re.I | re.S)

    if padrao_fechado:
        return padrao_fechado.group(1).strip()

    padrao_aberto = re.search(rf"<{tag}>([^\n\r<]+)", bloco, flags=re.I)

    if padrao_aberto:
        return padrao_aberto.group(1).strip()

    return None


def _parse_data_ofx(valor: Any) -> date | None:
    if not valor:
        return None

    texto = str(valor).strip()
    texto = re.sub(r"[^0-9]", "", texto)

    if len(texto) >= 8:
        try:
            return datetime.strptime(texto[:8], "%Y%m%d").date()
        except Exception:
            return None

    return None


def _pontuar_match(
    movimento_banco: dict[str, Any],
    movimento_sistema: dict[str, Any],
    tolerancia_valor: Decimal,
    tolerancia_dias: int,
) -> tuple[int, list[str]]:
    score = 0
    motivos: list[str] = []

    if movimento_banco["tipo"] != movimento_sistema["tipo"]:
        return 0, []

    diferenca_valor = abs(_decimal(movimento_banco["valor"]) - _decimal(movimento_sistema["valor"]))

    if diferenca_valor <= tolerancia_valor:
        score += 55
        motivos.append("valor compatível")
    else:
        return 0, []

    data_banco = movimento_banco["data"]
    data_sistema = movimento_sistema["data"]

    if not data_banco or not data_sistema:
        return 0, []

    diferenca_dias = abs((data_banco - data_sistema).days)

    if diferenca_dias == 0:
        score += 35
        motivos.append("mesma data")
    elif diferenca_dias <= tolerancia_dias:
        score += max(8, 28 - (diferenca_dias * 5))
        motivos.append(f"data próxima ({diferenca_dias} dia(s))")
    else:
        return 0, []

    texto_banco = movimento_banco.get("texto_busca") or ""
    texto_sistema = movimento_sistema.get("texto_busca") or ""

    palavras_banco = set(palavra for palavra in texto_banco.split() if len(palavra) >= 4)
    palavras_sistema = set(palavra for palavra in texto_sistema.split() if len(palavra) >= 4)

    intersecao = palavras_banco.intersection(palavras_sistema)

    if intersecao:
        bonus = min(10, len(intersecao) * 3)
        score += bonus
        motivos.append("descrição semelhante")

    return min(score, 100), motivos


def _conciliar_movimentos(
    movimentos_banco: list[dict[str, Any]],
    movimentos_sistema: list[dict[str, Any]],
    tolerancia_valor: Decimal,
    tolerancia_dias: int,
) -> dict[str, Any]:
    ids_sistema_usados: set[str] = set()
    conciliados = []
    pendentes_banco = []

    for movimento_banco in movimentos_banco:
        melhor_match = None
        melhor_score = 0
        melhor_motivos: list[str] = []

        for movimento_sistema in movimentos_sistema:
            chave_sistema = f"{movimento_sistema['origem']}:{movimento_sistema['id']}"

            if chave_sistema in ids_sistema_usados:
                continue

            score, motivos = _pontuar_match(
                movimento_banco=movimento_banco,
                movimento_sistema=movimento_sistema,
                tolerancia_valor=tolerancia_valor,
                tolerancia_dias=tolerancia_dias,
            )

            if score > melhor_score:
                melhor_score = score
                melhor_match = movimento_sistema
                melhor_motivos = motivos

        item_banco = _serializar_movimento_banco(movimento_banco)

        if melhor_match and melhor_score >= 75:
            chave_sistema = f"{melhor_match['origem']}:{melhor_match['id']}"
            ids_sistema_usados.add(chave_sistema)

            conciliados.append(
                {
                    "banco": item_banco,
                    "sistema": _serializar_movimento_sistema(melhor_match),
                    "score": melhor_score,
                    "motivo": ", ".join(melhor_motivos),
                }
            )
        else:
            sugestoes = _buscar_sugestoes(
                movimento_banco=movimento_banco,
                movimentos_sistema=movimentos_sistema,
                ids_sistema_usados=ids_sistema_usados,
                tolerancia_valor=tolerancia_valor,
                tolerancia_dias=tolerancia_dias,
            )

            item_banco["sugestoes"] = sugestoes
            pendentes_banco.append(item_banco)

    pendentes_sistema = []

    for movimento_sistema in movimentos_sistema:
        chave_sistema = f"{movimento_sistema['origem']}:{movimento_sistema['id']}"

        if chave_sistema not in ids_sistema_usados:
            pendentes_sistema.append(_serializar_movimento_sistema(movimento_sistema))

    total_banco_entradas = sum(
        (_decimal(item["valor"]) for item in movimentos_banco if item["tipo"] == "ENTRADA"),
        Decimal("0.00"),
    )
    total_banco_saidas = sum(
        (_decimal(item["valor"]) for item in movimentos_banco if item["tipo"] == "SAIDA"),
        Decimal("0.00"),
    )
    total_sistema_entradas = sum(
        (_decimal(item["valor"]) for item in movimentos_sistema if item["tipo"] == "ENTRADA"),
        Decimal("0.00"),
    )
    total_sistema_saidas = sum(
        (_decimal(item["valor"]) for item in movimentos_sistema if item["tipo"] == "SAIDA"),
        Decimal("0.00"),
    )

    return {
        "resumo": {
            "movimentos_banco": len(movimentos_banco),
            "movimentos_sistema": len(movimentos_sistema),
            "conciliados": len(conciliados),
            "pendentes_banco": len(pendentes_banco),
            "pendentes_sistema": len(pendentes_sistema),
            "total_banco_entradas": _float(total_banco_entradas),
            "total_banco_saidas": _float(total_banco_saidas),
            "total_sistema_entradas": _float(total_sistema_entradas),
            "total_sistema_saidas": _float(total_sistema_saidas),
            "diferenca_entradas": _float(total_banco_entradas - total_sistema_entradas),
            "diferenca_saidas": _float(total_banco_saidas - total_sistema_saidas),
        },
        "conciliados": conciliados,
        "pendentes_banco": pendentes_banco,
        "pendentes_sistema": pendentes_sistema,
    }


def _buscar_sugestoes(
    movimento_banco: dict[str, Any],
    movimentos_sistema: list[dict[str, Any]],
    ids_sistema_usados: set[str],
    tolerancia_valor: Decimal,
    tolerancia_dias: int,
) -> list[dict[str, Any]]:
    sugestoes = []

    for movimento_sistema in movimentos_sistema:
        chave_sistema = f"{movimento_sistema['origem']}:{movimento_sistema['id']}"

        if chave_sistema in ids_sistema_usados:
            continue

        score, motivos = _pontuar_match(
            movimento_banco=movimento_banco,
            movimento_sistema=movimento_sistema,
            tolerancia_valor=tolerancia_valor * Decimal("3"),
            tolerancia_dias=tolerancia_dias + 3,
        )

        if score >= 50:
            sugestoes.append(
                {
                    "sistema": _serializar_movimento_sistema(movimento_sistema),
                    "score": score,
                    "motivo": ", ".join(motivos),
                }
            )

    sugestoes.sort(key=lambda item: item["score"], reverse=True)
    return sugestoes[:3]


def _serializar_movimento_banco(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "linha": item.get("linha"),
        "data": item.get("data_iso"),
        "tipo": item.get("tipo"),
        "descricao": item.get("descricao"),
        "documento": item.get("documento"),
        "valor": _float(item.get("valor")),
        "valor_original": _float(item.get("valor_original")),
    }


def _serializar_movimento_sistema(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "origem": item.get("origem"),
        "id": item.get("id"),
        "tipo": item.get("tipo"),
        "data": item.get("data_iso"),
        "descricao": item.get("descricao"),
        "pessoa": item.get("pessoa"),
        "forma_pagamento": item.get("forma_pagamento"),
        "valor": _float(item.get("valor")),
        "status": item.get("status"),
    }


def _periodo_do_arquivo(movimentos: list[dict[str, Any]]) -> tuple[date, date]:
    datas = [item["data"] for item in movimentos if item.get("data")]

    if not datas:
        hoje = date.today()
        return hoje, hoje

    return min(datas), max(datas)


def _gerar_modelo_csv() -> BytesIO:
    linhas = [
        ["Data", "Descrição", "Valor", "Documento"],
        [date.today().strftime("%d/%m/%Y"), "Exemplo de entrada PIX", "150,00", "PIX123"],
        [date.today().strftime("%d/%m/%Y"), "Exemplo de saída fornecedor", "-80,00", "PAG456"],
    ]

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\n")
    writer.writerows(linhas)

    conteudo = "\ufeff" + buffer.getvalue()
    output = BytesIO(conteudo.encode("utf-8"))
    output.seek(0)
    return output


def _processar_conciliacao(
    db: Session,
    empresa_id: int,
    movimentos_banco: list[dict[str, Any]],
    data_inicio: date | None,
    data_fim: date | None,
    tolerancia_centavos: int,
    tolerancia_dias: int,
) -> dict[str, Any]:
    periodo_inicio_arquivo, periodo_fim_arquivo = _periodo_do_arquivo(movimentos_banco)

    inicio = data_inicio or periodo_inicio_arquivo
    fim = data_fim or periodo_fim_arquivo

    margem_inicio = inicio - timedelta(days=max(tolerancia_dias, 0))
    margem_fim = fim + timedelta(days=max(tolerancia_dias, 0))

    movimentos_sistema = _consultar_financeiro_realizado(
        db=db,
        empresa_id=empresa_id,
        data_inicio=margem_inicio,
        data_fim=margem_fim,
    )

    tolerancia_valor = Decimal(tolerancia_centavos) / Decimal("100")

    resultado = _conciliar_movimentos(
        movimentos_banco=movimentos_banco,
        movimentos_sistema=movimentos_sistema,
        tolerancia_valor=tolerancia_valor,
        tolerancia_dias=tolerancia_dias,
    )

    resultado["empresa_id"] = empresa_id
    resultado["data_inicio"] = inicio.isoformat()
    resultado["data_fim"] = fim.isoformat()
    resultado["periodo_arquivo"] = {
        "data_inicio": periodo_inicio_arquivo.isoformat(),
        "data_fim": periodo_fim_arquivo.isoformat(),
    }
    resultado["parametros"] = {
        "tolerancia_centavos": tolerancia_centavos,
        "tolerancia_valor": _float(tolerancia_valor),
        "tolerancia_dias": tolerancia_dias,
    }

    return resultado


@router.get("/modelo-csv")
def baixar_modelo_csv():
    arquivo = _gerar_modelo_csv()

    return StreamingResponse(
        arquivo,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="modelo_conciliacao_bancaria.csv"'
        },
    )


@router.post("/importar-csv")
def importar_csv_conciliacao_bancaria(
    empresa_id: int = Query(..., ge=1),
    data_inicio: date | None = Query(None),
    data_fim: date | None = Query(None),
    tolerancia_centavos: int = Query(2, ge=0, le=10000),
    tolerancia_dias: int = Query(2, ge=0, le=30),
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    nome_arquivo = arquivo.filename or ""

    if not nome_arquivo.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Envie um arquivo CSV.",
        )

    texto = _ler_upload_texto(arquivo)
    movimentos_banco = _parse_csv(texto)

    return _processar_conciliacao(
        db=db,
        empresa_id=empresa_id,
        movimentos_banco=movimentos_banco,
        data_inicio=data_inicio,
        data_fim=data_fim,
        tolerancia_centavos=tolerancia_centavos,
        tolerancia_dias=tolerancia_dias,
    )


@router.post("/importar-ofx")
def importar_ofx_conciliacao_bancaria(
    empresa_id: int = Query(..., ge=1),
    data_inicio: date | None = Query(None),
    data_fim: date | None = Query(None),
    tolerancia_centavos: int = Query(2, ge=0, le=10000),
    tolerancia_dias: int = Query(2, ge=0, le=30),
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    nome_arquivo = arquivo.filename or ""

    if not nome_arquivo.lower().endswith((".ofx", ".qfx")):
        raise HTTPException(
            status_code=400,
            detail="Envie um arquivo OFX ou QFX.",
        )

    texto = _ler_upload_texto(arquivo)
    movimentos_banco = _parse_ofx(texto)

    return _processar_conciliacao(
        db=db,
        empresa_id=empresa_id,
        movimentos_banco=movimentos_banco,
        data_inicio=data_inicio,
        data_fim=data_fim,
        tolerancia_centavos=tolerancia_centavos,
        tolerancia_dias=tolerancia_dias,
    )


@router.get("/financeiro-realizado")
def listar_financeiro_realizado_para_conciliacao(
    empresa_id: int = Query(..., ge=1),
    data_inicio: date | None = Query(None),
    data_fim: date | None = Query(None),
    db: Session = Depends(get_db),
):
    hoje = date.today()
    inicio = data_inicio or hoje.replace(day=1)
    fim = data_fim or hoje

    if fim < inicio:
        raise HTTPException(
            status_code=400,
            detail="A data final não pode ser menor que a data inicial.",
        )

    movimentos = _consultar_financeiro_realizado(
        db=db,
        empresa_id=empresa_id,
        data_inicio=inicio,
        data_fim=fim,
    )

    entradas = sum(
        (_decimal(item["valor"]) for item in movimentos if item["tipo"] == "ENTRADA"),
        Decimal("0.00"),
    )
    saidas = sum(
        (_decimal(item["valor"]) for item in movimentos if item["tipo"] == "SAIDA"),
        Decimal("0.00"),
    )

    return {
        "empresa_id": empresa_id,
        "data_inicio": inicio.isoformat(),
        "data_fim": fim.isoformat(),
        "resumo": {
            "movimentos": len(movimentos),
            "entradas": _float(entradas),
            "saidas": _float(saidas),
            "saldo": _float(entradas - saidas),
        },
        "movimentos": [_serializar_movimento_sistema(item) for item in movimentos],
    }
