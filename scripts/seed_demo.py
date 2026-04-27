
from __future__ import annotations

import random
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import inspect, text

from app.core.database import SessionLocal
from app.models.empresa import Empresa
from app.models.cliente import Cliente
from app.models.pet import Pet
from app.models.produto import Produto
from app.models.servico import Servico
from app.models.pdv_venda import PdvVenda
from app.models.pdv_venda_item import PdvVendaItem
from app.models.pdv_pagamento import PdvPagamento
from app.models.estoque_saldo import EstoqueSaldo


DEMO_EMPRESA_NOME = "VectorPet Demo"
DEMO_CNPJ = "00.000.000/0001-00"


def agora():
    return datetime.now(timezone.utc)


def dinheiro(valor):
    return Decimal(str(valor)).quantize(Decimal("0.01"))


def limpar_empresa_demo(db, empresa_id: int):
    print("Limpando dados antigos da empresa demo...")

    venda_ids = [
        row[0]
        for row in db.execute(
            text("SELECT id FROM pdv_vendas WHERE empresa_id = :empresa_id"),
            {"empresa_id": empresa_id},
        ).fetchall()
    ]

    if venda_ids:
        db.query(PdvPagamento).filter(PdvPagamento.venda_id.in_(venda_ids)).delete(synchronize_session=False)
        db.query(PdvVendaItem).filter(PdvVendaItem.venda_id.in_(venda_ids)).delete(synchronize_session=False)
        db.query(PdvVenda).filter(PdvVenda.id.in_(venda_ids)).delete(synchronize_session=False)

    db.query(Pet).filter(Pet.empresa_id == empresa_id).delete(synchronize_session=False)
    db.query(Cliente).filter(Cliente.empresa_id == empresa_id).delete(synchronize_session=False)
    db.query(Servico).filter(Servico.empresa_id == empresa_id).delete(synchronize_session=False)
    db.query(EstoqueSaldo).filter(EstoqueSaldo.empresa_id == empresa_id).delete(synchronize_session=False)
    db.query(Produto).filter(Produto.empresa_id == empresa_id).delete(synchronize_session=False)

    inspector = inspect(db.bind)
    if "caixa_sessoes" in inspector.get_table_names():
        db.execute(text("DELETE FROM caixa_sessoes WHERE empresa_id = :empresa_id"), {"empresa_id": empresa_id})

    db.commit()


def get_or_create_empresa_demo(db):
    empresa = db.query(Empresa).filter(Empresa.cnpj == DEMO_CNPJ).first()

    if not empresa:
        empresa = Empresa(
            nome=DEMO_EMPRESA_NOME,
            cnpj=DEMO_CNPJ,
            razao_social="VectorPet Demo LTDA",
            nome_fantasia="VectorPet Demo",
            telefone="(11) 99999-0000",
            email="demo@vectorpet.local",
            cidade="S?o Paulo",
            uf="SP",
            endereco_loja="Rua Demo, 123 - Centro - S?o Paulo/SP",
            ativa=True,
        )
        db.add(empresa)
        db.commit()
        db.refresh(empresa)

    limpar_empresa_demo(db, empresa.id)
    return empresa


def criar_clientes(db, empresa_id: int):
    nomes = [
        "Ana Martins", "Bruno Almeida", "Carla Souza", "Diego Lima", "Eduarda Rocha",
        "Felipe Santos", "Giovana Mendes", "Henrique Costa", "Isabela Ferreira", "Jo?o Pereira",
        "Larissa Gomes", "Marcelo Ribeiro", "Nat?lia Barbosa", "Ot?vio Nunes", "Paula Teixeira",
        "Rafael Cardoso", "Sabrina Melo", "Thiago Vieira", "Vanessa Lopes", "William Castro",
        "Camila Duarte", "Leonardo Ramos", "Mariana Azevedo", "Pedro Moreira", "Renata Freitas",
        "Lucas Andrade", "Beatriz Oliveira", "Daniel Correia", "Fernanda Batista", "Gustavo Martins",
    ]

    clientes = []

    for idx, nome in enumerate(nomes, start=1):
        cliente = Cliente(
            empresa_id=empresa_id,
            nome=nome,
            cpf=f"900.000.0{idx:02d}-00",
            email=f"cliente{idx}@demo.local",
            telefone=f"(11) 9{idx:04d}-{idx:04d}",
            ativo=True,
            saldo_cashback=dinheiro(random.choice([0, 5, 10, 15, 25])),
        )
        db.add(cliente)
        clientes.append(cliente)

    db.commit()

    for cliente in clientes:
        db.refresh(cliente)

    return clientes


