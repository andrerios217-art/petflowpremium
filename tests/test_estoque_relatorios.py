from app.crud import estoque as estoque_crud


def test_relatorio_posicao_resumida_json(client, monkeypatch):
    def fake_relatorio_posicao_resumida(db, empresa_id, busca=None, somente_abaixo_minimo=False):
        assert empresa_id == 1
        assert busca is None
        assert somente_abaixo_minimo is False
        return {
            "total_produtos": 2,
            "total_abaixo_minimo": 1,
            "itens": [
                {
                    "produto_id": 1,
                    "sku": "RACAO-001",
                    "nome": "Ração Premium",
                    "unidade": "UN",
                    "estoque_minimo": "5.00",
                    "saldo_total": "3.00",
                    "abaixo_minimo": True,
                },
                {
                    "produto_id": 2,
                    "sku": "AREIA-001",
                    "nome": "Areia Higiênica",
                    "unidade": "UN",
                    "estoque_minimo": "2.00",
                    "saldo_total": "8.00",
                    "abaixo_minimo": False,
                },
            ],
        }

    monkeypatch.setattr(
        estoque_crud,
        "relatorio_posicao_resumida",
        fake_relatorio_posicao_resumida,
    )

    response = client.get(
        "/api/estoque/relatorios/posicao-resumida",
        headers={"X-Empresa-Id": "1"},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["total_produtos"] == 2
    assert body["total_abaixo_minimo"] == 1
    assert len(body["itens"]) == 2
    assert body["itens"][0]["produto_id"] == 1
    assert body["itens"][0]["abaixo_minimo"] is True
    assert body["itens"][1]["produto_id"] == 2
    assert body["itens"][1]["abaixo_minimo"] is False


def test_relatorio_posicao_resumida_json_com_filtros(client, monkeypatch):
    def fake_relatorio_posicao_resumida(db, empresa_id, busca=None, somente_abaixo_minimo=False):
        assert empresa_id == 1
        assert busca == "racao"
        assert somente_abaixo_minimo is True
        return {
            "total_produtos": 1,
            "total_abaixo_minimo": 1,
            "itens": [
                {
                    "produto_id": 1,
                    "sku": "RACAO-001",
                    "nome": "Ração Premium",
                    "unidade": "UN",
                    "estoque_minimo": "5.00",
                    "saldo_total": "3.00",
                    "abaixo_minimo": True,
                }
            ],
        }

    monkeypatch.setattr(
        estoque_crud,
        "relatorio_posicao_resumida",
        fake_relatorio_posicao_resumida,
    )

    response = client.get(
        "/api/estoque/relatorios/posicao-resumida?busca=racao&somente_abaixo_minimo=true",
        headers={"X-Empresa-Id": "1"},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["total_produtos"] == 1
    assert body["total_abaixo_minimo"] == 1
    assert body["itens"][0]["sku"] == "RACAO-001"


def test_relatorio_posicao_resumida_csv(client, monkeypatch):
    csv_content = (
        "\ufeffproduto_id;sku;nome;unidade;estoque_minimo;saldo_total;abaixo_minimo\n"
        "1;RACAO-001;Ração Premium;UN;5.00;3.00;SIM\n"
    )

    def fake_gerar_csv(db, empresa_id, busca=None, somente_abaixo_minimo=False):
        assert empresa_id == 1
        assert busca is None
        assert somente_abaixo_minimo is False
        return csv_content

    monkeypatch.setattr(
        estoque_crud,
        "gerar_csv_relatorio_posicao_resumida",
        fake_gerar_csv,
    )

    response = client.get(
        "/api/estoque/relatorios/posicao-resumida.csv",
        headers={"X-Empresa-Id": "1"},
    )

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert 'attachment; filename="estoque_posicao_resumida.csv"' == response.headers["content-disposition"]
    assert response.text == csv_content


def test_relatorio_posicao_por_deposito_json(client, monkeypatch):
    def fake_relatorio_por_deposito(
        db,
        empresa_id,
        deposito_id,
        busca=None,
        somente_abaixo_minimo=False,
    ):
        assert empresa_id == 1
        assert deposito_id == 1
        assert busca is None
        assert somente_abaixo_minimo is False
        return {
            "deposito_id": 1,
            "deposito_nome": "Principal",
            "total_produtos": 2,
            "total_abaixo_minimo": 1,
            "itens": [
                {
                    "produto_id": 1,
                    "sku": "RACAO-001",
                    "nome": "Ração Premium",
                    "unidade": "UN",
                    "estoque_minimo": "5.00",
                    "quantidade": "3.00",
                    "abaixo_minimo": True,
                },
                {
                    "produto_id": 2,
                    "sku": "AREIA-001",
                    "nome": "Areia Higiênica",
                    "unidade": "UN",
                    "estoque_minimo": "2.00",
                    "quantidade": "8.00",
                    "abaixo_minimo": False,
                },
            ],
        }

    monkeypatch.setattr(
        estoque_crud,
        "relatorio_posicao_por_deposito",
        fake_relatorio_por_deposito,
    )

    response = client.get(
        "/api/estoque/relatorios/posicao-por-deposito/1",
        headers={"X-Empresa-Id": "1"},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["deposito_id"] == 1
    assert body["deposito_nome"] == "Principal"
    assert body["total_produtos"] == 2
    assert body["total_abaixo_minimo"] == 1
    assert len(body["itens"]) == 2


def test_relatorio_posicao_por_deposito_csv(client, monkeypatch):
    csv_content = (
        "\ufeffdeposito_id;deposito_nome;produto_id;sku;nome;unidade;estoque_minimo;quantidade;abaixo_minimo\n"
        "1;Principal;1;RACAO-001;Ração Premium;UN;5.00;3.00;SIM\n"
    )

    def fake_gerar_csv_por_deposito(
        db,
        empresa_id,
        deposito_id,
        busca=None,
        somente_abaixo_minimo=False,
    ):
        assert empresa_id == 1
        assert deposito_id == 1
        assert busca == "racao"
        assert somente_abaixo_minimo is True
        return csv_content

    monkeypatch.setattr(
        estoque_crud,
        "gerar_csv_relatorio_posicao_por_deposito",
        fake_gerar_csv_por_deposito,
    )

    response = client.get(
       "/api/estoque/relatorios/posicao-por-deposito/1/csv?busca=racao&somente_abaixo_minimo=true",
        headers={"X-Empresa-Id": "1"},
    )

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert (
        'attachment; filename="estoque_posicao_deposito_1.csv"'
        == response.headers["content-disposition"]
    )
    assert response.text == csv_content


def test_relatorios_sem_header_empresa_retorna_400(client):
    response = client.get("/api/estoque/relatorios/posicao-resumida")

    assert response.status_code == 400
    assert response.json()["detail"] == "X-Empresa-Id é obrigatório."