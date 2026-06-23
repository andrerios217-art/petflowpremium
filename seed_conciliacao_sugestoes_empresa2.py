from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.financeiro_pagar import FinanceiroPagar
from app.models.financeiro_receber import FinanceiroReceber


EMPRESA_ID = 2
PREFIXO_DEMO = "[DEMO SUGESTAO CONCILIACAO]"


MOVIMENTOS = [
    {"data": date(2025, 12, 31), "tipo": "SAIDA", "valor": Decimal("73.50")},
    {"data": date(2025, 12, 31), "tipo": "ENTRADA", "valor": Decimal("115.27")},
    {"data": date(2025, 12, 31), "tipo": "ENTRADA", "valor": Decimal("373.29")},
    {"data": date(2025, 12, 30), "tipo": "SAIDA", "valor": Decimal("12.00")},
    {"data": date(2025, 12, 30), "tipo": "SAIDA", "valor": Decimal("500.00")},
    {"data": date(2025, 12, 30), "tipo": "SAIDA", "valor": Decimal("500.00")},
    {"data": date(2025, 12, 30), "tipo": "SAIDA", "valor": Decimal("500.00")},
    {"data": date(2025, 12, 30), "tipo": "ENTRADA", "valor": Decimal("135.00")},
    {"data": date(2025, 12, 30), "tipo": "ENTRADA", "valor": Decimal("99.90")},
    {"data": date(2025, 12, 30), "tipo": "SAIDA", "valor": Decimal("3.00")},
    {"data": date(2025, 12, 30), "tipo": "SAIDA", "valor": Decimal("410.00")},
    {"data": date(2025, 12, 30), "tipo": "SAIDA", "valor": Decimal("101.58")},
    {"data": date(2025, 12, 30), "tipo": "SAIDA", "valor": Decimal("36.00")},
    {"data": date(2025, 12, 30), "tipo": "SAIDA", "valor": Decimal("156.51")},
    {"data": date(2025, 12, 30), "tipo": "ENTRADA", "valor": Decimal("135.28")},
    {"data": date(2025, 12, 30), "tipo": "SAIDA", "valor": Decimal("135.28")},
    {"data": date(2025, 12, 30), "tipo": "ENTRADA", "valor": Decimal("200.20")},
    {"data": date(2025, 12, 30), "tipo": "ENTRADA", "valor": Decimal("66.90")},
    {"data": date(2025, 12, 30), "tipo": "SAIDA", "valor": Decimal("313.01")},
    {"data": date(2025, 12, 30), "tipo": "SAIDA", "valor": Decimal("35.50")},
    {"data": date(2025, 12, 29), "tipo": "SAIDA", "valor": Decimal("249.90")},
    {"data": date(2025, 12, 29), "tipo": "ENTRADA", "valor": Decimal("125.00")},
    {"data": date(2025, 12, 29), "tipo": "SAIDA", "valor": Decimal("60.00")},
    {"data": date(2025, 12, 29), "tipo": "ENTRADA", "valor": Decimal("159.90")},
    {"data": date(2025, 12, 29), "tipo": "SAIDA", "valor": Decimal("89.90")},
    {"data": date(2025, 12, 29), "tipo": "ENTRADA", "valor": Decimal("310.00")},
    {"data": date(2025, 12, 29), "tipo": "SAIDA", "valor": Decimal("99.99")},
    {"data": date(2025, 12, 28), "tipo": "ENTRADA", "valor": Decimal("80.00")},
    {"data": date(2025, 12, 28), "tipo": "SAIDA", "valor": Decimal("52.90")},
    {"data": date(2025, 12, 28), "tipo": "ENTRADA", "valor": Decimal("45.00")},
]


def colunas_modelo(modelo):
    return {coluna.name: coluna for coluna in modelo.__table__.columns}


def tabela_existe(db: Session, nome_tabela: str) -> bool:
    inspector = inspect(db.get_bind())
    return nome_tabela in inspector.get_table_names()


def primeiro_id(db: Session, tabela: str, empresa_id: int | None = None):
    if not tabela_existe(db, tabela):
        return None

    inspector = inspect(db.get_bind())
    colunas = {coluna["name"] for coluna in inspector.get_columns(tabela)}

    if empresa_id and "empresa_id" in colunas:
        row = db.execute(
            text(f"select id from {tabela} where empresa_id = :empresa_id order by id limit 1"),
            {"empresa_id": empresa_id},
        ).first()

        if row:
            return row[0]

    row = db.execute(text(f"select id from {tabela} order by id limit 1")).first()
    return row[0] if row else None


def primeiro_dre_id(db: Session):
    if not tabela_existe(db, "financeiro_plano_dre"):
        return None

    inspector = inspect(db.get_bind())
    colunas = {coluna["name"] for coluna in inspector.get_columns("financeiro_plano_dre")}
    filtros = []

    if "empresa_id" in colunas:
        filtros.append("(empresa_id = :empresa_id or empresa_id is null)")

    if "ativo" in colunas:
        filtros.append("(ativo = true or ativo is null)")

    where = "where " + " and ".join(filtros) if filtros else ""

    row = db.execute(
        text(f"select id from financeiro_plano_dre {where} order by id limit 1"),
        {"empresa_id": EMPRESA_ID},
    ).first()

    return row[0] if row else None