def criar_pets(db, empresa_id: int, clientes):
    nomes_pet = [
        "Mel", "Thor", "Luna", "Bob", "Nina", "Max", "Amora", "Toby", "Belinha", "Simba",
        "Maya", "Theo", "Pandora", "Billy", "Meg", "Fred", "Jade", "Luke", "Pipoca", "Sushi",
    ]

    racas = ["Shih-tzu", "Spitz", "SRD", "Poodle", "Golden", "Yorkshire", "Bulldog", "Lhasa Apso", "Gato SRD"]
    portes = ["P", "M", "G"]

    pets = []

    for idx, cliente in enumerate(clientes, start=1):
        quantidade = random.choice([1, 1, 1, 2])

        for n in range(quantidade):
            pet = Pet(
                empresa_id=empresa_id,
                cliente_id=cliente.id,
                nome=random.choice(nomes_pet) + f" {idx}" if n else random.choice(nomes_pet),
                nascimento=date.today() - timedelta(days=random.randint(180, 3650)),
                raca=random.choice(racas),
                sexo=random.choice(["MACHO", "FEMEA"]),
                temperamento=random.choice(["CALMO", "NORMAL", "AGITADO"]),
                peso=dinheiro(random.uniform(2.5, 32.0)),
                porte=random.choice(portes),
                observacoes=random.choice([None, "Cliente prefere buscar no fim do dia.", "Pet sens?vel a barulho."]),
                pode_perfume=random.choice([True, True, False]),
                pode_acessorio=random.choice([True, True, False]),
                castrado=random.choice([True, False]),
                ativo=True,
            )
            db.add(pet)
            pets.append(pet)

    db.commit()

    for pet in pets:
        db.refresh(pet)

    return pets


def criar_produtos(db, empresa_id: int):
    produtos_base = [
        ("RACAO-CAO-001", "Ra??o Golden C?es Adultos 10kg", 159.90, 104.00, 4),
        ("RACAO-CAO-002", "Ra??o Premier C?es Filhotes 10kg", 219.90, 152.00, 3),
        ("RACAO-GATO-001", "Ra??o GranPlus Gatos Castrados 10kg", 189.90, 130.00, 3),
        ("PETISCO-001", "Petisco Bifinho Carne 500g", 29.90, 14.50, 10),
        ("PETISCO-002", "Sach? Gato Frango 85g", 4.90, 2.60, 30),
        ("HIGIENE-001", "Tapete Higi?nico 30 unidades", 79.90, 43.00, 8),
        ("HIGIENE-002", "Areia Sanit?ria 4kg", 24.90, 12.00, 12),
        ("BRINQ-001", "Bola Maci?a Pet", 18.90, 7.50, 10),
        ("BRINQ-002", "Arranhador Pequeno", 89.90, 48.00, 2),
        ("BANHO-001", "Shampoo Neutro Pet 500ml", 34.90, 16.00, 6),
        ("BANHO-002", "Condicionador Pet 500ml", 36.90, 17.00, 6),
        ("COLEIRA-001", "Coleira Nylon P", 22.90, 9.00, 8),
        ("COLEIRA-002", "Coleira Nylon M", 26.90, 11.00, 8),
        ("COLEIRA-003", "Guia Refor?ada", 39.90, 18.00, 6),
        ("MED-001", "Verm?fugo C?es Pequenos", 42.90, 23.00, 5),
        ("MED-002", "Antipulgas Spot On", 74.90, 41.00, 5),
    ]

    produtos = []

    for sku, nome, venda, custo, minimo in produtos_base:
        produto = Produto(
            empresa_id=empresa_id,
            sku=sku,
            nome=nome,
            descricao=f"Produto demo: {nome}",
            unidade="UN",
            ativo=True,
            aceita_fracionado=False,
            preco_venda_atual=dinheiro(venda),
            custo_medio_atual=Decimal(str(custo)),
            estoque_minimo=Decimal(str(minimo)),
            ncm="23091000",
            cfop_padrao="5102",
            origem_fiscal="0",
        )
        db.add(produto)
        produtos.append(produto)

    db.commit()

    for produto in produtos:
        db.refresh(produto)

    return produtos


