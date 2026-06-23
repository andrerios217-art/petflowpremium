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
  let linhasConferencia = [];

  document.addEventListener("DOMContentLoaded", inicializarConciliacaoBancaria);

  async function inicializarConciliacaoBancaria() {
    configurarDatasPadrao();
    configurarEmpresaPadrao();
    vincularEventos();
    habilitarCadastroConciliacao(false);
    await carregarHistoricoConciliacoes();
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
    const btnExportar = document.getElementById("btnExportarConciliacao");
    const btnCadastrar = document.getElementById("btnCadastrarConciliacao");
    const btnLimpar = document.getElementById("btnLimparConciliacao");
    const btnAtualizarHistorico = document.getElementById("btnAtualizarHistoricoConciliacao");
    const btnSelecionarTodos = document.getElementById("btnSelecionarTodosConferencia");
    const btnMarcarConferidos = document.getElementById("btnMarcarConferidos");
    const btnMarcarIgnorados = document.getElementById("btnMarcarIgnorados");
    const btnMarcarPendentes = document.getElementById("btnMarcarPendentes");
    const checkTodos = document.getElementById("checkTodosConferencia");
    const inputEmpresa = document.getElementById("conciliacaoEmpresaId");
    const tabelaConferencia = document.getElementById("conciliacaoTabelaConferencia");
    const tabelaHistorico = document.getElementById("conciliacaoTabelaHistorico");

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

    if (btnExportar) {
      btnExportar.addEventListener("click", exportarConciliacaoXlsx);
    }

    if (btnCadastrar) {
      btnCadastrar.addEventListener("click", cadastrarConciliacao);
    }

    if (btnLimpar) {
      btnLimpar.addEventListener("click", limparTela);
    }

    if (btnAtualizarHistorico) {
      btnAtualizarHistorico.addEventListener("click", carregarHistoricoConciliacoes);
    }

    if (btnSelecionarTodos) {
      btnSelecionarTodos.addEventListener("click", alternarSelecaoConferencia);
    }

    if (btnMarcarConferidos) {
      btnMarcarConferidos.addEventListener("click", function () {
        marcarSelecionadosComo("CONFERIDO");
      });
    }

    if (btnMarcarIgnorados) {
      btnMarcarIgnorados.addEventListener("click", function () {
        marcarSelecionadosComo("IGNORADO");
      });
    }

    if (btnMarcarPendentes) {
      btnMarcarPendentes.addEventListener("click", function () {
        marcarSelecionadosComo("PENDENTE");
      });
    }

    if (checkTodos) {
      checkTodos.addEventListener("change", function () {
        marcarTodosConferencia(checkTodos.checked);
      });
    }

    if (inputEmpresa) {
      inputEmpresa.addEventListener("change", async function () {
        if (inputEmpresa.value) {
          localStorage.setItem("empresa_id", inputEmpresa.value);
          localStorage.setItem("empresaSelecionadaId", inputEmpresa.value);
          await carregarHistoricoConciliacoes();
        }
      });
    }

    if (tabelaConferencia) {
      tabelaConferencia.addEventListener("change", function (event) {
        const alvo = event.target;

        if (alvo.classList.contains("conciliacao-check-conferencia")) {
          atualizarCheckTodosConferencia();
          return;
        }

        if (alvo.classList.contains("conciliacao-status-select")) {
          const index = Number(alvo.dataset.index);
          const linha = linhasConferencia[index];

          if (!linha) {
            return;
          }

          linha.status = alvo.value || "PENDENTE";
          linha.observacao = obterObservacaoPadrao(linha);
          renderizarConferencia();
          atualizarResumoConferencia();
          habilitarCadastroConciliacao(true);
        }
      });
    }

    if (tabelaHistorico) {
      tabelaHistorico.addEventListener("click", function (event) {
        const botao = event.target.closest("[data-historico-action]");

        if (!botao) {
          return;
        }

        const id = botao.dataset.historicoId;
        const action = botao.dataset.historicoAction;

        if (!id) {
          return;
        }

        if (action === "ver") {
          carregarResultadoHistorico(id);
        }

        if (action === "xlsx") {
          exportarHistoricoXlsx(id);
        }
      });
    }
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

    if (!validarArquivoSelecionado()) {
      return;
    }

    const extensao = obterExtensaoArquivo(arquivoSelecionado.name);
    const endpoint = extensao === "csv" ? "importar-csv" : "importar-ofx";

    const params = montarParametros(filtros);
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

        throw new Error(obterMensagemErroApi(erro, `Erro ao processar extrato. Status ${resposta.status}.`));
      }

      const dados = await resposta.json();

      ultimoResultado = dados;
      ultimoResultado.nome_arquivo = ultimoResultado.nome_arquivo || arquivoSelecionado.name;
      ultimoResultado.tipo_arquivo = ultimoResultado.tipo_arquivo || extensao.toUpperCase();

      linhasConferencia = montarLinhasConferencia(ultimoResultado);

      renderizarConferencia();
      atualizarResumoConferencia();
      habilitarCadastroConciliacao(true);

      exibirMensagem(
        "Extrato processado. O que bateu com o financeiro foi marcado como conferido. Revise apenas pendências e cadastre a conciliação.",
        "sucesso"
      );
    } catch (error) {
      console.error(error);
      exibirMensagem(error.message || "Não foi possível processar o extrato.", "erro");
    } finally {
      setProcessando(false);
    }
  }

  async function exportarConciliacaoXlsx() {
    ocultarMensagem();

    const filtros = obterFiltros();

    if (!filtros) {
      return;
    }

    if (!validarArquivoSelecionado()) {
      return;
    }

    const params = montarParametros(filtros);
    const formData = new FormData();
    formData.append("arquivo", arquivoSelecionado);

    setExportando(true);

    try {
      const resposta = await fetch(`${API_BASE}/exportar-xlsx?${params.toString()}`, {
        method: "POST",
        headers: montarHeadersUpload(),
        body: formData,
      });

      if (!resposta.ok) {
        const erro = await resposta.json().catch(function () {
          return null;
        });

        throw new Error(obterMensagemErroApi(erro, `Erro ao exportar XLSX. Status ${resposta.status}.`));
      }

      const blob = await resposta.blob();
      baixarBlob(blob, montarNomeArquivoXlsx(filtros));

      exibirMensagem("Arquivo XLSX exportado com sucesso.", "sucesso");
    } catch (error) {
      console.error(error);
      exibirMensagem(error.message || "Não foi possível exportar o XLSX.", "erro");
    } finally {
      setExportando(false);
    }
  }

  async function cadastrarConciliacao() {
    ocultarMensagem();

    const empresaId = obterEmpresaId();

    if (!empresaId) {
      exibirMensagem("Informe a empresa para salvar a conferência.", "erro");
      return;
    }

    if (!ultimoResultado || !linhasConferencia.length) {
      exibirMensagem("Processe um extrato antes de salvar a conferência.", "erro");
      return;
    }

    if (ultimoResultado.historico_id) {
      exibirMensagem("Esta conferência já foi salva no histórico.", "info");
      habilitarCadastroConciliacao(false);
      return;
    }

    const resultadoParaSalvar = montarResultadoParaSalvar();

    const headers = montarHeadersJson();
    headers["Content-Type"] = "application/json";

    setCadastrando(true);

    try {
      const resposta = await fetch(`${API_BASE}/cadastrar`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          empresa_id: Number(empresaId),
          nome_arquivo: resultadoParaSalvar.nome_arquivo || "extrato_bancario",
          tipo_arquivo: resultadoParaSalvar.tipo_arquivo || "CSV",
          resultado: resultadoParaSalvar,
        }),
      });

      if (!resposta.ok) {
        const erro = await resposta.json().catch(function () {
          return null;
        });

        throw new Error(obterMensagemErroApi(erro, `Erro ao salvar conferência. Status ${resposta.status}.`));
      }

      const dados = await resposta.json();

      if (dados.historico && dados.historico.id) {
        ultimoResultado.historico_id = dados.historico.id;
      }

      habilitarCadastroConciliacao(false);
      await carregarHistoricoConciliacoes();

      exibirMensagem("Conferência salva no histórico com sucesso.", "sucesso");
    } catch (error) {
      console.error(error);
      exibirMensagem(error.message || "Não foi possível salvar a conferência.", "erro");
    } finally {
      setCadastrando(false);
    }
  }

  function montarLinhasConferencia(resultado) {
    const linhas = [];

    const conciliados = Array.isArray(resultado.conciliados) ? resultado.conciliados : [];
    const pendentesBanco = Array.isArray(resultado.pendentes_banco) ? resultado.pendentes_banco : [];

    conciliados.forEach(function (item, index) {
      const banco = normalizarBanco(item.banco || {});
      const sistema = item.sistema || {};

      linhas.push({
        id: `conciliado-${index}`,
        banco,
        sistema,
        status: "CONFERIDO",
        correspondencia: montarTextoCorrespondencia(sistema),
        score: Number(item.score || 100),
        motivo: item.motivo || "Correspondência encontrada automaticamente.",
        observacao: item.motivo || "Correspondência encontrada automaticamente.",
      });
    });

    pendentesBanco.forEach(function (item, index) {
      const banco = normalizarBanco(item);

      linhas.push({
        id: `pendente-${index}`,
        banco,
        sistema: null,
        status: sugerirStatusInicial(banco),
        correspondencia: "Não encontrado no financeiro",
        score: 0,
        motivo: "Pendente de conferência",
        observacao: sugerirObservacaoSimples(banco),
      });
    });

    linhas.sort(function (a, b) {
      const dataA = String(a.banco.data || "");
      const dataB = String(b.banco.data || "");

      if (dataA !== dataB) {
        return dataA.localeCompare(dataB);
      }

      return String(a.banco.descricao || "").localeCompare(String(b.banco.descricao || ""));
    });

    return linhas;
  }

  function normalizarBanco(item) {
    return {
      linha: item.linha || null,
      data: item.data || item.data_iso || null,
      tipo: String(item.tipo || "").toUpperCase(),
      descricao: item.descricao || "Movimento bancário",
      documento: item.documento || null,
      valor: Number(item.valor || item.valor_float || 0),
      valor_original: Number(item.valor_original || item.valor || 0),
    };
  }

  function montarTextoCorrespondencia(sistema) {
    if (!sistema) {
      return "Não encontrado no financeiro";
    }

    const partes = [];

    if (sistema.descricao) {
      partes.push(sistema.descricao);
    }

    if (sistema.pessoa) {
      partes.push(sistema.pessoa);
    }

    if (sistema.data) {
      partes.push(formatarDataBR(sistema.data));
    }

    return partes.length ? partes.join(" | ") : "Encontrado no financeiro";
  }

  function sugerirStatusInicial(banco) {
    const texto = normalizarTexto(`${banco.descricao || ""} ${banco.documento || ""}`);

    if (
      texto.includes("saldo anterior") ||
      texto.includes("saldo do dia") ||
      texto.includes("saldo final") ||
      texto.includes("aplicacao automatica") ||
      texto.includes("aplicação automatica")
    ) {
      return "IGNORADO";
    }

    return "PENDENTE";
  }

  function sugerirObservacaoSimples(banco) {
    const texto = normalizarTexto(`${banco.descricao || ""} ${banco.documento || ""}`);
    const tipo = String(banco.tipo || "").toUpperCase();

    if (tipo === "ENTRADA") {
      if (texto.includes("stone") || texto.includes("cartao") || texto.includes("cartão") || texto.includes("recebivel")) {
        return "Entrada provável de cartão/PDV. Conferir com recebíveis.";
      }

      if (texto.includes("pix")) {
        return "Entrada PIX. Conferir se já está no PDV.";
      }

      if (texto.includes("transferencia") || texto.includes("transferência")) {
        return "Transferência recebida. Conferir origem.";
      }

      return "Entrada bancária pendente de conferência.";
    }

    if (texto.includes("iof")) {
      return "Despesa bancária: IOF.";
    }

    if (texto.includes("juros") || texto.includes("encargos")) {
      return "Despesa bancária: juros/encargos.";
    }

    if (texto.includes("tarifa") || texto.includes("tar ") || texto.includes("cesta")) {
      return "Despesa bancária: tarifa.";
    }

    if (texto.includes("pix")) {
      return "PIX enviado. Conferir fornecedor, despesa ou transferência.";
    }

    if (texto.includes("boleto")) {
      return "Boleto pago. Conferir no contas a pagar.";
    }

    if (texto.includes("sispag")) {
      return "Pagamento em lote/SISPAG. Conferir fornecedor ou folha.";
    }

    return "Saída bancária pendente de conferência.";
  }

  function renderizarConferencia() {
    const tbody = document.getElementById("conciliacaoTabelaConferencia");

    if (!tbody) {
      return;
    }

    if (!linhasConferencia.length) {
      preencherTabelaVazia("conciliacaoTabelaConferencia", 9, "Nenhum arquivo processado.");
      atualizarCheckTodosConferencia();
      return;
    }

    tbody.innerHTML = linhasConferencia
      .map(function (linha, index) {
        const banco = linha.banco || {};

        return `
          <tr class="conciliacao-linha-${escaparHtml(linha.status.toLowerCase())}">
            <td class="conciliacao-center">
              <input
                type="checkbox"
                class="conciliacao-check-conferencia"
                data-index="${index}"
              >
            </td>
            <td>${formatarDataBR(banco.data)}</td>
            <td>
              <strong>${escaparHtml(banco.descricao || "-")}</strong>
            </td>
            <td>${escaparHtml(banco.documento || "-")}</td>
            <td>${badgeTipo(banco.tipo)}</td>
            <td class="conciliacao-right ${classeValorPorTipo(banco.tipo)}">${moeda(banco.valor || 0)}</td>
            <td>
              <select class="conciliacao-status-select" data-index="${index}">
                ${optionStatus("CONFERIDO", "Conferido", linha.status)}
                ${optionStatus("PENDENTE", "Pendente", linha.status)}
                ${optionStatus("IGNORADO", "Ignorado", linha.status)}
              </select>
            </td>
            <td>
              <span class="conciliacao-muted">${escaparHtml(linha.correspondencia || "-")}</span>
            </td>
            <td>
              <span class="conciliacao-muted">${escaparHtml(linha.observacao || "-")}</span>
            </td>
          </tr>
        `;
      })
      .join("");

    atualizarCheckTodosConferencia();
  }

  function optionStatus(value, label, atual) {
    const selected = String(value) === String(atual) ? "selected" : "";
    return `<option value="${escaparHtml(value)}" ${selected}>${escaparHtml(label)}</option>`;
  }

  function marcarSelecionadosComo(status) {
    const selecionados = obterIndicesSelecionados();

    if (!selecionados.length) {
      exibirMensagem("Selecione pelo menos um movimento.", "erro");
      return;
    }

    selecionados.forEach(function (index) {
      const linha = linhasConferencia[index];

      if (!linha) {
        return;
      }

      linha.status = status;
      linha.observacao = obterObservacaoPadrao(linha);
    });

    renderizarConferencia();
    atualizarResumoConferencia();
    habilitarCadastroConciliacao(true);

    exibirMensagem(`${selecionados.length} movimento(s) atualizado(s).`, "sucesso");
  }

  function obterObservacaoPadrao(linha) {
    if (!linha) {
      return "-";
    }

    if (linha.status === "CONFERIDO") {
      return linha.sistema ? "Conferido com o financeiro." : "Conferido manualmente pelo operador.";
    }

    if (linha.status === "IGNORADO") {
      return "Ignorado na conferência bancária.";
    }

    return sugerirObservacaoSimples(linha.banco || {});
  }

  function obterIndicesSelecionados() {
    return Array.from(document.querySelectorAll(".conciliacao-check-conferencia"))
      .filter(function (checkbox) {
        return checkbox.checked;
      })
      .map(function (checkbox) {
        return Number(checkbox.dataset.index);
      })
      .filter(function (index) {
        return Number.isInteger(index) && index >= 0;
      });
  }

  function alternarSelecaoConferencia() {
    const checkboxes = Array.from(document.querySelectorAll(".conciliacao-check-conferencia"));

    if (!checkboxes.length) {
      return;
    }

    const deveMarcar = checkboxes.some(function (checkbox) {
      return !checkbox.checked;
    });

    checkboxes.forEach(function (checkbox) {
      checkbox.checked = deveMarcar;
    });

    atualizarCheckTodosConferencia();
  }

  function marcarTodosConferencia(marcar) {
    document.querySelectorAll(".conciliacao-check-conferencia").forEach(function (checkbox) {
      checkbox.checked = marcar;
    });

    atualizarCheckTodosConferencia();
  }

  function atualizarCheckTodosConferencia() {
    const checkTodos = document.getElementById("checkTodosConferencia");
    const checkboxes = Array.from(document.querySelectorAll(".conciliacao-check-conferencia"));

    if (!checkTodos) {
      return;
    }

    if (!checkboxes.length) {
      checkTodos.checked = false;
      checkTodos.indeterminate = false;
      return;
    }

    const marcados = checkboxes.filter(function (checkbox) {
      return checkbox.checked;
    }).length;

    checkTodos.checked = marcados === checkboxes.length;
    checkTodos.indeterminate = marcados > 0 && marcados < checkboxes.length;
  }

  function atualizarResumoConferencia() {
    const total = linhasConferencia.length;
    const conferidos = contarStatus("CONFERIDO");
    const pendentes = contarStatus("PENDENTE");
    const ignorados = contarStatus("IGNORADO");

    const container = document.getElementById("conciliacaoResumoCards");

    if (!container) {
      return;
    }

    container.innerHTML = `
      ${montarCardResumo("Movimentos banco", total, "Total importado do extrato", "")}
      ${montarCardResumo("Conferidos", conferidos, `${percentual(conferidos, total)}% do extrato`, conferidos === total ? "is-ok" : "is-alerta")}
      ${montarCardResumo("Pendentes", pendentes, "Precisam de revisão", pendentes > 0 ? "is-risco" : "is-ok")}
      ${montarCardResumo("Ignorados", ignorados, "Fora da conferência", ignorados > 0 ? "is-alerta" : "")}
    `;
  }

  function contarStatus(status) {
    return linhasConferencia.filter(function (linha) {
      return linha.status === status;
    }).length;
  }

  function percentual(parte, total) {
    if (!total) {
      return 0;
    }

    return Math.round((Number(parte || 0) / Number(total || 1)) * 100);
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

  function montarResultadoParaSalvar() {
    const conferidos = linhasConferencia.filter(function (linha) {
      return linha.status === "CONFERIDO";
    });

    const pendentes = linhasConferencia.filter(function (linha) {
      return linha.status === "PENDENTE";
    });

    const ignorados = linhasConferencia.filter(function (linha) {
      return linha.status === "IGNORADO";
    });

    const conciliados = conferidos.map(function (linha) {
      return {
        banco: linha.banco,
        sistema: linha.sistema || {
          data: linha.banco.data,
          descricao: "Conferido manualmente",
          pessoa: null,
          tipo: linha.banco.tipo,
          forma_pagamento: "CONTA_BANCARIA",
          valor: linha.banco.valor,
          status: "CONFERIDO",
          origem: "conferencia_manual",
          id: null,
        },
        score: linha.score || (linha.sistema ? 100 : 0),
        motivo: linha.observacao || "Conferido pelo operador",
        manual: !linha.sistema,
      };
    });

    const pendentesBanco = pendentes.map(function (linha) {
      return {
        ...linha.banco,
        status_conferencia: "PENDENTE",
        observacao_conferencia: linha.observacao,
      };
    });

    const ignoradosBanco = ignorados.map(function (linha) {
      return {
        ...linha.banco,
        status_conferencia: "IGNORADO",
        observacao_conferencia: linha.observacao,
      };
    });

    const resumoOriginal = ultimoResultado.resumo || {};

    return {
      ...ultimoResultado,
      linhas_conferencia: linhasConferencia,
      conciliados,
      pendentes_banco: pendentesBanco,
      pendentes_sistema: ultimoResultado.pendentes_sistema || [],
      ignorados_banco: ignoradosBanco,
      resumo: {
        ...resumoOriginal,
        movimentos_banco: linhasConferencia.length,
        conciliados: conciliados.length,
        pendentes_banco: pendentesBanco.length,
        pendentes_sistema: (ultimoResultado.pendentes_sistema || []).length,
        ignorados: ignoradosBanco.length,
        conferidos: conciliados.length,
      },
    };
  }

  async function carregarHistoricoConciliacoes() {
    const empresaId = obterEmpresaId();

    if (!empresaId) {
      return;
    }

    preencherTabelaVazia("conciliacaoTabelaHistorico", 9, "Carregando histórico...");

    try {
      const params = new URLSearchParams({
        empresa_id: empresaId,
        limite: "50",
      });

      const resposta = await fetch(`${API_BASE}/historico?${params.toString()}`, {
        method: "GET",
        headers: montarHeadersJson(),
      });

      if (!resposta.ok) {
        const erro = await resposta.json().catch(function () {
          return null;
        });

        throw new Error(obterMensagemErroApi(erro, `Erro ao carregar histórico. Status ${resposta.status}.`));
      }

      const dados = await resposta.json();
      renderizarHistorico(dados.historico || []);
    } catch (error) {
      console.error(error);
      preencherTabelaVazia("conciliacaoTabelaHistorico", 9, "Não foi possível carregar o histórico.");
    }
  }

  async function carregarResultadoHistorico(id) {
    ocultarMensagem();

    const empresaId = obterEmpresaId();

    if (!empresaId) {
      exibirMensagem("Informe a empresa para abrir o histórico.", "erro");
      return;
    }

    try {
      const params = new URLSearchParams({
        empresa_id: empresaId,
      });

      const resposta = await fetch(`${API_BASE}/historico/${id}?${params.toString()}`, {
        method: "GET",
        headers: montarHeadersJson(),
      });

      if (!resposta.ok) {
        const erro = await resposta.json().catch(function () {
          return null;
        });

        throw new Error(obterMensagemErroApi(erro, `Erro ao abrir histórico. Status ${resposta.status}.`));
      }

      const dados = await resposta.json();
      const resultado = dados.resultado || {};

      ultimoResultado = resultado;
      linhasConferencia = Array.isArray(resultado.linhas_conferencia)
        ? resultado.linhas_conferencia
        : montarLinhasConferencia(resultado);

      renderizarConferencia();
      atualizarResumoConferencia();
      habilitarCadastroConciliacao(false);

      exibirMensagem(`Histórico #${id} carregado na tela.`, "info");

      const conferenciaSection = document.querySelector(".conciliacao-section");

      if (conferenciaSection) {
        conferenciaSection.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    } catch (error) {
      console.error(error);
      exibirMensagem(error.message || "Não foi possível abrir o histórico.", "erro");
    }
  }

  async function exportarHistoricoXlsx(id) {
    ocultarMensagem();

    const empresaId = obterEmpresaId();

    if (!empresaId) {
      exibirMensagem("Informe a empresa para exportar o histórico.", "erro");
      return;
    }

    try {
      const params = new URLSearchParams({
        empresa_id: empresaId,
      });

      const resposta = await fetch(`${API_BASE}/historico/${id}/exportar-xlsx?${params.toString()}`, {
        method: "GET",
        headers: montarHeadersJson(),
      });

      if (!resposta.ok) {
        const erro = await resposta.json().catch(function () {
          return null;
        });

        throw new Error(obterMensagemErroApi(erro, `Erro ao exportar histórico. Status ${resposta.status}.`));
      }

      const blob = await resposta.blob();
      baixarBlob(blob, `conciliacao_bancaria_historico_${id}.xlsx`);

      exibirMensagem(`Histórico #${id} exportado com sucesso.`, "sucesso");
    } catch (error) {
      console.error(error);
      exibirMensagem(error.message || "Não foi possível exportar o histórico.", "erro");
    }
  }

  function renderizarHistorico(itens) {
    const tbody = document.getElementById("conciliacaoTabelaHistorico");

    if (!tbody) {
      return;
    }

    if (!itens.length) {
      preencherTabelaVazia("conciliacaoTabelaHistorico", 9, "Nenhuma conciliação gravada ainda.");
      return;
    }

    tbody.innerHTML = itens
      .map(function (item) {
        const conferidos = Number(item.conciliados || item.conferidos || 0);
        const pendentes = Number(item.pendentes_banco || 0);
        const ignorados = Number(item.ignorados || 0);

        return `
          <tr>
            <td>#${escaparHtml(item.id)}</td>
            <td>
              <strong>${escaparHtml(item.nome_arquivo || "-")}</strong>
              <br>
              <span class="conciliacao-muted">${escaparHtml(item.tipo_arquivo || "-")}</span>
            </td>
            <td>${formatarDataBR(item.data_inicio)} até ${formatarDataBR(item.data_fim)}</td>
            <td class="conciliacao-right">${Number(item.movimentos_banco || 0)}</td>
            <td class="conciliacao-right conciliacao-valor-positivo">${conferidos}</td>
            <td class="conciliacao-right ${pendentes > 0 ? "conciliacao-valor-negativo" : "conciliacao-valor-positivo"}">${pendentes}</td>
            <td class="conciliacao-right">${ignorados}</td>
            <td>${formatarDataHoraBR(item.criado_em)}</td>
            <td class="conciliacao-right">
              <div class="conciliacao-inline-actions">
                <button
                  type="button"
                  class="conciliacao-btn-mini"
                  data-historico-action="ver"
                  data-historico-id="${escaparHtml(item.id)}"
                >
                  Ver
                </button>

                <button
                  type="button"
                  class="conciliacao-btn-mini conciliacao-btn-mini-exportar"
                  data-historico-action="xlsx"
                  data-historico-id="${escaparHtml(item.id)}"
                >
                  XLSX
                </button>
              </div>
            </td>
          </tr>
        `;
      })
      .join("");
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

  function validarArquivoSelecionado() {
    if (!arquivoSelecionado) {
      exibirMensagem("Selecione um arquivo CSV, OFX ou QFX para processar.", "erro");
      return false;
    }

    const extensao = obterExtensaoArquivo(arquivoSelecionado.name);

    if (!["csv", "ofx", "qfx"].includes(extensao)) {
      exibirMensagem("Formato inválido. Envie um arquivo CSV, OFX ou QFX.", "erro");
      return false;
    }

    return true;
  }

  function montarParametros(filtros) {
    return new URLSearchParams({
      empresa_id: filtros.empresaId,
      data_inicio: filtros.dataInicio,
      data_fim: filtros.dataFim,
      tolerancia_centavos: filtros.toleranciaCentavos,
      tolerancia_dias: filtros.toleranciaDias,
    });
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

  function obterEmpresaId() {
    const inputEmpresa = document.getElementById("conciliacaoEmpresaId");
    const valor = inputEmpresa?.value || detectarEmpresaAtual() || "2";
    return String(valor).trim();
  }

  function montarHeadersJson() {
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

  function montarHeadersUpload() {
    return montarHeadersJson();
  }

  function limparTela() {
    arquivoSelecionado = null;
    ultimoResultado = null;
    linhasConferencia = [];

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
    habilitarCadastroConciliacao(false);

    const resumo = document.getElementById("conciliacaoResumoCards");

    if (resumo) {
      resumo.innerHTML = `
        ${montarCardResumo("Movimentos banco", "--", "Aguardando importação", "")}
        ${montarCardResumo("Conferidos", "--", "Aguardando importação", "")}
        ${montarCardResumo("Pendentes", "--", "Aguardando importação", "")}
        ${montarCardResumo("Ignorados", "--", "Aguardando importação", "")}
      `;
    }

    preencherTabelaVazia("conciliacaoTabelaConferencia", 9, "Nenhum arquivo processado.");
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

  function habilitarCadastroConciliacao(habilitar) {
    const botao = document.getElementById("btnCadastrarConciliacao");

    if (!botao) {
      return;
    }

    botao.disabled = !habilitar;
    botao.classList.toggle("is-enabled", !!habilitar);

    if (habilitar) {
      botao.removeAttribute("disabled");
    } else {
      botao.setAttribute("disabled", "disabled");
    }

    botao.textContent = "Salvar conferência";
  }

  function setProcessando(processando) {
    const botao = document.getElementById("btnProcessarConciliacao");
    const btnLimpar = document.getElementById("btnLimparConciliacao");

    if (botao) {
      botao.disabled = processando;
      botao.textContent = processando ? "Processando..." : "Processar extrato";
    }

    if (btnLimpar) {
      btnLimpar.disabled = processando;
    }
  }

  function setExportando(exportando) {
    const botao = document.getElementById("btnExportarConciliacao");
    const btnProcessar = document.getElementById("btnProcessarConciliacao");
    const btnLimpar = document.getElementById("btnLimparConciliacao");

    if (botao) {
      botao.disabled = exportando;
      botao.textContent = exportando ? "Exportando..." : "Exportar XLSX";
    }

    if (btnProcessar) {
      btnProcessar.disabled = exportando;
    }

    if (btnLimpar) {
      btnLimpar.disabled = exportando;
    }
  }

  function setCadastrando(cadastrando) {
    const botao = document.getElementById("btnCadastrarConciliacao");
    const btnProcessar = document.getElementById("btnProcessarConciliacao");
    const btnExportar = document.getElementById("btnExportarConciliacao");
    const btnLimpar = document.getElementById("btnLimparConciliacao");

    if (botao) {
      botao.disabled = cadastrando;
      botao.textContent = cadastrando ? "Salvando..." : "Salvar conferência";
    }

    if (btnProcessar) {
      btnProcessar.disabled = cadastrando;
    }

    if (btnExportar) {
      btnExportar.disabled = cadastrando;
    }

    if (btnLimpar) {
      btnLimpar.disabled = cadastrando;
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

  function baixarBlob(blob, nomeArquivo) {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = nomeArquivo;
    document.body.appendChild(link);
    link.click();

    window.URL.revokeObjectURL(url);
    link.remove();
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

    const texto = String(valor);

    if (texto.includes("T")) {
      return formatarDataHoraBR(texto);
    }

    const partes = texto.split("-");

    if (partes.length !== 3) {
      return texto;
    }

    return `${partes[2]}/${partes[1]}/${partes[0]}`;
  }

  function formatarDataHoraBR(valor) {
    if (!valor) {
      return "-";
    }

    const data = new Date(valor);

    if (Number.isNaN(data.getTime())) {
      return String(valor);
    }

    return data.toLocaleString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function montarNomeArquivoXlsx(filtros) {
    return `conciliacao_bancaria_empresa_${filtros.empresaId}_${filtros.dataInicio}_${filtros.dataFim}.xlsx`;
  }

  function classeValorPorTipo(tipo) {
    return String(tipo || "").toUpperCase() === "SAIDA"
      ? "conciliacao-valor-negativo"
      : "conciliacao-valor-positivo";
  }

  function obterMensagemErroApi(erro, fallback) {
    if (!erro) {
      return fallback;
    }

    if (typeof erro.detail === "string") {
      return erro.detail;
    }

    if (erro.detail && typeof erro.detail === "object") {
      return erro.detail.mensagem || JSON.stringify(erro.detail);
    }

    return fallback;
  }

  function normalizarTexto(valor) {
    return String(valor || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
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
