(function () {
  const state = {
    empresaId: 1,
    caixaAtual: null,
    caixaResumo: null,
    vendaAtual: null,
    clientesEncontrados: [],
    producaoPronta: [],
    operadores: [],
  };

  const els = {
    alertaGeral: document.getElementById("pdv-alerta-geral"),

    empresaId: document.getElementById("pdv-empresa-id"),

    caixaStatus: document.getElementById("pdv-caixa-status"),
    caixaOperador: document.getElementById("pdv-caixa-operador"),
    caixaAbertura: document.getElementById("pdv-caixa-abertura"),
    caixaSaldo: document.getElementById("pdv-caixa-saldo"),

    btnAbrirCaixa: document.getElementById("btn-abrir-caixa"),
    btnSangria: document.getElementById("btn-sangria"),
    btnSuprimento: document.getElementById("btn-suprimento"),
    btnFecharCaixa: document.getElementById("btn-fechar-caixa"),

    btnVendaBalcao: document.getElementById("btn-venda-balcao"),
    btnCancelarVenda: document.getElementById("btn-cancelar-venda"),

    vendaCliente: document.getElementById("pdv-venda-cliente"),
    vendaMeta: document.getElementById("pdv-venda-meta"),
    vendaNumero: document.getElementById("pdv-venda-numero"),
    vendaModo: document.getElementById("pdv-venda-modo"),

    buscaProduto: document.getElementById("pdv-busca-produto"),
    btnBuscarProduto: document.getElementById("btn-buscar-produto"),
    produtosResultado: document.getElementById("pdv-produtos-resultado"),

    carrinhoLista: document.getElementById("pdv-carrinho-lista"),
    totalSubtotal: document.getElementById("pdv-total-subtotal"),
    totalDesconto: document.getElementById("pdv-total-desconto"),
    totalAcrescimo: document.getElementById("pdv-total-acrescimo"),
    totalFinal: document.getElementById("pdv-total-final"),

    formaPagamento: document.getElementById("pdv-forma-pagamento"),
    valorPagamento: document.getElementById("pdv-valor-pagamento"),
    btnFinalizarVenda: document.getElementById("btn-finalizar-venda"),

    producaoLista: document.getElementById("pdv-producao-lista"),
    btnAtualizarProducao: document.getElementById("btn-atualizar-producao"),
  };

  function setText(el, value) {
    if (!el) return;
    el.textContent = value ?? "";
  }

  function setHtml(el, value) {
    if (!el) return;
    el.innerHTML = value ?? "";
  }

  function setValue(el, value) {
    if (!el) return;
    el.value = value ?? "";
  }

  function toNumber(value, fallback = 0) {
    const normalized = String(value ?? "")
      .replace(/\./g, "")
      .replace(",", ".")
      .trim();

    const parsed = Number(normalized);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function formatMoney(value) {
    return toNumber(value, 0).toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
    });
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function showAlert(message, type = "info") {
    if (!els.alertaGeral) {
      console[type === "danger" ? "error" : "log"](message);
      return;
    }

    const classMap = {
      info: "pdv-alert pdv-alert-info",
      warning: "pdv-alert pdv-alert-warning",
      danger: "pdv-alert pdv-alert-danger",
    };

    els.alertaGeral.className = classMap[type] || classMap.info;
    els.alertaGeral.textContent = message;
  }

  async function request(url, options = {}) {
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });

    const contentType = response.headers.get("content-type") || "";
    const isJson = contentType.includes("application/json");
    const data = isJson ? await response.json() : await response.text();

    if (!response.ok) {
      console.error("Erro HTTP", {
        url,
        status: response.status,
        response: data,
      });

      const detail =
        (isJson && (data.detail || data.message)) ||
        (typeof data === "string" ? data : null) ||
        "Não foi possível concluir a operação.";

      throw new Error(detail);
    }

    return data;
  }

  function getEmpresaId() {
    const empresaId = toNumber(els.empresaId?.value, 1);
    state.empresaId = empresaId > 0 ? empresaId : 1;
    return state.empresaId;
  }

  function getCaixaSessaoId() {
    return state.caixaAtual?.id || null;
  }

  function hasCaixaAberto() {
    return !!state.caixaAtual && state.caixaAtual.status === "ABERTO";
  }

  function hasVendaAtual() {
    return !!state.vendaAtual;
  }

  function hasVendaAberta() {
    return !!state.vendaAtual && state.vendaAtual.status === "ABERTA";
  }

  function isWalkIn() {
    return hasVendaAberta() && state.vendaAtual.modo_cliente === "WALK_IN";
  }

  function isRegisteredClient() {
    return hasVendaAberta() && state.vendaAtual.modo_cliente === "REGISTERED_CLIENT";
  }

  function promptNumber(message, defaultValue = "") {
    const value = window.prompt(message, String(defaultValue ?? ""));
    if (value === null) return null;

    const number = toNumber(value, NaN);
    if (!Number.isFinite(number)) {
      throw new Error("Valor numérico inválido informado.");
    }

    return number;
  }

  function promptText(message, defaultValue = "") {
    const value = window.prompt(message, defaultValue ?? "");
    if (value === null) return null;
    return String(value).trim();
  }

  async function carregarOperadores(termo = "") {
    const empresaId = getEmpresaId();
    const query = termo ? `&q=${encodeURIComponent(termo)}` : "";
    const data = await request(`/api/pdv/operadores?empresa_id=${empresaId}${query}&limite=100`);
    state.operadores = Array.isArray(data) ? data : [];
    return state.operadores;
  }

  function montarTextoSelecaoOperadores(operadores, titulo) {
    const linhas = operadores.map((operador, index) => {
      const tipo = operador.tipo ? ` (${operador.tipo})` : "";
      return `${index + 1} - ${operador.nome}${tipo}`;
    });

    return `${titulo}\n\n${linhas.join("\n")}\n\nDigite o número da opção desejada.`;
  }

  async function escolherOperador({
    titulo = "Selecione o funcionário",
    termoInicial = "",
    obrigatorio = true,
    permitirVazio = false,
  } = {}) {
    let termo = termoInicial;

    if (!termo) {
      termo = promptText(
        `${titulo}\n\nDigite parte do nome do funcionário para pesquisar:`,
        ""
      );
      if (termo === null) return null;
    }

    let operadores = await carregarOperadores(termo);

    if (!operadores.length) {
      const novoTermo = promptText(
        "Nenhum funcionário encontrado. Digite outro nome para pesquisar:",
        ""
      );
      if (novoTermo === null) {
        if (permitirVazio) return null;
        throw new Error("Nenhum funcionário selecionado.");
      }

      operadores = await carregarOperadores(novoTermo);
    }

    if (!operadores.length) {
      if (permitirVazio) return null;
      throw new Error("Nenhum funcionário ativo encontrado para a empresa.");
    }

    if (operadores.length === 1) {
      return operadores[0];
    }

    const escolha = promptText(
      montarTextoSelecaoOperadores(operadores, titulo),
      "1"
    );

    if (escolha === null || escolha === "") {
      if (permitirVazio) return null;
      if (obrigatorio) {
        throw new Error("Seleção de funcionário é obrigatória.");
      }
      return null;
    }

    const indice = Number(escolha) - 1;
    if (!Number.isInteger(indice) || indice < 0 || indice >= operadores.length) {
      throw new Error("Opção de funcionário inválida.");
    }

    return operadores[indice];
  }

  async function escolherGerente({
    titulo = "Selecione o gerente autorizador",
    obrigatorio = false,
  } = {}) {
    const gerente = await escolherOperador({
      titulo,
      termoInicial: "",
      obrigatorio,
      permitirVazio: !obrigatorio,
    });

    if (!gerente) {
      return null;
    }

    const tipo = String(gerente.tipo || "").toLowerCase();
    if (!["gerente", "admin"].includes(tipo)) {
      throw new Error("O funcionário selecionado não possui perfil gerencial.");
    }

    return gerente;
  }

  async function escolherOperadorPadrao({
    titulo,
    preferidoId = null,
    obrigatorio = true,
  }) {
    if (preferidoId) {
      const operadores = await carregarOperadores("");
      const preferido = operadores.find((item) => Number(item.id) === Number(preferidoId));
      if (preferido) {
        const confirmar = window.confirm(
          `${titulo}\n\nUsar ${preferido.nome}?`
        );
        if (confirmar) {
          return preferido;
        }
      }
    }

    return escolherOperador({ titulo, obrigatorio });
  }

  function renderCaixa() {
    const caixa = state.caixaAtual;
    const resumo = state.caixaResumo;

    if (!caixa) {
      setText(els.caixaStatus, "Fechado");
      setText(els.caixaOperador, "-");
      setText(els.caixaAbertura, formatMoney(0));
      setText(els.caixaSaldo, formatMoney(0));
      return;
    }

    const operadorNome =
      caixa.usuario_responsavel?.nome ||
      caixa.usuario_abertura?.nome ||
      (caixa.usuario_responsavel_id ? `Usuário #${caixa.usuario_responsavel_id}` : "-");

    setText(els.caixaStatus, caixa.status || "-");
    setText(els.caixaOperador, operadorNome);
    setText(els.caixaAbertura, formatMoney(caixa.valor_abertura_informado || 0));
    setText(els.caixaSaldo, formatMoney(resumo?.saldo_dinheiro_esperado || 0));
  }

  function renderVendaContexto() {
    const venda = state.vendaAtual;

    if (!venda) {
      setText(els.vendaCliente, "Nenhuma venda iniciada");
      setText(els.vendaMeta, "Abra uma venda balcão ou puxe da produção.");
      setText(els.vendaNumero, "Sem venda");
      setText(els.vendaModo, "-");
      return;
    }

    const clienteNome =
      venda.cliente?.nome ||
      venda.nome_cliente_snapshot ||
      (venda.modo_cliente === "WALK_IN" ? "Venda balcão" : "Cliente não identificado");

    setText(els.vendaCliente, clienteNome);
    setText(els.vendaMeta, `Status: ${venda.status} | Origem: ${venda.origem || "-"}`);
    setText(els.vendaNumero, venda.numero_venda || `Venda #${venda.id}`);
    setText(
      els.vendaModo,
      venda.modo_cliente === "WALK_IN" ? "Balcão" : "Cliente cadastrado"
    );
  }

  function renderTotais() {
    const venda = state.vendaAtual;

    setText(els.totalSubtotal, formatMoney(venda?.subtotal || 0));
    setText(els.totalDesconto, formatMoney(venda?.desconto_valor || 0));
    setText(els.totalAcrescimo, formatMoney(venda?.acrescimo_valor || 0));
    setText(els.totalFinal, formatMoney(venda?.valor_total || 0));

    if (els.valorPagamento) {
      setValue(els.valorPagamento, venda ? toNumber(venda.valor_total, 0).toFixed(2) : "");
    }
  }

  function renderCarrinho() {
    const itens = state.vendaAtual?.itens || [];

    if (!els.carrinhoLista) return;

    if (!itens.length) {
      setHtml(els.carrinhoLista, '<div class="pdv-empty">Nenhum item adicionado.</div>');
      return;
    }

    setHtml(
      els.carrinhoLista,
      itens
        .map((item) => {
          const badgeClass = item.tipo_item === "SERVICE" ? "pdv-badge-blue" : "pdv-badge-green";
          const badgeText = item.tipo_item === "SERVICE" ? "Atendimento" : "Produto";

          return `
            <div class="pdv-carrinho-item">
              <div class="pdv-carrinho-info">
                <div class="pdv-carrinho-title">${escapeHtml(item.descricao_snapshot || "Item sem descrição")}</div>
                <div class="pdv-carrinho-meta">
                  Qtde: ${toNumber(item.quantidade, 0)} |
                  Unitário: ${formatMoney(item.valor_unitario)} |
                  Desconto: ${formatMoney(item.desconto_valor)}
                </div>
                ${item.observacao ? `<div class="pdv-carrinho-meta">${escapeHtml(item.observacao)}</div>` : ""}
              </div>

              <div class="pdv-carrinho-side">
                <span class="pdv-badge ${badgeClass}">${badgeText}</span>
                <strong>${formatMoney(item.valor_total)}</strong>
                ${
                  hasVendaAberta()
                    ? `
                      <button
                        class="pdv-btn pdv-btn-danger pdv-btn-sm btn-remover-item"
                        type="button"
                        data-item-id="${item.id}"
                      >
                        Remover
                      </button>
                    `
                    : ""
                }
              </div>
            </div>
          `;
        })
        .join("")
    );

    document.querySelectorAll(".btn-remover-item").forEach((button) => {
      button.addEventListener("click", async () => {
        const itemId = toNumber(button.dataset.itemId, 0);
        if (!itemId || !state.vendaAtual) return;

        const confirmar = window.confirm("Deseja remover este item da venda?");
        if (!confirmar) return;

        try {
          const venda = await request(`/api/pdv/vendas/${state.vendaAtual.id}/itens/${itemId}`, {
            method: "DELETE",
          });
          state.vendaAtual = venda;
          renderVenda();
          showAlert("Item removido da venda.", "info");
        } catch (error) {
          showAlert(error.message, "danger");
        }
      });
    });
  }

  function renderBuscaResultadosVazio(message) {
    if (!els.produtosResultado) return;
    setHtml(els.produtosResultado, `<div class="pdv-empty">${escapeHtml(message)}</div>`);
  }

  function renderClientesEncontrados() {
    if (!els.produtosResultado) return;

    if (!state.clientesEncontrados.length) {
      renderBuscaResultadosVazio("Nenhum cliente encontrado.");
      return;
    }

    setHtml(
      els.produtosResultado,
      state.clientesEncontrados
        .map((cliente) => {
          const meta = [];
          if (cliente.cpf) meta.push(`CPF: ${escapeHtml(cliente.cpf)}`);
          if (cliente.telefone) meta.push(`Tel.: ${escapeHtml(cliente.telefone)}`);

          return `
            <div class="pdv-result-item">
              <div>
                <div class="pdv-result-title">${escapeHtml(cliente.nome)}</div>
                <div class="pdv-result-subtitle">${meta.join(" | ") || "Cliente sem dados complementares"}</div>
              </div>
              <button
                class="pdv-btn pdv-btn-primary pdv-btn-sm btn-iniciar-venda-cliente"
                type="button"
                data-cliente-id="${cliente.id}"
              >
                Iniciar venda
              </button>
            </div>
          `;
        })
        .join("")
    );

    document.querySelectorAll(".btn-iniciar-venda-cliente").forEach((button) => {
      button.addEventListener("click", async () => {
        const clienteId = toNumber(button.dataset.clienteId, 0);
        if (!clienteId) return;
        await iniciarVendaCliente(clienteId);
      });
    });
  }

  function renderSugestaoProduto(termo) {
    if (!els.produtosResultado) return;

    const termoSeguro = escapeHtml(termo || "");

    setHtml(
      els.produtosResultado,
      `
        <div class="pdv-result-item">
          <div>
            <div class="pdv-result-title">${termoSeguro || "Produto avulso"}</div>
            <div class="pdv-result-subtitle">
              Sem catálogo integrado neste passo. Use este item para adicionar produto avulso à venda atual.
            </div>
          </div>
          <button id="btn-adicionar-produto-avulso" class="pdv-btn pdv-btn-primary pdv-btn-sm" type="button">
            Adicionar à venda
          </button>
        </div>
      `
    );

    document.getElementById("btn-adicionar-produto-avulso")?.addEventListener("click", async () => {
      await adicionarProdutoAvulso(termo);
    });
  }

  function renderProducao() {
    if (!els.producaoLista) return;

    if (!state.producaoPronta.length) {
      setHtml(els.producaoLista, '<div class="pdv-empty">Nenhum item pronto para cobrança.</div>');
      return;
    }

    setHtml(
      els.producaoLista,
      state.producaoPronta
        .map((item) => {
          return `
            <div class="pdv-prod-item">
              <div class="pdv-prod-item-top">
                <div>
                  <div class="pdv-prod-item-title">${escapeHtml(item.descricao)}</div>
                  <div class="pdv-prod-item-subtitle">
                    Cliente: ${escapeHtml(item.cliente_nome || "-")}
                    ${item.pet_nome ? ` | Pet: ${escapeHtml(item.pet_nome)}` : ""}
                  </div>
                </div>
                <strong>${formatMoney(item.valor_total)}</strong>
              </div>

              <div style="display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap;">
                <span class="pdv-badge pdv-badge-blue">Pronto para cobrança</span>
                <button
                  class="pdv-btn pdv-btn-primary pdv-btn-sm btn-puxar-producao"
                  type="button"
                  data-atendimento-id="${item.atendimento_id}"
                  data-cliente-id="${item.cliente_id}"
                >
                  Puxar para venda
                </button>
              </div>
            </div>
          `;
        })
        .join("")
    );

    document.querySelectorAll(".btn-puxar-producao").forEach((button) => {
      button.addEventListener("click", async () => {
        const atendimentoId = toNumber(button.dataset.atendimentoId, 0);
        const clienteId = toNumber(button.dataset.clienteId, 0);
        if (!atendimentoId || !clienteId) return;

        try {
          await puxarProducaoParaVenda(atendimentoId, clienteId);
        } catch (error) {
          showAlert(error.message, "danger");
        }
      });
    });
  }

  function renderVenda() {
    renderVendaContexto();
    renderTotais();
    renderCarrinho();
  }

  async function carregarCaixaAtual() {
    const empresaId = getEmpresaId();
    state.caixaResumo = null;

    try {
      const caixa = await request(`/api/caixa/atual?empresa_id=${empresaId}`);
      state.caixaAtual = caixa || null;

      if (state.caixaAtual?.id) {
        state.caixaResumo = await request(`/api/caixa/sessoes/${state.caixaAtual.id}/resumo`);
      }
    } catch (error) {
      state.caixaAtual = null;
      state.caixaResumo = null;
      showAlert(error.message, "danger");
    }

    renderCaixa();
  }

  async function carregarProducao() {
    try {
      const empresaId = getEmpresaId();
      const clienteId = isRegisteredClient() ? state.vendaAtual.cliente_id : null;
      let url = `/api/pdv/atendimentos/prontos?empresa_id=${empresaId}`;

      if (clienteId) {
        url += `&cliente_id=${clienteId}`;
      }

      const data = await request(url);
      state.producaoPronta = Array.isArray(data) ? data : [];
      renderProducao();
    } catch (error) {
      state.producaoPronta = [];
      renderProducao();
      showAlert(error.message, "danger");
    }
  }

  async function abrirCaixa() {
    try {
      const empresaId = getEmpresaId();

      const operadorResponsavel = await escolherOperador({
        titulo: "Selecione o funcionário responsável pelo caixa",
        obrigatorio: true,
      });
      if (!operadorResponsavel) return;

      const usuarioAbertura = await escolherOperadorPadrao({
        titulo: "Selecione o funcionário que está abrindo o caixa",
        preferidoId: operadorResponsavel.id,
        obrigatorio: true,
      });
      if (!usuarioAbertura) return;

      const valorAbertura = promptNumber("Valor inicial em dinheiro:", "0.00");
      if (valorAbertura === null) return;

      const observacoes = promptText("Observações da abertura (opcional):", "") ?? null;
      const motivoDiferenca = promptText(
        "Motivo da diferença de abertura, se existir (opcional):",
        ""
      );

      let gerente = null;
      let senhaGerente = null;

      const desejaInformarGerente = window.confirm(
        "Deseja informar um gerente autorizador agora?"
      );

      if (desejaInformarGerente) {
        gerente = await escolherGerente({
          titulo: "Selecione o gerente autorizador da abertura",
          obrigatorio: true,
        });
        senhaGerente = promptText("Senha do gerente autorizador:", "") || null;
      }

      const payload = {
        empresa_id: empresaId,
        usuario_responsavel_id: operadorResponsavel.id,
        usuario_abertura_id: usuarioAbertura.id,
        valor_abertura_informado: valorAbertura,
        observacoes: observacoes || null,
        motivo_diferenca_abertura: motivoDiferenca || null,
        gerente_abertura_id: gerente ? gerente.id : null,
        senha_gerente: senhaGerente || null,
      };

      const result = await request("/api/caixa/abrir", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      state.caixaAtual = result.caixa_sessao || null;
      if (state.caixaAtual?.id) {
        state.caixaResumo = await request(`/api/caixa/sessoes/${state.caixaAtual.id}/resumo`);
      }

      renderCaixa();
      showAlert(result.mensagem || "Caixa aberto com sucesso.", "info");
    } catch (error) {
      showAlert(error.message, "danger");
    }
  }

  async function registrarSangria() {
    try {
      if (!hasCaixaAberto()) {
        showAlert("Abra o caixa antes de registrar sangria.", "warning");
        return;
      }

      const valor = promptNumber("Valor da sangria:");
      if (valor === null) return;

      const usuario = await escolherOperadorPadrao({
        titulo: "Selecione o funcionário que está registrando a sangria",
        preferidoId: state.caixaAtual?.usuario_responsavel_id || null,
        obrigatorio: true,
      });
      if (!usuario) return;

      const motivo = promptText("Motivo da sangria:", "Retirada de numerário");
      if (motivo === null || !motivo) {
        showAlert("Motivo é obrigatório para sangria.", "warning");
        return;
      }

      const observacoes = promptText("Observações da sangria (opcional):", "") ?? null;

      let gerente = null;
      let senhaGerente = null;

      const desejaInformarGerente = window.confirm(
        "Deseja informar um gerente autorizador para a sangria?"
      );
      if (desejaInformarGerente) {
        gerente = await escolherGerente({
          titulo: "Selecione o gerente autorizador da sangria",
          obrigatorio: true,
        });
        senhaGerente = promptText("Senha do gerente autorizador:", "") || null;
      }

      const payload = {
        empresa_id: getEmpresaId(),
        caixa_sessao_id: state.caixaAtual.id,
        valor,
        usuario_id: usuario.id,
        motivo,
        observacoes: observacoes || null,
        gerente_autorizador_id: gerente ? gerente.id : null,
        senha_gerente: senhaGerente || null,
      };

      const result = await request("/api/caixa/sangria", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      state.caixaAtual = result.caixa_sessao || state.caixaAtual;
      if (state.caixaAtual?.id) {
        state.caixaResumo = await request(`/api/caixa/sessoes/${state.caixaAtual.id}/resumo`);
      }

      renderCaixa();
      showAlert(result.mensagem || "Sangria registrada com sucesso.", "info");
    } catch (error) {
      showAlert(error.message, "danger");
    }
  }

  async function registrarSuprimento() {
    try {
      if (!hasCaixaAberto()) {
        showAlert("Abra o caixa antes de registrar suprimento.", "warning");
        return;
      }

      const valor = promptNumber("Valor do suprimento:");
      if (valor === null) return;

      const usuario = await escolherOperadorPadrao({
        titulo: "Selecione o funcionário que está registrando o suprimento",
        preferidoId: state.caixaAtual?.usuario_responsavel_id || null,
        obrigatorio: true,
      });
      if (!usuario) return;

      const motivo = promptText("Motivo do suprimento:", "Reforço de caixa");
      if (motivo === null || !motivo) {
        showAlert("Motivo é obrigatório para suprimento.", "warning");
        return;
      }

      const observacoes = promptText("Observações do suprimento (opcional):", "") ?? null;

      let gerente = null;
      let senhaGerente = null;

      const desejaInformarGerente = window.confirm(
        "Deseja informar um gerente autorizador para o suprimento?"
      );
      if (desejaInformarGerente) {
        gerente = await escolherGerente({
          titulo: "Selecione o gerente autorizador do suprimento",
          obrigatorio: true,
        });
        senhaGerente = promptText("Senha do gerente autorizador:", "") || null;
      }

      const payload = {
        empresa_id: getEmpresaId(),
        caixa_sessao_id: state.caixaAtual.id,
        valor,
        usuario_id: usuario.id,
        motivo,
        observacoes: observacoes || null,
        gerente_autorizador_id: gerente ? gerente.id : null,
        senha_gerente: senhaGerente || null,
      };

      const result = await request("/api/caixa/suprimento", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      state.caixaAtual = result.caixa_sessao || state.caixaAtual;
      if (state.caixaAtual?.id) {
        state.caixaResumo = await request(`/api/caixa/sessoes/${state.caixaAtual.id}/resumo`);
      }

      renderCaixa();
      showAlert(result.mensagem || "Suprimento registrado com sucesso.", "info");
    } catch (error) {
      showAlert(error.message, "danger");
    }
  }

  async function fecharCaixa() {
    try {
      if (!hasCaixaAberto()) {
        showAlert("Nenhum caixa aberto para fechamento.", "warning");
        return;
      }

      const usuarioFechamento = await escolherOperadorPadrao({
        titulo: "Selecione o funcionário que está fechando o caixa",
        preferidoId: state.caixaAtual?.usuario_responsavel_id || null,
        obrigatorio: true,
      });
      if (!usuarioFechamento) return;

      const valorFechamento = promptNumber(
        "Contagem cega: valor total em caixa no fechamento:"
      );
      if (valorFechamento === null) return;

      const motivoDiferenca = promptText(
        "Motivo da diferença no fechamento, se existir (opcional):",
        ""
      );

      let gerente = null;
      let senhaGerente = null;

      const desejaInformarGerente = window.confirm(
        "Deseja informar um gerente autorizador para o fechamento?"
      );
      if (desejaInformarGerente) {
        gerente = await escolherGerente({
          titulo: "Selecione o gerente autorizador do fechamento",
          obrigatorio: true,
        });
        senhaGerente = promptText("Senha do gerente autorizador:", "") || null;
      }

      const payload = {
        usuario_fechamento_id: usuarioFechamento.id,
        valor_fechamento_informado: valorFechamento,
        motivo_diferenca_fechamento: motivoDiferenca || null,
        gerente_fechamento_id: gerente ? gerente.id : null,
        senha_gerente: senhaGerente || null,
      };

      const result = await request(`/api/caixa/sessoes/${state.caixaAtual.id}/fechar`, {
        method: "POST",
        body: JSON.stringify(payload),
      });

      state.caixaAtual = result.caixa_sessao || null;
      state.caixaResumo = null;
      renderCaixa();
      showAlert(result.mensagem || "Caixa fechado com sucesso.", "info");
    } catch (error) {
      showAlert(error.message, "danger");
    }
  }

  async function iniciarVendaCliente(clienteId) {
    try {
      if (!hasCaixaAberto()) {
        showAlert("É necessário ter um caixa aberto para iniciar a venda.", "warning");
        return;
      }

      if (hasVendaAberta()) {
        showAlert("Já existe uma venda aberta. Finalize ou cancele antes de iniciar outra.", "warning");
        return;
      }

      const payload = {
        empresa_id: getEmpresaId(),
        caixa_sessao_id: getCaixaSessaoId(),
        modo_cliente: "REGISTERED_CLIENT",
        cliente_id: clienteId,
        observacoes: null,
      };

      const venda = await request("/api/pdv/vendas", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      state.vendaAtual = venda;
      state.clientesEncontrados = [];
      renderVenda();
      renderBuscaResultadosVazio("Venda iniciada. Use a busca para adicionar produto avulso.");
      await carregarProducao();
      showAlert("Venda com cliente cadastrado iniciada com sucesso.", "info");
    } catch (error) {
      showAlert(error.message, "danger");
    }
  }

  async function iniciarVendaBalcao() {
    try {
      if (!hasCaixaAberto()) {
        showAlert("É necessário ter um caixa aberto para iniciar a venda.", "warning");
        return;
      }

      if (hasVendaAberta()) {
        showAlert("Já existe uma venda aberta. Finalize ou cancele antes de iniciar outra.", "warning");
        return;
      }

      const payload = {
        empresa_id: getEmpresaId(),
        caixa_sessao_id: getCaixaSessaoId(),
        modo_cliente: "WALK_IN",
        nome_cliente_snapshot: "Venda balcão",
        observacoes: null,
      };

      const venda = await request("/api/pdv/vendas", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      state.vendaAtual = venda;
      renderVenda();
      renderBuscaResultadosVazio("Venda balcão iniciada. Use a busca para adicionar produto avulso.");
      await carregarProducao();
      showAlert("Venda balcão iniciada com sucesso.", "info");
    } catch (error) {
      showAlert(error.message, "danger");
    }
  }

  async function buscarClientesParaIniciarVenda() {
    const termo = (els.buscaProduto?.value || "").trim();
    if (!termo) {
      showAlert("Digite um nome, CPF ou telefone para localizar o cliente.", "warning");
      return;
    }

    try {
      const empresaId = getEmpresaId();
      const data = await request(
        `/api/pdv/clientes/busca?empresa_id=${empresaId}&q=${encodeURIComponent(termo)}&limite=20`
      );
      state.clientesEncontrados = Array.isArray(data) ? data : [];
      renderClientesEncontrados();

      if (!state.clientesEncontrados.length) {
        showAlert("Nenhum cliente encontrado para iniciar venda.", "warning");
      } else {
        showAlert("Selecione o cliente para abrir a venda no caixa atual.", "info");
      }
    } catch (error) {
      showAlert(error.message, "danger");
    }
  }

  async function adicionarProdutoAvulso(termoBase) {
    try {
      if (!hasVendaAberta()) {
        showAlert("Abra uma venda antes de adicionar produtos.", "warning");
        return;
      }

      const produtoIdPadrao = /^\d+$/.test(String(termoBase || "").trim())
        ? String(termoBase).trim()
        : "";

      const produtoId = promptNumber("ID do produto:", produtoIdPadrao);
      if (produtoId === null) return;

      const descricao = promptText("Descrição do produto:", termoBase || "Produto avulso");
      if (descricao === null || !descricao) {
        showAlert("Descrição do produto é obrigatória.", "warning");
        return;
      }

      const quantidade = promptNumber("Quantidade:", "1");
      if (quantidade === null) return;

      const valorUnitario = promptNumber("Valor unitário:");
      if (valorUnitario === null) return;

      const desconto = promptNumber("Desconto do item:", "0");
      if (desconto === null) return;

      const observacao = promptText("Observação do item (opcional):", "") ?? null;

      const payload = {
        tipo_item: "PRODUCT",
        produto_id: produtoId,
        descricao_snapshot: descricao,
        quantidade,
        valor_unitario: valorUnitario,
        desconto_valor: desconto,
        observacao: observacao || null,
      };

      const venda = await request(`/api/pdv/vendas/${state.vendaAtual.id}/itens`, {
        method: "POST",
        body: JSON.stringify(payload),
      });

      state.vendaAtual = venda;
      renderVenda();
      showAlert("Produto adicionado à venda.", "info");
    } catch (error) {
      showAlert(error.message, "danger");
    }
  }

  async function puxarProducaoParaVenda(atendimentoId, clienteId) {
    if (!hasCaixaAberto()) {
      showAlert("É necessário ter um caixa aberto para puxar da produção.", "warning");
      return;
    }

    if (!hasVendaAberta()) {
      await iniciarVendaCliente(clienteId);
    }

    if (!hasVendaAberta()) {
      return;
    }

    if (isWalkIn()) {
      showAlert(
        "A venda atual está em modo balcão. Cancele ou finalize para puxar atendimento de cliente cadastrado.",
        "warning"
      );
      return;
    }

    if (state.vendaAtual.cliente_id !== clienteId) {
      showAlert("Não é permitido misturar clientes na mesma venda.", "warning");
      return;
    }

    const payload = {
      tipo_item: "SERVICE",
      atendimento_clinico_id: atendimentoId,
      desconto_valor: 0,
    };

    const venda = await request(`/api/pdv/vendas/${state.vendaAtual.id}/itens`, {
      method: "POST",
      body: JSON.stringify(payload),
    });

    state.vendaAtual = venda;
    renderVenda();
    await carregarProducao();
    showAlert("Item da produção adicionado à venda.", "info");
  }

  async function finalizarVendaAtual() {
    try {
      if (!hasVendaAberta()) {
        showAlert("Não há venda aberta para finalizar.", "warning");
        return;
      }

      if (!hasCaixaAberto()) {
        showAlert("É necessário ter um caixa aberto para finalizar a venda.", "warning");
        return;
      }

      const valorTotal = toNumber(state.vendaAtual?.valor_total, 0);
      const valorPagamento = toNumber(els.valorPagamento?.value, NaN);

      if (!Number.isFinite(valorPagamento) || valorPagamento <= 0) {
        showAlert("Informe um valor de pagamento válido.", "warning");
        return;
      }

      if (Math.abs(valorPagamento - valorTotal) > 0.0001) {
        showAlert("A venda só pode ser finalizada com pagamento integral.", "warning");
        return;
      }

      const usuarioRecebimento = await escolherOperadorPadrao({
        titulo: "Selecione o funcionário que está recebendo a venda",
        preferidoId: state.caixaAtual?.usuario_responsavel_id || null,
        obrigatorio: true,
      });
      if (!usuarioRecebimento) return;

      const referencia = promptText("Referência do pagamento (opcional):", "") ?? null;
      const observacoesPagamento = promptText("Observações do pagamento (opcional):", "") ?? null;

      const confirmar = window.confirm(
        `Confirmar fechamento da venda no valor de ${formatMoney(valorTotal)}?`
      );
      if (!confirmar) return;

      const payload = {
        pagamento: {
          forma_pagamento: els.formaPagamento?.value || "DINHEIRO",
          valor: valorPagamento,
          referencia: referencia || null,
          observacoes: observacoesPagamento || null,
          usuario_id: usuarioRecebimento.id,
        },
        observacoes: null,
      };

      const result = await request(`/api/pdv/vendas/${state.vendaAtual.id}/checkout`, {
        method: "POST",
        body: JSON.stringify(payload),
      });

      state.vendaAtual = result.venda || null;
      renderVenda();
      await carregarCaixaAtual();
      await carregarProducao();
      showAlert(result.mensagem || "Venda finalizada com sucesso.", "info");
    } catch (error) {
      showAlert(error.message, "danger");
    }
  }

  async function cancelarVendaAtual() {
    try {
      if (!hasVendaAtual()) {
        showAlert("Nenhuma venda carregada para cancelamento.", "warning");
        return;
      }

      const confirmar = window.confirm("Deseja realmente cancelar a venda atual?");
      if (!confirmar) return;

      const usuarioCancelamento = await escolherOperadorPadrao({
        titulo: "Selecione o funcionário que está cancelando a venda",
        preferidoId:
          state.caixaAtual?.usuario_responsavel_id ||
          state.vendaAtual?.usuario_abertura_id ||
          null,
        obrigatorio: true,
      });
      if (!usuarioCancelamento) return;

      let motivo = promptText(
        "Motivo do cancelamento:",
        state.vendaAtual.status === "FECHADA"
          ? "Cancelamento manual de venda fechada"
          : "Cancelamento manual"
      );
      if (motivo === null) return;
      motivo = motivo || null;

      let gerente = null;
      let senhaGerente = null;

      if (state.vendaAtual.status === "FECHADA") {
        gerente = await escolherGerente({
          titulo: "Selecione o gerente autorizador do cancelamento",
          obrigatorio: true,
        });
        if (!gerente) return;

        senhaGerente = promptText("Senha do gerente autorizador:", "");
        if (senhaGerente === null || !senhaGerente) {
          showAlert("Senha do gerente é obrigatória para cancelar venda fechada.", "warning");
          return;
        }

        if (!motivo) {
          showAlert("Motivo é obrigatório para cancelamento de venda fechada.", "warning");
          return;
        }
      }

      const payload = {
        motivo_cancelamento: motivo,
        usuario_cancelamento_id: usuarioCancelamento.id,
        gerente_autorizador_id: gerente ? gerente.id : null,
        senha_gerente: senhaGerente || null,
      };

      const result = await request(`/api/pdv/vendas/${state.vendaAtual.id}/cancelar`, {
        method: "POST",
        body: JSON.stringify(payload),
      });

      state.vendaAtual = result.venda || null;
      renderVenda();
      await carregarCaixaAtual();
      await carregarProducao();
      showAlert(result.mensagem || "Venda cancelada com sucesso.", "info");
    } catch (error) {
      showAlert(error.message, "danger");
    }
  }

  async function executarBuscaPrincipal() {
    const termo = (els.buscaProduto?.value || "").trim();

    if (!termo) {
      renderBuscaResultadosVazio(
        hasVendaAberta()
          ? "Digite o nome ou código para adicionar produto avulso."
          : "Digite nome, CPF ou telefone para localizar cliente."
      );
      return;
    }

    if (hasVendaAberta()) {
      renderSugestaoProduto(termo);
      showAlert("Confirme os dados do item para adicionar produto avulso à venda.", "info");
      return;
    }

    await buscarClientesParaIniciarVenda();
  }

  function bindEvents() {
    els.btnAbrirCaixa?.addEventListener("click", abrirCaixa);
    els.btnSangria?.addEventListener("click", registrarSangria);
    els.btnSuprimento?.addEventListener("click", registrarSuprimento);
    els.btnFecharCaixa?.addEventListener("click", fecharCaixa);

    els.btnVendaBalcao?.addEventListener("click", iniciarVendaBalcao);
    els.btnCancelarVenda?.addEventListener("click", cancelarVendaAtual);
    els.btnFinalizarVenda?.addEventListener("click", finalizarVendaAtual);
    els.btnAtualizarProducao?.addEventListener("click", carregarProducao);
    els.btnBuscarProduto?.addEventListener("click", executarBuscaPrincipal);

    els.buscaProduto?.addEventListener("keydown", async (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        await executarBuscaPrincipal();
      }
    });

    els.empresaId?.addEventListener("change", async () => {
      state.vendaAtual = null;
      state.clientesEncontrados = [];
      state.operadores = [];
      renderVenda();
      renderBuscaResultadosVazio("Empresa alterada. Recarregue o fluxo da venda.");
      await carregarCaixaAtual();
      await carregarProducao();
    });
  }

  async function init() {
    getEmpresaId();
    renderCaixa();
    renderVenda();
    renderBuscaResultadosVazio(
      "Digite nome, CPF ou telefone para localizar cliente, ou abra uma venda balcão."
    );
    renderProducao();
    bindEvents();
    await carregarOperadores("");
    await carregarCaixaAtual();
    await carregarProducao();
  }

  init();
})();