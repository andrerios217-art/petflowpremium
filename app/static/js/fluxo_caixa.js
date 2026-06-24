(function () {
  "use strict";

  const API_BASE = "/api/fluxo-caixa";

  const FORMAS_ICONS = {
    DINHEIRO: "\uD83D\uDCB5",
    PIX: "\u26A1",
    CONTA_BANCARIA: "\uD83C\uDFE6",
    CARTAO_CREDITO: "\uD83D\uDCB3",
    CARTAO_DEBITO: "\uD83D\uDCB3",
    BOLETO: "\uD83E\uDDFE",
    OUTRO: "\uD83D\uDCCC",
  };

  const STORAGE_EMPRESA_KEYS = [
    "petflow_empresa_id",
    "empresa_id",
    "empresaSelecionadaId",
    "empresaSelecionada",
    "empresaAtualId",
  ];

  document.addEventListener("DOMContentLoaded", inicializarFluxoCaixa);

  function inicializarFluxoCaixa() {
    injetarEstiloFluxoCaixa();
    const root = garantirRoot();
    root.innerHTML = montarLayout();

    configurarDatasPadrao();
    configurarEmpresaPadrao();
    vincularEventos();

    carregarFluxoCaixa();
  }

  function garantirRoot() {
    let root = document.getElementById("fluxoCaixaApp");

    if (root) {
      return root;
    }

    const alvoExistente =
      document.querySelector(".fluxo-caixa-page") ||
      document.querySelector(".fluxo-caixa-container") ||
      document.querySelector("[data-fluxo-caixa]");

    if (alvoExistente) {
      alvoExistente.innerHTML = "";
      alvoExistente.id = "fluxoCaixaApp";
      return alvoExistente;
    }

    const main =
      document.querySelector("main") ||
      document.querySelector(".main-content") ||
      document.querySelector(".content") ||
      document.querySelector(".page-content") ||
      document.body;

    root = document.createElement("section");
    root.id = "fluxoCaixaApp";
    root.className = "fluxo-caixa-page";
    main.appendChild(root);

    return root;
  }

  function montarLayout() {
    return `
      <div class="fc-wrapper">
        <div class="fc-header">
          <div>
            <p class="fc-eyebrow">Financeiro</p>
            <h1>Fluxo de Caixa</h1>
            <p class="fc-subtitle">Entradas, sa\u00eddas, previs\u00e3o e sa\u00fade financeira da empresa.</p>
          </div>

          <div class="fc-header-actions">
            <button type="button" class="fc-btn fc-btn-secondary" id="btnAtualizarFluxo">
              Atualizar
            </button>

            <button type="button" class="fc-btn fc-btn-exportar" id="btnExportarFluxo">
              Exportar XLSX
            </button>
          </div>
        </div>

        <div class="fc-filtros">
          <label class="fc-field">
            <span>Empresa</span>
            <input type="number" id="fluxoEmpresaId" min="1" step="1" />
          </label>

          <label class="fc-field">
            <span>Data inicial</span>
            <input type="date" id="fluxoDataInicio" />
          </label>

          <label class="fc-field">
            <span>Data final</span>
            <input type="date" id="fluxoDataFim" />
          </label>

          <button type="button" class="fc-btn fc-btn-primary" id="btnFiltrarFluxo">
            Filtrar
          </button>
        </div>

        <div id="fluxoMensagem" class="fc-message" hidden></div>

        <section class="fc-grid fc-grid-resumo" id="fluxoResumoCards">
          ${cardSkeleton("Entradas")}
          ${cardSkeleton("Sa\u00eddas")}
          ${cardSkeleton("Saldo")}
          ${cardSkeleton("Previs\u00e3o")}
        </section>

        <section class="fc-section">
          <div class="fc-section-title">
            <div>
              <h2>Sem\u00e1foro financeiro</h2>
              <p>Leitura autom\u00e1tica do saldo realizado, vencidos e previs\u00e3o.</p>
            </div>
          </div>

          <div id="fluxoSemaforo" class="fc-semaforo fc-semaforo-neutro">
            <div class="fc-semaforo-indicador"></div>
            <div>
              <h3>Carregando...</h3>
              <p>Aguarde a an\u00e1lise do caixa.</p>
            </div>
          </div>
        </section>

        <section class="fc-section">
          <div class="fc-section-title">
            <div>
              <h2>Previs\u00e3o de caixa</h2>
              <p>Pr\u00f3ximos 7, 15 e 30 dias.</p>
            </div>
          </div>

          <div class="fc-grid fc-grid-previsao" id="fluxoPrevisoes"></div>
        </section>

        <section class="fc-section">
          <div class="fc-section-title">
            <div>
              <h2>Formas de pagamento</h2>
              <p>Entradas, sa\u00eddas e saldo por meio financeiro.</p>
            </div>
          </div>

          <div class="fc-grid fc-grid-formas" id="fluxoFormasPagamento"></div>
        </section>

        <section class="fc-section">
          <div class="fc-section-title">
            <div>
              <h2>Tabela di\u00e1ria</h2>
              <p>Entradas, sa\u00eddas e saldo acumulado por dia.</p>
            </div>
          </div>

          <div class="fc-table-wrap">
            <table class="fc-table">
              <thead>
                <tr>
                  <th>Data</th>
                  <th class="fc-right">Entradas</th>
                  <th class="fc-right">Sa\u00eddas</th>
                  <th class="fc-right">Saldo do dia</th>
                  <th class="fc-right">Saldo acumulado</th>
                  <th class="fc-right">Movimentos</th>
                </tr>
              </thead>
              <tbody id="fluxoSerieDiaria">
                <tr>
                  <td colspan="6" class="fc-empty">Carregando dados...</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>
    `;
  }

  function cardSkeleton(titulo) {
    return `
      <article class="fc-card">
        <span>${titulo}</span>
        <strong>--</strong>
        <small>Carregando...</small>
      </article>
    `;
  }

  function configurarDatasPadrao() {
    const hoje = new Date();
    const inicio = new Date(hoje.getFullYear(), hoje.getMonth(), 1);

    const inputInicio = document.getElementById("fluxoDataInicio");
    const inputFim = document.getElementById("fluxoDataFim");

    if (inputInicio && !inputInicio.value) {
      inputInicio.value = formatarDataInput(inicio);
    }

    if (inputFim && !inputFim.value) {
      inputFim.value = formatarDataInput(hoje);
    }
  }

  function configurarEmpresaPadrao() {
    const inputEmpresa = document.getElementById("fluxoEmpresaId");

    if (!inputEmpresa) {
      return;
    }

    const empresaDetectada = detectarEmpresaAtual();
    inputEmpresa.value = empresaDetectada || "2";
  }

  function detectarEmpresaAtual() {
    const params = new URLSearchParams(window.location.search);
    const empresaUrl = params.get("empresa_id") || params.get("empresa");

    if (empresaUrl) {
      return empresaUrl;
    }

    const seletores = [
      "#empresa_id",
      "#empresaId",
      "#empresaSelect",
      "#empresa-select",
      "#filtroEmpresa",
      "#empresaFiltro",
      "#selectEmpresa",
      "select[name='empresa_id']",
      "input[name='empresa_id']",
      "[data-empresa-id]",
    ];

    for (const seletor of seletores) {
      const el = document.querySelector(seletor);

      if (!el) {
        continue;
      }

      const valor = el.value || el.dataset.empresaId;

      if (valor) {
        return valor;
      }
    }

    for (const chave of STORAGE_EMPRESA_KEYS) {
      const valor = localStorage.getItem(chave);

      if (valor) {
        return valor;
      }
    }

    return null;
  }

  function vincularEventos() {
    const btnAtualizar = document.getElementById("btnAtualizarFluxo");
    const btnFiltrar = document.getElementById("btnFiltrarFluxo");
    const btnExportar = document.getElementById("btnExportarFluxo");
    const inputEmpresa = document.getElementById("fluxoEmpresaId");

    if (btnAtualizar) {
      btnAtualizar.addEventListener("click", carregarFluxoCaixa);
    }

    if (btnFiltrar) {
      btnFiltrar.addEventListener("click", carregarFluxoCaixa);
    }

    if (btnExportar) {
      btnExportar.addEventListener("click", exportarFluxoCaixa);
    }

    if (inputEmpresa) {
      inputEmpresa.addEventListener("change", function () {
        if (inputEmpresa.value) {
          localStorage.setItem("empresa_id", inputEmpresa.value);
          localStorage.setItem("empresaSelecionadaId", inputEmpresa.value);
        }
      });
    }
  }

  async function carregarFluxoCaixa() {
    ocultarMensagem();

    const filtros = obterFiltros();

    if (!filtros) {
      return;
    }

    setLoading(true);

    try {
      const params = new URLSearchParams({
        empresa_id: filtros.empresaId,
        data_inicio: filtros.dataInicio,
        data_fim: filtros.dataFim,
      });

      const resposta = await fetch(`${API_BASE}/resumo?${params.toString()}`, {
        method: "GET",
        headers: montarHeaders(),
      });

      if (!resposta.ok) {
        const erro = await resposta.json().catch(function () {
          return null;
        });

        throw new Error(
          erro?.detail || `Erro ao carregar fluxo de caixa. Status ${resposta.status}.`
        );
      }

      const dados = await resposta.json();

      renderizarResumo(dados.resumo || {});
      renderizarSemaforo(dados.semaforo || {});
      renderizarPrevisoes(dados.previsoes || []);
      renderizarFormasPagamento(dados.formas_pagamento || []);
      renderizarSerieDiaria(dados.serie_diaria || []);
    } catch (error) {
      console.error(error);
      exibirMensagem(error.message || "N\u00e3o foi poss\u00edvel carregar o fluxo de caixa.", "erro");
    } finally {
      setLoading(false);
    }
  }

  async function exportarFluxoCaixa() {
    ocultarMensagem();

    const filtros = obterFiltros();

    if (!filtros) {
      return;
    }

    setExportando(true);

    try {
      const params = new URLSearchParams({
        empresa_id: filtros.empresaId,
        data_inicio: filtros.dataInicio,
        data_fim: filtros.dataFim,
        incluir_previstos: "true",
        saldo_inicial: "0",
      });

      const resposta = await fetch(`${API_BASE}/exportar-xlsx?${params.toString()}`, {
        method: "GET",
        headers: montarHeaders(),
      });

      if (!resposta.ok) {
        const erro = await resposta.json().catch(function () {
          return null;
        });

        throw new Error(
          erro?.detail || `Erro ao exportar XLSX. Status ${resposta.status}.`
        );
      }

      const blob = await resposta.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      const nomeArquivo = montarNomeArquivoXlsx(filtros);

      link.href = url;
      link.download = nomeArquivo;
      document.body.appendChild(link);
      link.click();

      window.URL.revokeObjectURL(url);
      link.remove();

      exibirMensagem("Arquivo XLSX gerado com sucesso.", "info");
    } catch (error) {
      console.error(error);
      exibirMensagem(error.message || "N\u00e3o foi poss\u00edvel exportar o XLSX.", "erro");
    } finally {
      setExportando(false);
    }
  }

  function obterFiltros() {
    const empresaId = obterEmpresaId();
    const dataInicio = document.getElementById("fluxoDataInicio")?.value;
    const dataFim = document.getElementById("fluxoDataFim")?.value;

    if (!empresaId) {
      exibirMensagem("Informe a empresa para carregar o fluxo de caixa.", "erro");
      return null;
    }

    if (!dataInicio || !dataFim) {
      exibirMensagem("Informe a data inicial e a data final.", "erro");
      return null;
    }

    if (dataFim < dataInicio) {
      exibirMensagem("A data final n\u00e3o pode ser menor que a data inicial.", "erro");
      return null;
    }

    return {
      empresaId,
      dataInicio,
      dataFim,
    };
  }

  function obterEmpresaId() {
    const inputEmpresa = document.getElementById("fluxoEmpresaId");
    const valor = inputEmpresa?.value || detectarEmpresaAtual() || "2";
    return String(valor).trim();
  }

  function montarHeaders() {
    const headers = {
      Accept: "application/json",
    };

    const token =
      localStorage.getItem("access_token") ||
      localStorage.getItem("token") ||
      localStorage.getItem("authToken") ||
      sessionStorage.getItem("access_token") ||
      sessionStorage.getItem("token");

    if (token) {
      headers.Authorization = token.startsWith("Bearer ") ? token : `Bearer ${token}`;
    }

    return headers;
  }

  function renderizarResumo(resumo) {
    const container = document.getElementById("fluxoResumoCards");

    if (!container) {
      return;
    }

    const entradas = Number(resumo.entradas_realizadas ?? resumo.entradas ?? 0);
    const saidas = Number(resumo.saidas_realizadas ?? resumo.saidas ?? 0);
    const saldo = Number(resumo.saldo_realizado ?? resumo.saldo ?? 0);
    const saldoPrevisto = Number(resumo.saldo_previsto ?? 0);

    container.innerHTML = `
      ${montarCardResumo(
        "Entradas realizadas",
        moeda(entradas),
        `${resumo.Quantidade_entradas_realizadas || 0} recebimento(s) no per\u00edodo`,
        "positivo"
      )}
      ${montarCardResumo(
        "Sa\u00eddas realizadas",
        moeda(saidas),
        `${resumo.Quantidade_saidas_realizadas || 0} pagamento(s) no per\u00edodo`,
        "negativo"
      )}
      ${montarCardResumo(
        "Saldo realizado",
        moeda(saldo),
        saldo >= 0 ? "Resultado positivo no per\u00edodo" : "Resultado negativo no per\u00edodo",
        saldo >= 0 ? "positivo" : "negativo"
      )}
      ${montarCardResumo(
        "Saldo previsto",
        moeda(saldoPrevisto),
        `${resumo.Quantidade_entradas_previstas || 0} entrada(s) e ${resumo.Quantidade_saidas_previstas || 0} sa\u00edda(s) previstas`,
        saldoPrevisto >= 0 ? "positivo" : "negativo"
      )}
    `;
  }

  function montarCardResumo(titulo, valor, detalhe, tipo) {
    return `
      <article class="fc-card fc-card-${tipo}">
        <span>${escaparHtml(titulo)}</span>
        <strong>${escaparHtml(valor)}</strong>
        <small>${escaparHtml(detalhe)}</small>
      </article>
    `;
  }

  function renderizarSemaforo(semaforo) {
    const container = document.getElementById("fluxoSemaforo");

    if (!container) {
      return;
    }

    const cor = String(semaforo.cor || "neutro").toLowerCase();
    const titulo = semaforo.titulo || "Sem dados suficientes";
    const mensagem = semaforo.mensagem || "Ainda n\u00e3o foi poss\u00edvel calcular a sa\u00fade do caixa.";

    container.className = `fc-semaforo fc-semaforo-${cor}`;

    container.innerHTML = `
      <div class="fc-semaforo-indicador"></div>
      <div class="fc-semaforo-info">
        <h3>${escaparHtml(titulo)}</h3>
        <p>${escaparHtml(mensagem)}</p>

        <div class="fc-semaforo-metricas">
          <span>7 dias: <strong>${moeda(semaforo.saldo_projetado_7 || 0)}</strong></span>
          <span>15 dias: <strong>${moeda(semaforo.saldo_projetado_15 || 0)}</strong></span>
          <span>30 dias: <strong>${moeda(semaforo.saldo_projetado_30 || 0)}</strong></span>
        </div>
      </div>
    `;
  }

  function renderizarPrevisoes(previsoes) {
    const container = document.getElementById("fluxoPrevisoes");

    if (!container) {
      return;
    }

    if (!previsoes.length) {
      container.innerHTML = `<div class="fc-empty-card">Nenhuma previs\u00e3o encontrada.</div>`;
      return;
    }

    container.innerHTML = previsoes
      .map(function (item) {
        const saldo = Number(item.saldo_previsto || 0);
        const classe = saldo >= 0 ? "positivo" : "negativo";

        return `
          <article class="fc-card fc-previsao-card fc-card-${classe}">
            <span>${escaparHtml(item.titulo || `Pr\u00f3ximos ${item.dias} dias`)}</span>
            <strong>${moeda(saldo)}</strong>
            <small>
              Entradas: ${moeda(item.entradas_previstas || 0)}<br>
              Sa\u00eddas: ${moeda(item.saidas_previstas || 0)}
            </small>
            <div class="fc-mini-meta">
              ${item.Quantidade_total || 0} movimento(s)
            </div>
          </article>
        `;
      })
      .join("");
  }

  function renderizarFormasPagamento(formas) {
    const container = document.getElementById("fluxoFormasPagamento");

    if (!container) {
      return;
    }

    if (!formas.length) {
      container.innerHTML = `<div class="fc-empty-card">Nenhuma forma de pagamento encontrada.</div>`;
      return;
    }

    container.innerHTML = formas
      .map(function (item) {
        const saldo = Number(item.saldo || 0);
        const classe = saldo >= 0 ? "positivo" : "negativo";
        const icone = FORMAS_ICONS[item.chave] || FORMAS_ICONS.OUTRO;

        return `
          <article class="fc-forma-card fc-card-${classe}">
            <div class="fc-forma-top">
              <div class="fc-forma-icon">${icone}</div>
              <div>
                <h3>${escaparHtml(item.forma_pagamento || "Outro")}</h3>
                <p>${item.Quantidade_total || 0} movimento(s)</p>
              </div>
            </div>

            <div class="fc-forma-valores">
              <div>
                <span>Entradas</span>
                <strong>${moeda(item.entradas || 0)}</strong>
              </div>

              <div>
                <span>Sa\u00eddas</span>
                <strong>${moeda(item.saidas || 0)}</strong>
              </div>

              <div>
                <span>Saldo</span>
                <strong>${moeda(saldo)}</strong>
              </div>
            </div>
          </article>
        `;
      })
      .join("");
  }

  function renderizarSerieDiaria(serie) {
    const tbody = document.getElementById("fluxoSerieDiaria");

    if (!tbody) {
      return;
    }

    if (!serie.length) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="fc-empty">Nenhum movimento encontrado para o per\u00edodo.</td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = serie
      .map(function (item) {
        const saldoDia = Number(item.saldo_dia || 0);
        const saldoAcumulado = Number(item.saldo_acumulado || 0);

        return `
          <tr>
            <td>${formatarDataBR(item.data)}</td>
            <td class="fc-right fc-positive">${moeda(item.entradas || 0)}</td>
            <td class="fc-right fc-negative">${moeda(item.saidas || 0)}</td>
            <td class="fc-right ${saldoDia >= 0 ? "fc-positive" : "fc-negative"}">${moeda(saldoDia)}</td>
            <td class="fc-right ${saldoAcumulado >= 0 ? "fc-positive" : "fc-negative"}">${moeda(saldoAcumulado)}</td>
            <td class="fc-right">${item.Quantidade_movimentos || 0}</td>
          </tr>
        `;
      })
      .join("");
  }

  function setLoading(loading) {
    const botoes = [
      document.getElementById("btnAtualizarFluxo"),
      document.getElementById("btnFiltrarFluxo"),
    ];

    botoes.forEach(function (botao) {
      if (!botao) {
        return;
      }

      botao.disabled = loading;
      botao.classList.toggle("is-loading", loading);
    });
  }

  function setExportando(exportando) {
    const botao = document.getElementById("btnExportarFluxo");

    if (!botao) {
      return;
    }

    botao.disabled = exportando;
    botao.classList.toggle("is-loading", exportando);
    botao.textContent = exportando ? "Exportando..." : "Exportar XLSX";
  }

  function exibirMensagem(texto, tipo) {
    const el = document.getElementById("fluxoMensagem");

    if (!el) {
      return;
    }

    el.hidden = false;
    el.className = `fc-message fc-message-${tipo || "info"}`;
    el.textContent = texto;
  }

  function ocultarMensagem() {
    const el = document.getElementById("fluxoMensagem");

    if (!el) {
      return;
    }

    el.hidden = true;
    el.textContent = "";
  }

  function moeda(valor) {
    const numero = Number(valor || 0);

    return numero.toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
    });
  }

  function formatarDataInput(data) {
    const ano = data.getFullYear();
    const mes = String(data.getMonth() + 1).padStart(2, "0");
    const dia = String(data.getDate()).padStart(2, "0");

    return `${ano}-${mes}-${dia}`;
  }

  function formatarDataBR(valor) {
    if (!valor) {
      return "-";
    }

    const partes = String(valor).split("-");

    if (partes.length !== 3) {
      return valor;
    }

    return `${partes[2]}/${partes[1]}/${partes[0]}`;
  }

  function montarNomeArquivoXlsx(filtros) {
    return `fluxo_caixa_empresa_${filtros.empresaId}_${filtros.dataInicio}_${filtros.dataFim}.xlsx`;
  }

  function escaparHtml(valor) {
    return String(valor ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function injetarEstiloFluxoCaixa() {
    if (document.getElementById("fluxoCaixaStyleRuntime")) {
      return;
    }

    const style = document.createElement("style");
    style.id = "fluxoCaixaStyleRuntime";
    style.textContent = `
      .fc-wrapper {
        display: flex;
        flex-direction: column;
        gap: 22px;
        padding: 22px;
      }

      .fc-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 18px;
        flex-wrap: wrap;
      }

      .fc-eyebrow {
        margin: 0 0 4px;
        color: #64748b;
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .08em;
      }

      .fc-header h1 {
        margin: 0;
        color: #0f172a;
        font-size: 30px;
        line-height: 1.1;
      }

      .fc-subtitle {
        margin: 8px 0 0;
        color: #64748b;
        font-size: 15px;
      }

      .fc-header-actions {
        display: flex;
        align-items: center;
        gap: 10px;
      }

      .fc-filtros {
        display: grid;
        grid-template-columns: minmax(130px, 180px) minmax(160px, 220px) minmax(160px, 220px) auto;
        align-items: end;
        gap: 12px;
        padding: 16px;
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        background: #ffffff;
        box-shadow: 0 10px 30px rgba(15, 23, 42, .06);
      }

      .fc-field {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }

      .fc-field span {
        color: #475569;
        font-size: 13px;
        font-weight: 700;
      }

      .fc-field input,
      .fc-field select {
        width: 100%;
        height: 42px;
        padding: 0 12px;
        color: #0f172a;
        border: 1px solid #cbd5e1;
        border-radius: 12px;
        background: #ffffff;
        outline: none;
      }

      .fc-field input:focus,
      .fc-field select:focus {
        border-color: #2563eb;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, .12);
      }

      .fc-btn {
        height: 42px;
        padding: 0 16px;
        border: 0;
        border-radius: 12px;
        font-weight: 800;
        cursor: pointer;
        transition: transform .15s ease, opacity .15s ease, box-shadow .15s ease;
      }

      .fc-btn:hover {
        transform: translateY(-1px);
      }

      .fc-btn:disabled {
        opacity: .65;
        cursor: wait;
        transform: none;
      }

      .fc-btn-primary {
        color: #ffffff;
        background: #2563eb;
        box-shadow: 0 10px 22px rgba(37, 99, 235, .18);
      }

      .fc-btn-secondary {
        color: #0f172a;
        background: #e2e8f0;
      }

      .fc-btn-exportar {
        color: #ffffff;
        background: #15803d;
        box-shadow: 0 10px 22px rgba(21, 128, 61, .18);
      }

      .fc-message {
        padding: 12px 14px;
        border-radius: 14px;
        font-size: 14px;
        font-weight: 700;
      }

      .fc-message-erro {
        color: #991b1b;
        background: #fee2e2;
        border: 1px solid #fecaca;
      }

      .fc-message-info {
        color: #1e3a8a;
        background: #dbeafe;
        border: 1px solid #bfdbfe;
      }

      .fc-grid {
        display: grid;
        gap: 14px;
      }

      .fc-grid-resumo {
        grid-template-columns: repeat(4, minmax(0, 1fr));
      }

      .fc-grid-previsao {
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }

      .fc-grid-formas {
        grid-template-columns: repeat(4, minmax(0, 1fr));
      }

      .fc-card,
      .fc-forma-card,
      .fc-empty-card {
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        background: #ffffff;
        box-shadow: 0 10px 30px rgba(15, 23, 42, .06);
      }

      .fc-card {
        padding: 16px;
      }

      .fc-card span {
        display: block;
        color: #64748b;
        font-size: 13px;
        font-weight: 800;
      }

      .fc-card strong {
        display: block;
        margin-top: 8px;
        color: #0f172a;
        font-size: 24px;
        line-height: 1.1;
      }

      .fc-card small {
        display: block;
        margin-top: 8px;
        color: #64748b;
        font-size: 13px;
        line-height: 1.35;
      }

      .fc-card-positivo strong,
      .fc-positive {
        color: #15803d;
      }

      .fc-card-negativo strong,
      .fc-negative {
        color: #b91c1c;
      }

      .fc-section {
        display: flex;
        flex-direction: column;
        gap: 14px;
      }

      .fc-section-title {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 12px;
      }

      .fc-section-title h2 {
        margin: 0;
        color: #0f172a;
        font-size: 20px;
      }

      .fc-section-title p {
        margin: 4px 0 0;
        color: #64748b;
        font-size: 14px;
      }

      .fc-semaforo {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 18px;
        border-radius: 20px;
        border: 1px solid #e2e8f0;
        background: #ffffff;
        box-shadow: 0 10px 30px rgba(15, 23, 42, .06);
      }

      .fc-semaforo-indicador {
        width: 48px;
        height: 48px;
        flex: 0 0 48px;
        border-radius: 999px;
        background: #94a3b8;
        box-shadow: inset 0 0 0 8px rgba(255, 255, 255, .55);
      }

      .fc-semaforo-verde .fc-semaforo-indicador {
        background: #22c55e;
      }

      .fc-semaforo-amarelo .fc-semaforo-indicador {
        background: #f59e0b;
      }

      .fc-semaforo-vermelho .fc-semaforo-indicador {
        background: #ef4444;
      }

      .fc-semaforo-info h3 {
        margin: 0;
        color: #0f172a;
        font-size: 18px;
      }

      .fc-semaforo-info p {
        margin: 5px 0 0;
        color: #64748b;
        font-size: 14px;
      }

      .fc-semaforo-metricas {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 12px;
      }

      .fc-semaforo-metricas span {
        padding: 7px 10px;
        border-radius: 999px;
        color: #334155;
        background: #f1f5f9;
        font-size: 13px;
      }

      .fc-mini-meta {
        display: inline-flex;
        width: fit-content;
        margin-top: 12px;
        padding: 6px 9px;
        color: #475569;
        background: #f1f5f9;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 800;
      }

      .fc-forma-card {
        padding: 15px;
      }

      .fc-forma-top {
        display: flex;
        align-items: center;
        gap: 12px;
      }

      .fc-forma-icon {
        display: grid;
        place-items: center;
        width: 42px;
        height: 42px;
        border-radius: 14px;
        background: #f1f5f9;
        font-size: 20px;
      }

      .fc-forma-top h3 {
        margin: 0;
        color: #0f172a;
        font-size: 15px;
      }

      .fc-forma-top p {
        margin: 3px 0 0;
        color: #64748b;
        font-size: 12px;
      }

      .fc-forma-valores {
        display: grid;
        grid-template-columns: 1fr;
        gap: 8px;
        margin-top: 14px;
      }

      .fc-forma-valores div {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        padding-top: 8px;
        border-top: 1px solid #f1f5f9;
      }

      .fc-forma-valores span {
        color: #64748b;
        font-size: 13px;
      }

      .fc-forma-valores strong {
        color: #0f172a;
        font-size: 13px;
      }

      .fc-table-wrap {
        overflow-x: auto;
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        background: #ffffff;
        box-shadow: 0 10px 30px rgba(15, 23, 42, .06);
      }

      .fc-table {
        width: 100%;
        border-collapse: collapse;
        min-width: 760px;
      }

      .fc-table th,
      .fc-table td {
        padding: 13px 14px;
        border-bottom: 1px solid #f1f5f9;
        color: #334155;
        font-size: 14px;
      }

      .fc-table th {
        color: #64748b;
        background: #f8fafc;
        font-size: 12px;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: .05em;
        text-align: left;
      }

      .fc-table tr:last-child td {
        border-bottom: 0;
      }

      .fc-right {
        text-align: right !important;
      }

      .fc-empty,
      .fc-empty-card {
        color: #64748b;
        text-align: center;
      }

      .fc-empty-card {
        padding: 22px;
        grid-column: 1 / -1;
      }

      @media (max-width: 1180px) {
        .fc-grid-resumo,
        .fc-grid-formas {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }

      @media (max-width: 860px) {
        .fc-wrapper {
          padding: 14px;
        }

        .fc-filtros,
        .fc-grid-resumo,
        .fc-grid-previsao,
        .fc-grid-formas {
          grid-template-columns: 1fr;
        }

        .fc-header {
          flex-direction: column;
        }

        .fc-header-actions,
        .fc-btn {
          width: 100%;
        }
      }
    `;

    document.head.appendChild(style);
  }
})();