def criar_servicos(db, empresa_id: int):
    servicos_base = [
        ("Banho pequeno porte", "PETSHOP", "P", 18.00, 55.00, 50),
        ("Banho m?dio porte", "PETSHOP", "M", 24.00, 75.00, 70),
        ("Banho grande porte", "PETSHOP", "G", 34.00, 110.00, 90),
        ("Tosa higi?nica", "PETSHOP", "M", 20.00, 65.00, 45),
        ("Tosa completa", "PETSHOP", "M", 35.00, 120.00, 120),
        ("Hidrata??o", "PETSHOP", "M", 18.00, 60.00, 40),
        ("Consulta veterin?ria", "VETERINARIO", "M", 45.00, 140.00, 40),
        ("Vacina V10", "VETERINARIO", "M", 55.00, 120.00, 20),
        ("Vacina Antirr?bica", "VETERINARIO", "M", 35.00, 90.00, 20),
        ("Exame cl?nico simples", "VETERINARIO", "M", 30.00, 100.00, 30),
    ]

    servicos = []

    for nome, tipo, porte, custo, venda, tempo in servicos_base:
        servico = Servico(
            empresa_id=empresa_id,
            nome=nome,
            tipo_servico=tipo,
            porte_referencia=porte,
            custo=dinheiro(custo),
            venda=dinheiro(venda),
            tempo_minutos=tempo,
            ativo=True,
        )
        db.add(servico)
        servicos.append(servico)

    db.commit()

    for servico in servicos:
        db.refresh(servico)

    return servicos



def criar_deposito_demo(db, empresa_id: int):
    inspector = inspect(db.bind)

    if "estoque_depositos" not in inspector.get_table_names():
        raise RuntimeError("Tabela estoque_depositos n?o encontrada.")

    existente = db.execute(
        text("SELECT id FROM estoque_depositos WHERE empresa_id = :empresa_id ORDER BY id ASC LIMIT 1"),
        {"empresa_id": empresa_id},
    ).scalar()

    if existente:
        return existente

    colunas = {col["name"]: col for col in inspector.get_columns("estoque_depositos")}
    dados = {}

    def set_if_coluna(nome, valor):
        if nome in colunas:
            dados[nome] = valor

    set_if_coluna("empresa_id", empresa_id)
    set_if_coluna("nome", "Dep?sito Demo")
    set_if_coluna("descricao", "Dep?sito fict?cio para testes da IA de compras.")
    set_if_coluna("ativo", True)
    set_if_coluna("padrao", True)
    set_if_coluna("created_at", agora())
    set_if_coluna("updated_at", agora())

    for nome, col in colunas.items():
        if nome == "id" or nome in dados:
            continue

        if not col.get("nullable", True) and col.get("default") is None:
            tipo = str(col.get("type", "")).upper()

            if "INT" in tipo:
                dados[nome] = 0
            elif "NUMERIC" in tipo or "DECIMAL" in tipo:
                dados[nome] = Decimal("0.00")
            elif "BOOL" in tipo:
                dados[nome] = True
            elif "DATE" in tipo or "TIME" in tipo:
                dados[nome] = agora()
            else:
                dados[nome] = "DEMO"

    colunas_insert = ", ".join(dados.keys())
    valores_insert = ", ".join(f":{key}" for key in dados.keys())

    result = db.execute(
        text(f"INSERT INTO estoque_depositos ({colunas_insert}) VALUES ({valores_insert}) RETURNING id"),
        dados,
    )

    deposito_id = result.scalar()
    db.commit()

    return deposito_id


def criar_saldos_estoque_demo(db, empresa_id: int, produtos):
    deposito_id = criar_deposito_demo(db, empresa_id)

    faixas = [
        (0, 2),    # ruptura/quase sem estoque
        (3, 8),    # baixo
        (9, 20),   # m?dio
        (21, 45),  # confort?vel
    ]

    saldos_criados = 0

    for produto in produtos:
        minimo = int(Decimal(str(produto.estoque_minimo or 0)))
        faixa = random.choices(faixas, weights=[25, 35, 30, 10])[0]

        quantidade = random.randint(faixa[0], faixa[1])

        # Alguns produtos ficam abaixo do m?nimo para testar sugest?o de compra.
        if random.random() < 0.45:
            quantidade = max(0, minimo - random.randint(0, max(1, minimo + 3)))

        saldo = EstoqueSaldo(
            empresa_id=empresa_id,
            deposito_id=deposito_id,
            produto_id=produto.id,
            quantidade_atual=Decimal(str(quantidade)),
        )

        if hasattr(saldo, "created_at"):
            saldo.created_at = agora()
        if hasattr(saldo, "updated_at"):
            saldo.updated_at = agora()

        db.add(saldo)
        saldos_criados += 1

    db.commit()
    return saldos_criados