def preencher_obrigatorios(modelo, dados: dict):
    colunas = colunas_modelo(modelo)

    for nome, coluna in colunas.items():
        if nome in dados:
            continue

        if coluna.primary_key:
            continue

        if coluna.nullable:
            continue

        if coluna.default is not None or coluna.server_default is not None:
            continue

        tipo = str(coluna.type).upper()

        if "DATE" in tipo:
            dados[nome] = date.today()
        elif "NUMERIC" in tipo or "DECIMAL" in tipo or "FLOAT" in tipo:
            dados[nome] = Decimal("0.00")
        elif "INTEGER" in tipo:
            dados[nome] = 0
        elif "BOOLEAN" in tipo:
            dados[nome] = False
        else:
            dados[nome] = "DEMO"

    return dados


def dados_base(modelo, movimento: dict, descricao: str):
    colunas = colunas_modelo(modelo)
    data_pagamento = movimento["data"] + timedelta(days=2)

    dados = {}

    if "empresa_id" in colunas:
        dados["empresa_id"] = EMPRESA_ID

    if "descricao" in colunas:
        dados["descricao"] = descricao

    if "valor" in colunas:
        dados["valor"] = movimento["valor"]

    if "valor_pago" in colunas:
        dados["valor_pago"] = movimento["valor"]

    if "status" in colunas:
        dados["status"] = "PAGO"

    if "data_pagamento" in colunas:
        dados["data_pagamento"] = data_pagamento

    if "vencimento" in colunas:
        dados["vencimento"] = data_pagamento

    if "data_vencimento" in colunas:
        dados["data_vencimento"] = data_pagamento

    if "competencia" in colunas:
        dados["competencia"] = data_pagamento

    if "data_competencia" in colunas:
        dados["data_competencia"] = data_pagamento

    if "forma_pagamento" in colunas:
        dados["forma_pagamento"] = "CONTA_BANCARIA"

    if "forma_pagamento_baixa" in colunas:
        dados["forma_pagamento_baixa"] = "CONTA_BANCARIA"

    if "observacao" in colunas:
        dados["observacao"] = "Demo criada para gerar sugestão na conciliação bancária."

    if "observacao_baixa" in colunas:
        dados["observacao_baixa"] = "Baixa demo para conciliação bancária."

    return dados


def limpar_demo(db: Session):
    for modelo in [FinanceiroPagar, FinanceiroReceber]:
        colunas = colunas_modelo(modelo)

        if "empresa_id" not in colunas or "descricao" not in colunas:
            continue

        db.query(modelo).filter(
            modelo.empresa_id == EMPRESA_ID,
            modelo.descricao.like(f"{PREFIXO_DEMO}%"),
        ).delete(synchronize_session=False)

    db.commit()


def criar_saida(db: Session, movimento: dict, idx: int):
    dre_id = primeiro_dre_id(db)
    colunas = colunas_modelo(FinanceiroPagar)
    descricao = f"{PREFIXO_DEMO} SAIDA {idx:03d}"

    dados = dados_base(FinanceiroPagar, movimento, descricao)

    if "fornecedor" in colunas:
        dados["fornecedor"] = "Fornecedor Demo Sugestão"

    if "classificacao_dre_id" in colunas and dre_id:
        dados["classificacao_dre_id"] = dre_id

    dados = preencher_obrigatorios(FinanceiroPagar, dados)

    db.add(FinanceiroPagar(**dados))


def criar_entrada(db: Session, movimento: dict, idx: int):
    cliente_id = primeiro_id(db, "clientes", EMPRESA_ID)
    colunas = colunas_modelo(FinanceiroReceber)
    descricao = f"{PREFIXO_DEMO} ENTRADA {idx:03d}"

    dados = dados_base(FinanceiroReceber, movimento, descricao)

    if "cliente_id" in colunas and cliente_id:
        dados["cliente_id"] = cliente_id

    if "cliente_nome" in colunas:
        dados["cliente_nome"] = "Cliente Demo Sugestão"

    dados = preencher_obrigatorios(FinanceiroReceber, dados)

    db.add(FinanceiroReceber(**dados))


def main():
    db = SessionLocal()

    try:
        limpar_demo(db)

        entradas = 0
        saidas = 0

        for idx, movimento in enumerate(MOVIMENTOS, start=1):
            if movimento["tipo"] == "SAIDA":
                criar_saida(db, movimento, idx)
                saidas += 1
            else:
                criar_entrada(db, movimento, idx)
                entradas += 1

        db.commit()

        print("Demo de sugestões criada com sucesso.")
        print(f"Empresa: {EMPRESA_ID}")
        print(f"Entradas criadas: {entradas}")
        print(f"Saídas criadas: {saidas}")
        print("")
        print("Agora processe o extrato na tela com:")
        print("Empresa 2")
        print("Tolerância em dias 2")
        print("Tolerância em centavos 2")
        print("O botão Conciliar sugeridos deve liberar.")

    except Exception as exc:
        db.rollback()
        print("Erro ao criar demo de sugestões:")
        print(repr(exc))
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
