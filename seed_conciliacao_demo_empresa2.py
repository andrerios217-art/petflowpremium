from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.financeiro_pagar import FinanceiroPagar
from app.models.financeiro_receber import FinanceiroReceber


EMPRESA_ID = 2
PREFIXO_DEMO = "[DEMO CONCILIAÇÃO]"


MOVIMENTOS_DEMO = [
    {"data": date(2025, 12, 31), "tipo": "SAIDA", "valor": Decimal("73.50"), "descricao_banco": "Pix 99 Food"},
    {"data": date(2025, 12, 31), "tipo": "ENTRADA", "valor": Decimal("115.27"), "descricao_banco": "Recebível de cartão"},
    {"data": date(2025, 12, 31), "tipo": "ENTRADA", "valor": Decimal("373.29"), "descricao_banco": "Transferência Stone"},
    {"data": date(2025, 12, 30), "tipo": "SAIDA", "valor": Decimal("12.00"), "descricao_banco": "Pix André"},
    {"data": date(2025, 12, 30), "tipo": "SAIDA", "valor": Decimal("500.00"), "descricao_banco": "Pix colaborador 1"},
    {"data": date(2025, 12, 30), "tipo": "ENTRADA", "valor": Decimal("135.00"), "descricao_banco": "Transação cliente"},
    {"data": date(2025, 12, 30), "tipo": "ENTRADA", "valor": Decimal("99.90"), "descricao_banco": "Pix cliente"},
    {"data": date(2025, 12, 30), "tipo": "SAIDA", "valor": Decimal("410.00"), "descricao_banco": "Mobile Vet"},
    {"data": date(2025, 12, 30), "tipo": "SAIDA", "valor": Decimal("101.58"), "descricao_banco": "Ifood"},
    {"data": date(2025, 12, 30), "tipo": "SAIDA", "valor": Decimal("36.00"), "descricao_banco": "Material construção"},
    {"data": date(2025, 12, 30), "tipo": "SAIDA", "valor": Decimal("156.51"), "descricao_banco": "Drogasil"},
    {"data": date(2025, 12, 30), "tipo": "ENTRADA", "valor": Decimal("200.20"), "descricao_banco": "Recebível cartão"},
    {"data": date(2025, 12, 30), "tipo": "ENTRADA", "valor": Decimal("66.90"), "descricao_banco": "Recebível cartão"},
    {"data": date(2025, 12, 30), "tipo": "SAIDA", "valor": Decimal("313.01"), "descricao_banco": "Auto posto"},
    {"data": date(2025, 12, 30), "tipo": "SAIDA", "valor": Decimal("35.50"), "descricao_banco": "Auto posto"},
    {"data": date(2025, 12, 29), "tipo": "ENTRADA", "valor": Decimal("250.00"), "descricao_banco": "Entrada cliente"},
]


def colunas_modelo(modelo):
    return {coluna.name: coluna for coluna in modelo.__table__.columns}


def tabela_existe(db: Session, nome_tabela: str) -> bool:
    bind = db.get_bind()
    inspector = inspect(bind)
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

    where = ""
    params = {"empresa_id": EMPRESA_ID}

    if filtros:
        where = "where " + " and ".join(filtros)

    row = db.execute(
        text(f"select id from financeiro_plano_dre {where} order by id limit 1"),
        params,
    ).first()

    return row[0] if row else None


def preencher_campos_obrigatorios(modelo, dados: dict):
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


def montar_dados_comuns(modelo, movimento: dict, descricao: str, data_pagamento: date):
    colunas = colunas_modelo(modelo)
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
        dados["observacao"] = "Registro criado para testar conciliação bancária por sugestão."

    if "observacao_baixa" in colunas:
        dados["observacao_baixa"] = "Baixa demo criada para teste da conciliação."

    return dados


def limpar_demo_anterior(db: Session):
    for modelo in [FinanceiroPagar, FinanceiroReceber]:
        colunas = colunas_modelo(modelo)

        if "descricao" not in colunas or "empresa_id" not in colunas:
            continue

        db.query(modelo).filter(
            modelo.empresa_id == EMPRESA_ID,
            modelo.descricao.like(f"{PREFIXO_DEMO}%"),
        ).delete(synchronize_session=False)

    db.commit()


def criar_saidas(db: Session):
    dre_id = primeiro_dre_id(db)
    fornecedor_padrao = "Fornecedor Demo Conciliação"

    total = 0

    for idx, movimento in enumerate([m for m in MOVIMENTOS_DEMO if m["tipo"] == "SAIDA"], start=1):
        data_pagamento = movimento["data"] + timedelta(days=2)
        descricao = f"{PREFIXO_DEMO} Saída {idx:02d} - {movimento['descricao_banco']}"

        dados = montar_dados_comuns(
            modelo=FinanceiroPagar,
            movimento=movimento,
            descricao=descricao,
            data_pagamento=data_pagamento,
        )

        colunas = colunas_modelo(FinanceiroPagar)

        if "fornecedor" in colunas:
            dados["fornecedor"] = fornecedor_padrao

        if "classificacao_dre_id" in colunas and dre_id:
            dados["classificacao_dre_id"] = dre_id

        dados = preencher_campos_obrigatorios(FinanceiroPagar, dados)

        db.add(FinanceiroPagar(**dados))
        total += 1

    return total


def criar_entradas(db: Session):
    cliente_id = primeiro_id(db, "clientes", EMPRESA_ID)
    total = 0

    for idx, movimento in enumerate([m for m in MOVIMENTOS_DEMO if m["tipo"] == "ENTRADA"], start=1):
        data_pagamento = movimento["data"] + timedelta(days=2)
        descricao = f"{PREFIXO_DEMO} Entrada {idx:02d} - {movimento['descricao_banco']}"

        dados = montar_dados_comuns(
            modelo=FinanceiroReceber,
            movimento=movimento,
            descricao=descricao,
            data_pagamento=data_pagamento,
        )

        colunas = colunas_modelo(FinanceiroReceber)

        if "cliente_id" in colunas and cliente_id:
            dados["cliente_id"] = cliente_id

        if "cliente_nome" in colunas:
            dados["cliente_nome"] = "Cliente Demo Conciliação"

        dados = preencher_campos_obrigatorios(FinanceiroReceber, dados)

        db.add(FinanceiroReceber(**dados))
        total += 1

    return total


def main():
    db = SessionLocal()

    try:
        limpar_demo_anterior(db)

        total_saidas = criar_saidas(db)
        total_entradas = criar_entradas(db)

        db.commit()

        print("Seed da conciliação criado com sucesso.")
        print(f"Empresa: {EMPRESA_ID}")
        print(f"Entradas criadas: {total_entradas}")
        print(f"Saídas criadas: {total_saidas}")
        print("")
        print("Para ver sugestões:")
        print("1. Abra /conciliacao-bancaria")
        print("2. Use Empresa 2")
        print("3. Coloque data inicial 01/12/2025")
        print("4. Coloque data final 31/12/2025")
        print("5. Tolerância em dias: 2")
        print("6. Processe o CSV enviado")
        print("")
        print("O botão Conciliar sugeridos deve liberar se as sugestões forem encontradas.")

    except Exception as exc:
        db.rollback()
        print("Erro ao criar seed da conciliação:")
        print(repr(exc))
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