def criar_caixa_demo(db, empresa_id: int):
    inspector = inspect(db.bind)
    if "caixa_sessoes" not in inspector.get_table_names():
        raise RuntimeError("Tabela caixa_sessoes n?o encontrada.")

    usuario_id = db.execute(text("SELECT id FROM usuarios ORDER BY id ASC LIMIT 1")).scalar()
    if not usuario_id:
        raise RuntimeError(
            "Nenhum usu?rio encontrado. Crie ao menos um usu?rio antes de rodar o seed demo."
        )

    colunas = {col["name"]: col for col in inspector.get_columns("caixa_sessoes")}
    dados = {}

    def set_if_coluna(nome, valor):
        if nome in colunas:
            dados[nome] = valor

    set_if_coluna("empresa_id", empresa_id)
    set_if_coluna("usuario_responsavel_id", usuario_id)
    set_if_coluna("usuario_abertura_id", usuario_id)
    set_if_coluna("usuario_fechamento_id", usuario_id)
    set_if_coluna("status", "FECHADO")
    set_if_coluna("valor_abertura_informado", Decimal("300.00"))
    set_if_coluna("valor_referencia_anterior", Decimal("0.00"))
    set_if_coluna("diferenca_abertura", Decimal("0.00"))
    set_if_coluna("valor_fechamento_esperado", Decimal("300.00"))
    set_if_coluna("valor_fechamento_informado", Decimal("300.00"))
    set_if_coluna("saldo_dinheiro_esperado", Decimal("300.00"))
    set_if_coluna("observacoes", "Caixa demo para seed de vendas fict?cias.")
    set_if_coluna("aberto_em", agora() - timedelta(days=365))
    set_if_coluna("fechado_em", agora())
    set_if_coluna("created_at", agora() - timedelta(days=365))
    set_if_coluna("updated_at", agora())

    for nome, col in colunas.items():
        if nome == "id" or nome in dados:
            continue

        if not col.get("nullable", True) and col.get("default") is None:
            tipo = str(col.get("type", "")).upper()

            if "usuario" in nome:
                dados[nome] = usuario_id
            elif "gerente" in nome:
                dados[nome] = usuario_id
            elif "INT" in tipo:
                dados[nome] = 0
            elif "NUMERIC" in tipo or "DECIMAL" in tipo:
                dados[nome] = Decimal("0.00")
            elif "BOOL" in tipo:
                dados[nome] = False
            elif "DATE" in tipo or "TIME" in tipo:
                dados[nome] = agora()
            else:
                dados[nome] = "DEMO"

    colunas_insert = ", ".join(dados.keys())
    valores_insert = ", ".join(f":{key}" for key in dados.keys())

    result = db.execute(
        text(f"INSERT INTO caixa_sessoes ({colunas_insert}) VALUES ({valores_insert}) RETURNING id"),
        dados,
    )

    caixa_id = result.scalar()
    db.commit()

    return caixa_id


def gerar_numero_venda(venda_id: int):
    return f"DEMO-{venda_id:06d}"


