(function () {
  "use strict";

  const API_BASE = "/api/conciliacao-bancaria";

  const STORAGE_EMPRESA_KEYS = [
    "petflow_empresa_id",
    "empresa_id",
    "empresaSelecionadaId",
    "empresaSelecionada",
    "empresaAtualId",
  ];

  let arquivoSelecionado = null;
  let ultimoResultado = null;

  document.addEventListener("DOMContentLoaded", inicializarConciliacaoBancaria);

  function inicializarConciliacaoBancaria() {
    configurarDatasPadrao();
    configurarEmpresaPadrao();
    vincularEventos();
  }

  function configurarDatasPadrao() {
    const hoje = new Date();
    const inicio = new Date(hoje.getFullYear(), hoje.getMonth(), 1);

    const inputInicio = document.getElementById("conciliacaoDataInicio");
    const inputFim = document.getElementById("conciliacaoDataFim");

    if (inputInicio && !inputInicio.value) {
      inputInicio.value = formatarDataInput(inicio);
    }

    if (inputFim && !inputFim.value) {
      inputFim.value = formatarDataInput(hoje);
    }
  }

  function configurarEmpresaPadrao() {
    const inputEmpresa = document.getElementById("conciliacaoEmpresaId");

    if (!inputEmpresa) {
      return;
    }

    inputEmpresa.value = detectarEmpresaAtual() || inputEmpresa.value || "2";
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
    const inputArquivo = document.getElementById("conciliacaoArquivo");
    const dropArea = document.getElementById("conciliacaoDropArea");
    const btnProcessar = document.getElementById("btnProcessarConciliacao");
    const btnLimpar = document.getElementById("btnLimparConciliacao");
    const inputEmpresa = document.getElementById("conciliacaoEmpresaId");

    if (inputArquivo) {
      inputArquivo.addEventListener("change", function () {
        definirArquivo(inputArquivo.files && inputArquivo.files[0] ? inputArquivo.files[0] : null);
      });
    }

    if (dropArea) {
      dropArea.addEventListener("dragover", function (event) {
        event.preventDefault();
        dropArea.classList.add("is-dragover");
      });

      dropArea.addEventListener("dragleave", function () {
        dropArea.classList.remove("is-dragover");
      });

      dropArea.addEventListener("drop", function (event) {
        event.preventDefault();
        dropArea.classList.remove("is-dragover");

        const arquivo = event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0];

        if (arquivo) {
          definirArquivo(arquivo);

          if (inputArquivo) {
            inputArquivo.files = event.dataTransfer.files;
          }
        }
      });
    }

    if (btnProcessar) {
      btnProcessar.addEventListener("click", processarConciliacao);
    }

    if (btnLimpar) {
      btnLimpar.addEventListener("click", limparTela);
    }

    if (inputEmpresa) {
      inputEmpresa.addEventListener("change", function () {
        if (inputEmpresa.value) {
          localStorage.setItem("empresa_id", inputEmpresa.value);
          localStorage.setItem("empresaSelecionadaId", inputEmpresa.value);
        }
      });
    }

    document.querySelectorAll(".conciliacao-tab").forEach(function (tab) {
      tab.addEventListener("click", function () {
        trocarAba(tab.dataset.tab);
      });
    });
  }

  function definirArquivo(arquivo) {
    arquivoSelecionado = arquivo;

    const nomeEl = document.getElementById("conciliacaoArquivoNome");

    if (!nomeEl) {
      return;
    }

    if (!arquivoSelecionado) {
      nomeEl.textContent = "Nenhum arquivo selecionado";
      return;
    }

    nomeEl.textContent = `${arquivoSelecionado.name} (${formatarTamanhoArquivo(arquivoSelecionado.size)})`;
  }

  async function processarConciliacao() {
    ocultarMensagem();

    const filtros = obterFiltros();

    if (!filtros) {
      return;
    }

    if (!arquivoSelecionado) {
      exibirMensagem("Selecione um arquivo CSV, OFX ou QFX para processar.", "erro");
      return;
    }

    const extensao = obterExtensaoArquivo(arquivoSelecionado.name);

    if (!["csv", "ofx", "qfx"].includes(extensao)) {
      exibirMensagem("Formato inválido. Envie um arquivo CSV, OFX ou QFX.", "erro");
      return;
    }

    const endpoint = extensao === "csv" ? "importar-csv" : "importar-ofx";

    const params = new URLSearchParams({
      empresa_id: filtros.empresaId,
      data_inicio: filtros.dataInicio,
      data_fim: filtros.dataFim,
      tolerancia_centavos: filtros.toleranciaCentavos,
      tolerancia_dias: filtros.toleranciaDias,
    });

    const formData = new FormData();
    formData.append("arquivo", arquivoSelecionado);

    setProcessando(true);

    try {
      const resposta = await fetch(`${API_BASE}/${endpoint}?${params.toString()}`, {
        method: "POST",
        headers: montarHeadersUpload(),
        body: formData,
      });

      if (!resposta.ok) {
        const erro = await resposta.json().catch(function () {
          return null;
        });

        throw new Error(
          erro?.detail || `Erro ao processar conciliação. Status ${resposta.status}.`
        );
      }

      const dados = await resposta.json();
      ultimoResultado = dados;

      renderizarResultado(dados);
      exibirMensagem("Conciliação processada com sucesso.", "sucesso");
    } catch (error) {
      console.error(error);
      exibirMensagem(error.message || "Não foi possível processar a conciliação.", "erro");
    } finally {
      setProcessando(false);
    }
  }

  function obterFiltros() {
    const empresaId = String(document.getElementById("conciliacaoEmpresaId")?.value || "").trim();
    const dataInicio = document.getElementById("conciliacaoDataInicio")?.value;
    const dataFim = document.getElementById("conciliacaoDataFim")?.value;
    const toleranciaDias = String(document.getElementById("conciliacaoToleranciaDias")?.value || "2").trim();
    const toleranciaCentavos = String(document.getElementById("conciliacaoToleranciaCentavos")?.value || "2").trim();

    if (!empresaId) {
      exibirMensagem("Informe a empresa.", "erro");
      return null;
    }

    if (!dataInicio || !dataFim) {
      exibirMensagem("Informe a data inicial e a data final.", "erro");
      return null;
    }

    if (dataFim < dataInicio) {
      exibirMensagem("A data final não pode ser menor que a data inicial.", "erro");
      return null;
    }

    return {
      empresaId,
      dataInicio,
      dataFim,
      toleranciaDias,
      toleranciaCentavos,
    };
  }

  function montarHeadersUpload() {
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

  function renderizarResultado(dados) {
    renderizarResumo(dados.resumo || {});
    renderizarConciliados(dados.conciliados || []);
    renderizarPendentesBanco(dados.pendentes_banco || []);
    renderizarPendentesSistema(dados.pendentes_sistema || []);
  }

  function renderizarResumo(resumo) {
    const container = document.getElementById("conciliacaoResumoCards");

    if (!container) {
      return;
    }

    const conciliados = Number(resumo.conciliados || 0);
    const movimentosBanco = Number(resumo.movimentos_banco || 0);
    const pendentesBanco = Number(resumo.pendentes_banco || 0);
    const pendentesSistema = Number(resumo.pendentes_sistema || 0);
    const percentual = movimentosBanco > 0 ? Math.round((conciliados / movimentosBanco) * 100) : 0;

    container.innerHTML = `
      ${montarCardResumo(
        "Movimentos banco",
        movimentosBanco,
        `${moeda(resumo.total_banco_entradas || 0)} em entradas e ${moeda(resumo.total_banco_saidas || 0)} em saídas`,
        ""
      )}
      ${montarCardResumo(
        "Conciliados",
        conciliados,
        `${percentual}% do extrato bancário`,
        percentual >= 80 ? "is-ok" : percentual >= 50 ? "is-alerta" : "is-risco"
      )}
      ${montarCardResumo(
        "Pendentes banco",
        pendentesBanco,
        "Itens do extrato sem baixa correspondente",
        pendentesBanco > 0 ? "is-alerta" : "is-ok"
      )}
      ${montarCardResumo(
        "Pendentes sistema",
        pendentesSistema,
        "Baixas do sistema sem item no extrato",
        pendentesSistema > 0 ? "is-alerta" : "is-ok"
      )}
    `;
  }

  function montarCardResumo(titulo, valor, detalhe, classe) {
    return `
      <article class="conciliacao-card conciliacao-resumo-card ${classe || ""}">
        <span>${escaparHtml(titulo)}</span>
        <strong>${escaparHtml(valor)}</strong>
        <small>${escaparHtml(detalhe)}</small>
      </article>
    `;
  }

  function renderizarConciliados(itens) {
    const tbody = document.getElementById("conciliacaoTabelaConciliados");

    if (!tbody) {
      return;
    }

    if (!itens.length) {
      tbody.innerHTML = `
        <tr>
          <td colspan="8" class="conciliacao-empty">Nenhum movimento conciliado automaticamente.</td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = itens
      .map(function (item) {
        const banco = item.banco || {};
        const sistema = item.sistema || {};

        return `
          <tr>
            <td>${formatarDataBR(banco.data)}</td>
            <td>
              <strong>${escaparHtml(banco.descricao || "-")}</strong>
              ${banco.documento ? `<br><span class="conciliacao-muted">Doc.: ${escaparHtml(banco.documento)}</span>` : ""}
            </td>
            <td class="conciliacao-right ${classeValorPorTipo(banco.tipo)}">${moeda(banco.valor || 0)}</td>
            <td>${formatarDataBR(sistema.data)}</td>
            <td>
              <strong>${escaparHtml(sistema.descricao || "-")}</strong>
              ${sistema.pessoa ? `<br><span class="conciliacao-muted">${escaparHtml(sistema.pessoa)}</span>` : ""}
            </td>
            <td class="conciliacao-right ${classeValorPorTipo(sistema.tipo)}">${moeda(sistema.valor || 0)}</td>
            <td class="conciliacao-right">
              <span class="conciliacao-badge conciliacao-badge-score">${Number(item.score || 0)}%</span>
            </td>
            <td>${escaparHtml(item.motivo || "-")}</td>
          </tr>
        `;
      })
      .join("");
  }

  function renderizarPendentesBanco(itens) {
    const tbody = document.getElementById("conciliacaoTabelaPendentesBanco");

    if (!tbody) {
      return;
    }

    if (!itens.length) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="conciliacao-empty">Nenhum movimento pendente no banco.</td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = itens
      .map(function (item) {
        return `
          <tr>
            <td>${formatarDataBR(item.data)}</td>
            <td>
              <strong>${escaparHtml(item.descricao || "-")}</strong>
              ${item.documento ? `<br><span class="conciliacao-muted">Doc.: ${escaparHtml(item.documento)}</span>` : ""}
            </td>
            <td>${escaparHtml(item.documento || "-")}</td>
            <td>${badgeTipo(item.tipo)}</td>
            <td class="conciliacao-right ${classeValorPorTipo(item.tipo)}">${moeda(item.valor || 0)}</td>
            <td>${montarSugestoes(item.sugestoes || [])}</td>
          </tr>
        `;
      })
      .join("");
  }

  function renderizarPendentesSistema(itens) {
    const tbody = document.getElementById("conciliacaoTabelaPendentesSistema");

    if (!tbody) {
      return;
    }

    if (!itens.length) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" class="conciliacao-empty">Nenhum movimento pendente no sistema.</td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = itens
      .map(function (item) {
        return `
          <tr>
            <td>${formatarDataBR(item.data)}</td>
            <td>
              <strong>${escaparHtml(item.descricao || "-")}</strong>
            </td>
            <td>${escaparHtml(item.pessoa || "-")}</td>
            <td>${badgeTipo(item.tipo)}</td>
            <td>${escaparHtml(formatarFormaPagamento(item.forma_pagamento))}</td>
            <td class="conciliacao-right ${classeValorPorTipo(item.tipo)}">${moeda(item.valor || 0)}</td>
            <td>
              <span class="conciliacao-badge conciliacao-badge-status">${escaparHtml(item.status || "-")}</span>
            </td>
          </tr>
        `;
      })
      .join("");
  }

  function montarSugestoes(sugestoes) {
    if (!sugestoes.length) {
      return `<span class="conciliacao-muted">Sem sugestão</span>`;
    }

    return `
      <div class="conciliacao-sugestoes">
        ${sugestoes
          .map(function (sugestao) {
            const sistema = sugestao.sistema || {};

            return `
              <div class="conciliacao-sugestao">
                <strong>${escaparHtml(sistema.descricao || "-")}</strong>
                <span>${formatarDataBR(sistema.data)} • ${moeda(sistema.valor || 0)} • ${Number(sugestao.score || 0)}%</span>
                <span>${escaparHtml(sugestao.motivo || "")}</span>
              </div>
            `;
          })
          .join("")}
      </div>
    `;
  }

  function badgeTipo(tipo) {
    const tipoNormalizado = String(tipo || "").toUpperCase();

    if (tipoNormalizado === "ENTRADA") {
      return `<span class="conciliacao-badge conciliacao-badge-entrada">Entrada</span>`;
    }

    if (tipoNormalizado === "SAIDA") {
      return `<span class="conciliacao-badge conciliacao-badge-saida">Saída</span>`;
    }

    return `<span class="conciliacao-badge conciliacao-badge-status">${escaparHtml(tipo || "-")}</span>`;
  }

  function classeValorPorTipo(tipo) {
    return String(tipo || "").toUpperCase() === "SAIDA"
      ? "conciliacao-valor-negativo"
      : "conciliacao-valor-positivo";
  }

  function trocarAba(nomeAba) {
    if (!nomeAba) {
      return;
    }

    document.querySelectorAll(".conciliacao-tab").forEach(function (tab) {
      tab.classList.toggle("active", tab.dataset.tab === nomeAba);
    });

    document.querySelectorAll(".conciliacao-tab-panel").forEach(function (panel) {
      panel.classList.remove("active");
    });

    const panel = document.getElementById(`tab-${nomeAba}`);

    if (panel) {
      panel.classList.add("active");
    }
  }

  function limparTela() {
    arquivoSelecionado = null;
    ultimoResultado = null;

    const inputArquivo = document.getElementById("conciliacaoArquivo");
    const nomeArquivo = document.getElementById("conciliacaoArquivoNome");

    if (inputArquivo) {
      inputArquivo.value = "";
    }

    if (nomeArquivo) {
      nomeArquivo.textContent = "Nenhum arquivo selecionado";
    }

    ocultarMensagem();
    configurarDatasPadrao();

    const resumo = document.getElementById("conciliacaoResumoCards");

    if (resumo) {
      resumo.innerHTML = `
        ${montarCardResumo("Movimentos banco", "--", "Aguardando importação", "")}
        ${montarCardResumo("Conciliados", "--", "Aguardando importação", "")}
        ${montarCardResumo("Pendentes banco", "--", "Aguardando importação", "")}
        ${montarCardResumo("Pendentes sistema", "--", "Aguardando importação", "")}
      `;
    }

    preencherTabelaVazia("conciliacaoTabelaConciliados", 8, "Nenhum arquivo processado.");
    preencherTabelaVazia("conciliacaoTabelaPendentesBanco", 6, "Nenhum arquivo processado.");
    preencherTabelaVazia("conciliacaoTabelaPendentesSistema", 7, "Nenhum arquivo processado.");

    trocarAba("conciliados");
  }

  function preencherTabelaVazia(id, colunas, mensagem) {
    const tbody = document.getElementById(id);

    if (!tbody) {
      return;
    }

    tbody.innerHTML = `
      <tr>
        <td colspan="${colunas}" class="conciliacao-empty">${escaparHtml(mensagem)}</td>
      </tr>
    `;
  }

  function setProcessando(processando) {
    const botao = document.getElementById("btnProcessarConciliacao");
    const btnLimpar = document.getElementById("btnLimparConciliacao");

    if (botao) {
      botao.disabled = processando;
      botao.textContent = processando ? "Processando..." : "Processar conciliação";
    }

    if (btnLimpar) {
      btnLimpar.disabled = processando;
    }
  }

  function exibirMensagem(texto, tipo) {
    const el = document.getElementById("conciliacaoMensagem");

    if (!el) {
      return;
    }

    el.hidden = false;
    el.className = `conciliacao-message conciliacao-message-${tipo || "info"}`;
    el.textContent = texto;
  }

  function ocultarMensagem() {
    const el = document.getElementById("conciliacaoMensagem");

    if (!el) {
      return;
    }

    el.hidden = true;
    el.textContent = "";
  }

  function obterExtensaoArquivo(nome) {
    const partes = String(nome || "").split(".");

    if (partes.length < 2) {
      return "";
    }

    return partes.pop().toLowerCase();
  }

  function formatarTamanhoArquivo(bytes) {
    const tamanho = Number(bytes || 0);

    if (tamanho < 1024) {
      return `${tamanho} B`;
    }

    if (tamanho < 1024 * 1024) {
      return `${(tamanho / 1024).toFixed(1)} KB`;
    }

    return `${(tamanho / 1024 / 1024).toFixed(1)} MB`;
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

  function formatarFormaPagamento(valor) {
    if (!valor) {
      return "-";
    }

    const texto = String(valor)
      .replace(/_/g, " ")
      .toLowerCase();

    return texto.charAt(0).toUpperCase() + texto.slice(1);
  }

  function escaparHtml(valor) {
    return String(valor ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
})();