def criar_vendas(db, empresa_id: int, caixa_sessao_id: int, clientes, produtos, servicos):
    formas = ["DINHEIRO", "PIX", "CARTAO_DEBITO", "CARTAO_CREDITO"]

    vendas_criadas = 0
    hoje = agora()

    for dia_offset in range(365, 0, -1):
        data_base = hoje - timedelta(days=dia_offset)

        qtd_vendas_dia = random.choices([0, 1, 2, 3, 4, 5], weights=[10, 25, 30, 20, 10, 5])[0]

        for _ in range(qtd_vendas_dia):
            cliente = random.choice(clientes)
            data_venda = data_base.replace(
                hour=random.randint(8, 19),
                minute=random.randint(0, 59),
                second=random.randint(0, 59),
                microsecond=0,
            )

            venda = PdvVenda(
                empresa_id=empresa_id,
                caixa_sessao_id=caixa_sessao_id,
                cliente_id=cliente.id,
                modo_cliente="REGISTERED_CLIENT",
                nome_cliente_snapshot=cliente.nome,
                telefone_cliente_snapshot=cliente.telefone,
                origem="PRODUCT_ONLY",
                status="ABERTA",
                subtotal=Decimal("0.00"),
                desconto_valor=Decimal("0.00"),
                acrescimo_valor=Decimal("0.00"),
                valor_total=Decimal("0.00"),
                observacoes="Venda demo gerada automaticamente.",
                aberta_em=data_venda,
                created_at=data_venda,
                updated_at=data_venda,
            )
            db.add(venda)
            db.flush()

            tem_produto = random.random() < 0.80
            tem_servico = random.random() < 0.55

            if not tem_produto and not tem_servico:
                tem_produto = True

            if tem_produto:
                for produto in random.sample(produtos, random.randint(1, min(4, len(produtos)))):
                    quantidade = Decimal(str(random.choice([1, 1, 1, 2, 3])))
                    desconto_item = Decimal("0.00")

                    item = PdvVendaItem(
                        venda_id=venda.id,
                        created_at=data_venda,
                        updated_at=data_venda,
                    )
                    item.definir_como_produto_catalogo(
                        produto_id=produto.id,
                        descricao_snapshot=produto.nome,
                        valor_unitario=produto.preco_venda_atual,
                        quantidade=quantidade,
                        desconto_valor=desconto_item,
                        observacao=None,
                        gera_movimento_estoque=True,
                    )
                    item.created_at = data_venda
                    item.updated_at = data_venda
                    db.add(item)

            if tem_servico:
                for servico in random.sample(servicos, random.randint(1, min(2, len(servicos)))):
                    item = PdvVendaItem(
                        venda_id=venda.id,
                        created_at=data_venda,
                        updated_at=data_venda,
                    )
                    item.definir_como_item_producao(
                        descricao_snapshot=servico.nome,
                        valor_unitario=servico.venda,
                        quantidade=Decimal("1.000"),
                        desconto_valor=Decimal("0.00"),
                        observacao="Servi?o demo.",
                    )
                    item.created_at = data_venda
                    item.updated_at = data_venda
                    db.add(item)

            db.flush()

            venda.recalcular_totais()

            if random.random() < 0.22:
                venda.desconto_valor = dinheiro(venda.subtotal * Decimal(str(random.choice([0.05, 0.08, 0.10]))))

            venda.recalcular_totais()
            venda.status = "FECHADA"
            venda.fechada_em = data_venda + timedelta(minutes=random.randint(3, 40))
            venda.numero_venda = gerar_numero_venda(venda.id)
            venda.updated_at = venda.fechada_em

            forma = random.choice(formas)
            parcelas = random.choice([1, 2, 3, 4]) if forma == "CARTAO_CREDITO" else 1

            pagamento = PdvPagamento(
                venda_id=venda.id,
                forma_pagamento=forma,
                valor=venda.valor_total,
                quantidade_parcelas=parcelas,
                status="RECEBIDO",
                referencia="DEMO",
                observacoes="Pagamento demo.",
                recebido_em=venda.fechada_em,
                created_at=venda.fechada_em,
                updated_at=venda.fechada_em,
            )
            db.add(pagamento)

            vendas_criadas += 1

    db.commit()
    return vendas_criadas


def main():
    random.seed(42)

    db = SessionLocal()

    try:
        empresa = get_or_create_empresa_demo(db)
        print(f"Empresa demo: {empresa.id} - {empresa.nome}")

        clientes = criar_clientes(db, empresa.id)
        print(f"Clientes criados: {len(clientes)}")

        pets = criar_pets(db, empresa.id, clientes)
        print(f"Pets criados: {len(pets)}")

        produtos = criar_produtos(db, empresa.id)
        print(f"Produtos criados: {len(produtos)}")

        saldos = criar_saldos_estoque_demo(db, empresa.id, produtos)
        print(f"Saldos de estoque criados: {saldos}")

        servicos = criar_servicos(db, empresa.id)
        print(f"Servi?os criados: {len(servicos)}")

        caixa_sessao_id = criar_caixa_demo(db, empresa.id)
        print(f"Caixa demo criado: {caixa_sessao_id}")

        vendas = criar_vendas(db, empresa.id, caixa_sessao_id, clientes, produtos, servicos)
        print(f"Vendas demo criadas: {vendas}")

        print("")
        print("Seed demo conclu?do.")
        print(f"Use empresa_id={empresa.id} nos relat?rios e no PDV para testar a base demo.")

    except Exception as error:
        db.rollback()
        print("")
        print("Erro ao gerar seed demo:")
        print(error)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
