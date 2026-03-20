(function () {
  const state = {
    empresaId: 1,
    caixaAtual: null,
    caixaResumo: null,
    vendaAtual: null,
    clientesEncontrados: [],
    producaoPronta: [],
    operadores: [],
    modalContext: {},
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

    modalOverlay: document.getElementById("pdv-modal-overlay"),

    modalAbrirCaixa: document.getElementById("modal-abrir-caixa"),
    modalSangria: document.getElementById("modal-sangria"),
    modalSuprimento: document.getElementById("modal-suprimento"),
    modalFecharCaixa: document.getElementById("modal-fechar-caixa"),

    caixaAberturaOperadorBusca: document.getElementById("caixa-abertura-operador-busca"),
    btnBuscarOperadorAbertura: document.getElementById("btn-buscar-operador-abertura"),
    caixaAberturaOperadorLista: document.getElementById("caixa-abertura-operador-lista"),
    caixaAberturaOperadorId: document.getElementById("caixa-abertura-operador-id"),
    caixaAberturaOperadorNome: document.getElementById("caixa-abertura-operador-nome"),
    caixaValorAbertura: document.getElementById("caixa-valor-abertura"),
    caixaObservacoesAbertura: document.getElementById("caixa-observacoes-abertura"),
    caixaAberturaDivergenciaBox: document.getElementById("caixa-abertura-divergencia-box"),
    caixaMotivoDiferencaAbertura: document.getElementById("caixa-motivo-diferenca-abertura"),
    caixaGerenteAberturaBusca: document.getElementById("caixa-gerente-abertura-busca"),
    btnBuscarGerenteAbertura: document.getElementById("btn-buscar-gerente-abertura"),
    caixaGerenteAberturaLista: document.getElementById("caixa-gerente-abertura-lista"),
    caixaGerenteAberturaId: document.getElementById("caixa-gerente-abertura-id"),
    caixaGerenteAberturaNome: document.getElementById("caixa-gerente-abertura-nome"),
    caixaSenhaGerenteAbertura: document.getElementById("caixa-senha-gerente-abertura"),
    btnConfirmarAbrirCaixa: document.getElementById("btn-confirmar-abrir-caixa"),

    caixaSangriaOperadorBusca: document.getElementById("caixa-sangria-operador-busca"),
    btnBuscarOperadorSangria: document.getElementById("btn-buscar-operador-sangria"),
    caixaSangriaOperadorLista: document.getElementById("caixa-sangria-operador-lista"),
    caixaSangriaOperadorId: document.getElementById("caixa-sangria-operador-id"),
    caixaSangriaOperadorNome: document.getElementById("caixa-sangria-operador-nome"),
    caixaSangriaValor: document.getElementById("caixa-sangria-valor"),
    caixaSangriaMotivo: document.getElementById("caixa-sangria-motivo"),
    caixaSangriaObservacoes: document.getElementById("caixa-sangria-observacoes"),
    caixaSangriaGerenteBox: document.getElementById("caixa-sangria-gerente-box"),
    caixaGerenteSangriaBusca: document.getElementById("caixa-gerente-sangria-busca"),
    btnBuscarGerenteSangria: document.getElementById("btn-buscar-gerente-sangria"),
    caixaGerenteSangriaLista: document.getElementById("caixa-gerente-sangria-lista"),
    caixaGerenteSangriaId: document.getElementById("caixa-gerente-sangria-id"),
    caixaGerenteSangriaNome: document.getElementById("caixa-gerente-sangria-nome"),
    caixaSenhaGerenteSangria: document.getElementById("caixa-senha-gerente-sangria"),
    btnConfirmarSangria: document.getElementById("btn-confirmar-sangria"),

    caixaSuprimentoOperadorBusca: document.getElementById("caixa-suprimento-operador-busca"),
    btnBuscarOperadorSuprimento: document.getElementById("btn-buscar-operador-suprimento"),
    caixaSuprimentoOperadorLista: document.getElementById("caixa-suprimento-operador-lista"),
    caixaSuprimentoOperadorId: document.getElementById("caixa-suprimento-operador-id"),
    caixaSuprimentoOperadorNome: document.getElementById("caixa-suprimento-operador-nome"),
    caixaSuprimentoValor: document.getElementById("caixa-suprimento-valor"),
    caixaSuprimentoMotivo: document.getElementById("caixa-suprimento-motivo"),
    caixaSuprimentoObservacoes: document.getElementById("caixa-suprimento-observacoes"),
    caixaSuprimentoGerenteBox: document.getElementById("caixa-suprimento-gerente-box"),
    caixaGerenteSuprimentoBusca: document.getElementById("caixa-gerente-suprimento-busca"),
    btnBuscarGerenteSuprimento: document.getElementById("btn-buscar-gerente-suprimento"),
    caixaGerenteSuprimentoLista: document.getElementById("caixa-gerente-suprimento-lista"),
    caixaGerenteSuprimentoId: document.getElementById("caixa-gerente-suprimento-id"),
    caixaGerenteSuprimentoNome: document.getElementById("caixa-gerente-suprimento-nome"),
    caixaSenhaGerenteSuprimento: document.getElementById("caixa-senha-gerente-suprimento"),
    btnConfirmarSuprimento: document.getElementById("btn-confirmar-suprimento"),

    caixaFechamentoSaldoEsperado: document.getElementById("caixa-fechamento-saldo-esperado"),
    caixaFechamentoOperadorBusca: document.getElementById("caixa-fechamento-operador-busca"),
    btnBuscarOperadorFechamento: document.getElementById("btn-buscar-operador-fechamento"),
    caixaFechamentoOperadorLista: document.getElementById("caixa-fechamento-operador-lista"),
    caixaFechamentoOperadorId: document.getElementById("caixa-fechamento-operador-id"),
    caixaFechamentoOperadorNome: document.getElementById("caixa-fechamento-operador-nome"),
    caixaFechamentoValor: document.getElementById("caixa-fechamento-valor"),
    caixaFechamentoDivergenciaBox: document.getElementById("caixa-fechamento-divergencia-box"),
    caixaMotivoDiferencaFechamento: document.getElementById("caixa-motivo-diferenca-fechamento"),
    caixaGerenteFechamentoBusca: document.getElementById("caixa-gerente-fechamento-busca"),
    btnBuscarGerenteFechamento: document.getElementById("btn-buscar-gerente-fechamento"),
    caixaGerenteFechamentoLista: document.getElementById("caixa-gerente-fechamento-lista"),
    caixaGerenteFechamentoId: document.getElementById("caixa-gerente-fechamento-id"),
    caixaGerenteFechamentoNome: document.getElementById("caixa-gerente-fechamento-nome"),
    caixaSenhaGerenteFechamento: document.getElementById("caixa-senha-gerente-fechamento"),
    btnConfirmarFecharCaixa: document.getElementById("btn-confirmar-fechar-caixa"),
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

  function showEl(el) {
    if (!el) return;
    el.classList.remove("pdv-hidden");
  }

  function hideEl(el) {
    if (!el) return;
    el.classList.add("pdv-hidden");
  }

  function toNumber(value, fallback = 0) {
    if (value === null || value === undefined || value === "") return fallback;
    const normalized = String(value).replace(/\./g, "").replace(",", ".").trim();
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
      success: "pdv-alert pdv-alert-success",
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
        (isJson && (data.detail || data.message || data.mensagem)) ||
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

  function normalizeTipoUsuario(tipo) {
    return String(tipo || "").trim().toLowerCase();
  }

  function requireText(value, message) {
    const v = String(value ?? "").trim();
    if (!v) throw new Error(message);
    return v;
  }

  function requirePositiveNumber(value, message) {
    const n = toNumber(value, NaN);
    if (!Number.isFinite(n) || n <= 0) {
      throw new Error(message);
    }
    return Number(n.toFixed(2));
  }

  function requireNonNegativeNumber(value, message) {
    const n = toNumber(value, NaN);
    if (!Number.isFinite(n) || n < 0) {
      throw new Error(message);
    }
    return Number(n.toFixed(2));
  }

  function clearSelection(listEl, idEl, nameEl, emptyMessage) {
    setValue(idEl, "");
    setValue(nameEl, "");
    setHtml(listEl, `<div class="pdv-empty-state">${escapeHtml(emptyMessage)}</div>`);
  }

  function setSelectedUser(listEl, idEl, nameEl, usuario, extraLabel = "") {
    if (!usuario) return;
    setValue(idEl, usuario.id);
    setValue(nameEl, usuario.nome || "");
    const tipo = usuario.tipo ? ` (${escapeHtml(usuario.tipo)})` : "";
    const email = usuario.email ? `<div class="pdv-selection-meta">${escapeHtml(usuario.email)}</div>` : "";
    setHtml(
      listEl,
      `
      <div class="pdv-selection-option pdv-selection-selected">
        <div>
          <strong>${escapeHtml(usuario.nome || "Usuário")}${tipo}</strong>
          ${email}
        </div>
        <span class="pdv-badge">${escapeHtml(extraLabel || "Selecionado")}</span>
      </div>
      `
    );
  }

  function renderSelectionList(listEl, usuarios, onSelect, emptyMessage) {
    if (!listEl) return;

    if (!usuarios || !usuarios.length) {
      setHtml(listEl, `<div class="pdv-empty-state">${escapeHtml(emptyMessage)}</div>`);
      return;
    }

    setHtml(
      listEl,
      usuarios
        .map((usuario) => {
          const tipo = usuario.tipo ? ` (${escapeHtml(usuario.tipo)})` : "";
          const email = usuario.email ? `<div class="pdv-selection-meta">${escapeHtml(usuario.email)}</div>` : "";
          return `
            <div class="pdv-selection-option">
              <div>
                <strong>${escapeHtml(usuario.nome || "Usuário")}${tipo}</strong>
                ${email}
              </div>
              <button type="button" class="pdv-btn btn-select-user" data-user-id="${usuario.id}">
                Selecionar
              </button>
            </div>
          `;
        })
        .join("")
    );

    listEl.querySelectorAll(".btn-select-user").forEach((button) => {
      button.addEventListener("click", () => {
        const userId = toNumber(button.dataset.userId, 0);
        const usuario = usuarios.find((item) => Number(item.id) === Number(userId));
        if (usuario) onSelect(usuario);
      });
    });
  }

  async function carregarOperadores(termo = "", limite = 20) {
    const empresaId = getEmpresaId();
    const q = String(termo || "").trim();
    if (!q) return [];

    const data = await request(
      `/api/caixa/operadores?empresa_id=${empresaId}&q=${encodeURIComponent(q)}&limite=${limite}`
    );

    state.operadores = Array.isArray(data) ? data : [];
    return state.operadores;
  }

  async function pesquisarUsuarios({
    termo,
    apenasGerente = false,
  }) {
    let usuarios = await carregarOperadores(termo, 20);

    if (apenasGerente) {
      usuarios = usuarios.filter((item) => {
        const tipo = normalizeTipoUsuario(item.tipo);
        return tipo === "gerente" || tipo === "admin";
      });
    }

    return usuarios;
  }

  function getModalElements(modalId) {
    const map = {
      "modal-abrir-caixa": {
        modal: els.modalAbrirCaixa,
        operadorBusca: els.caixaAberturaOperadorBusca,
        operadorLista: els.caixaAberturaOperadorLista,
        operadorId: els.caixaAberturaOperadorId,
        operadorNome: els.caixaAberturaOperadorNome,
      },
      "modal-sangria": {
        modal: els.modalSangria,
        operadorBusca: els.caixaSangriaOperadorBusca,
        operadorLista: els.caixaSangriaOperadorLista,
        operadorId: els.caixaSangriaOperadorId,
        operadorNome: els.caixaSangriaOperadorNome,
      },
      "modal-suprimento": {
        modal: els.modalSuprimento,
        operadorBusca: els.caixaSuprimentoOperadorBusca,
        operadorLista: els.caixaSuprimentoOperadorLista,
        operadorId: els.caixaSuprimentoOperadorId,
        operadorNome: els.caixaSuprimentoOperadorNome,
      },
      "modal-fechar-caixa": {
        modal: els.modalFecharCaixa,
        operadorBusca: els.caixaFechamentoOperadorBusca,
        operadorLista: els.caixaFechamentoOperadorLista,
        operadorId: els.caixaFechamentoOperadorId,
        operadorNome: els.caixaFechamentoOperadorNome,
      },
    };

    return map[modalId] || null;
  }

  function closeAllModals() {
    [
      els.modalAbrirCaixa,
      els.modalSangria,
      els.modalSuprimento,
      els.modalFecharCaixa,
    ].forEach(hideEl);

    hideEl(els.modalOverlay);
  }

  function openModal(modalId) {
    closeAllModals();
    const config = getModalElements(modalId);
    if (!config?.modal) return;
    showEl(els.modalOverlay);
    showEl(config.modal);
  }

  function resetModalAbrirCaixa() {
    setValue(els.caixaAberturaOperadorBusca, "");
    clearSelection(
      els.caixaAberturaOperadorLista,
      els.caixaAberturaOperadorId,
      els.caixaAberturaOperadorNome,
      "Nenhum operador selecionado."
    );
    setValue(els.caixaValorAbertura, "");
    setValue(els.caixaObservacoesAbertura, "");
    setValue(els.caixaMotivoDiferencaAbertura, "");
    setValue(els.caixaGerenteAberturaBusca, "");
    setValue(els.caixaSenhaGerenteAbertura, "");
    clearSelection(
      els.caixaGerenteAberturaLista,
      els.caixaGerenteAberturaId,
      els.caixaGerenteAberturaNome,
      "Nenhum gerente selecionado."
    );
    hideEl(els.caixaAberturaDivergenciaBox);
  }

  function resetModalSangria() {
    setValue(els.caixaSangriaOperadorBusca, "");
    clearSelection(
      els.caixaSangriaOperadorLista,
      els.caixaSangriaOperadorId,
      els.caixaSangriaOperadorNome,
      "Nenhum operador selecionado."
    );
    setValue(els.caixaSangriaValor, "");
    setValue(els.caixaSangriaMotivo, "");
    setValue(els.caixaSangriaObservacoes, "");
    setValue(els.caixaGerenteSangriaBusca, "");
    setValue(els.caixaSenhaGerenteSangria, "");
    clearSelection(
      els.caixaGerenteSangriaLista,
      els.caixaGerenteSangriaId,
      els.caixaGerenteSangriaNome,
      "Nenhum gerente selecionado."
    );
    hideEl(els.caixaSangriaGerenteBox);
  }

  function resetModalSuprimento() {
    setValue(els.caixaSuprimentoOperadorBusca, "");
    clearSelection(
      els.caixaSuprimentoOperadorLista,
      els.caixaSuprimentoOperadorId,
      els.caixaSuprimentoOperadorNome,
      "Nenhum operador selecionado."
    );
    setValue(els.caixaSuprimentoValor, "");
    setValue(els.caixaSuprimentoMotivo, "");
    setValue(els.caixaSuprimentoObservacoes, "");
    setValue(els.caixaGerenteSuprimentoBusca, "");
    setValue(els.caixaSenhaGerenteSuprimento, "");
    clearSelection(
      els.caixaGerenteSuprimentoLista,
      els.caixaGerenteSuprimentoId,
      els.caixaGerenteSuprimentoNome,
      "Nenhum gerente selecionado."
    );
    hideEl(els.caixaSuprimentoGerenteBox);
  }

  function resetModalFecharCaixa() {
    setValue(els.caixaFechamentoOperadorBusca, "");
    clearSelection(
      els.caixaFechamentoOperadorLista,
      els.caixaFechamentoOperadorId,
      els.caixaFechamentoOperadorNome,
      "Nenhum operador selecionado."
    );
    setValue(els.caixaFechamentoValor, "");
    setValue(els.caixaMotivoDiferencaFechamento, "");
    setValue(els.caixaGerenteFechamentoBusca, "");
    setValue(els.caixaSenhaGerenteFechamento, "");
    clearSelection(
      els.caixaGerenteFechamentoLista,
      els.caixaGerenteFechamentoId,
      els.caixaGerenteFechamentoNome,
      "Nenhum gerente selecionado."
    );
    setText(els.caixaFechamentoSaldoEsperado, formatMoney(0));
    hideEl(els.caixaFechamentoDivergenciaBox);
  }

  async function handleSearchUsers({
    inputEl,
    listEl,
    idEl,
    nameEl,
    onlyManager = false,
    selectedLabel = "Selecionado",
    emptyMessage = "Nenhum usuário encontrado.",
  }) {
    const termo = String(inputEl?.value || "").trim();
    if (!termo) {
      throw new Error("Digite um nome para pesquisar.");
    }

    const usuarios = await pesquisarUsuarios({
      termo,
      apenasGerente: onlyManager,
    });

    renderSelectionList(
      listEl,
      usuarios,
      (usuario) => setSelectedUser(listEl, idEl, nameEl, usuario, selectedLabel),
      emptyMessage
    );
  }

  async function carregarCaixaAtual() {
    const empresaId = getEmpresaId();
    const data = await request(`/api/caixa/atual?empresa_id=${empresaId}`);
    state.caixaAtual = data || null;

    if (state.caixaAtual?.id) {
      await carregarResumoCaixa(state.caixaAtual.id);
    } else {
      state.caixaResumo = null;
    }

    renderCaixa();
  }

  async function carregarResumoCaixa(caixaSessaoId) {
    if (!caixaSessaoId) {
      state.caixaResumo = null;
      return null;
    }

    const resumo = await request(`/api/caixa/sessoes/${caixaSessaoId}/resumo`);
    state.caixaResumo = resumo;
    return resumo;
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
      setHtml(
        els.carrinhoLista,
        `<div class="pdv-empty-state">Nenhum item adicionado.</div>`
      );
      return;
    }

    setHtml(
      els.carrinhoLista,
      itens
        .map((item) => {
          const badgeClass =
            item.tipo_item === "SERVICE" ? "pdv-badge-blue" : "pdv-badge-green";
          const badgeText = item.tipo_item === "SERVICE" ? "Atendimento" : "Produto";

          return `
            <div class="pdv-item-card">
              <div class="pdv-item-card__header">
                <strong>${escapeHtml(item.descricao_snapshot || "Item sem descrição")}</strong>
                <span class="${badgeClass}">${badgeText}</span>
              </div>
              <div class="pdv-item-card__meta">
                Qtde: ${toNumber(item.quantidade, 0)} |
                Unitário: ${formatMoney(item.valor_unitario)} |
                Desconto: ${formatMoney(item.desconto_valor)}
              </div>
              ${
                item.observacao
                  ? `<div class="pdv-item-card__obs">${escapeHtml(item.observacao)}</div>`
                  : ""
              }
              <div class="pdv-item-card__footer">
                <strong>${formatMoney(item.valor_total)}</strong>
                ${
                  hasVendaAberta()
                    ? `<button type="button" class="btn-remover-item" data-item-id="${item.id}">Remover</button>`
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
          const venda = await request(
            `/api/pdv/vendas/${state.vendaAtual.id}/itens/${itemId}`,
            { method: "DELETE" }
          );
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
    setHtml(
      els.produtosResultado,
      `<div class="pdv-empty-state">${escapeHtml(message)}</div>`
    );
  }

  function renderSugestaoProduto(termo) {
    if (!els.produtosResultado) return;

    const termoSeguro = escapeHtml(termo || "");
    setHtml(
      els.produtosResultado,
      `
      <div class="pdv-product-suggestion">
        <strong>${termoSeguro || "Produto avulso"}</strong>
        <div>Sem catálogo integrado neste passo. Use este item para adicionar produto avulso à venda atual.</div>
        <button type="button" id="btn-adicionar-produto-avulso">Adicionar à venda</button>
      </div>
      `
    );

    document
      .getElementById("btn-adicionar-produto-avulso")
      ?.addEventListener("click", async () => {
        try {
          await adicionarProdutoAvulso(termo);
        } catch (error) {
          showAlert(error.message, "danger");
        }
      });
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
            <div class="pdv-client-card">
              <strong>${escapeHtml(cliente.nome)}</strong>
              <div>${meta.join(" | ") || "Cliente sem dados complementares"}</div>
              <button type="button" class="btn-iniciar-venda-cliente" data-cliente-id="${cliente.id}">
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

        try {
          await iniciarVendaCliente(clienteId);
        } catch (error) {
          showAlert(error.message, "danger");
        }
      });
    });
  }

  function renderProducao() {
    if (!els.producaoLista) return;

    if (!state.producaoPronta.length) {
      setHtml(
        els.producaoLista,
        `<div class="pdv-empty-state">Nenhum item pronto para cobrança.</div>`
      );
      return;
    }

    setHtml(
      els.producaoLista,
      state.producaoPronta
        .map((item) => {
          return `
            <div class="pdv-producao-card">
              <strong>${escapeHtml(item.descricao)}</strong>
              <div>
                Cliente: ${escapeHtml(item.cliente_nome || "-")}
                ${item.pet_nome ? ` | Pet: ${escapeHtml(item.pet_nome)}` : ""}
              </div>
              <div>${formatMoney(item.valor_total)}</div>
              <button type="button" class="btn-puxar-producao" data-item-id="${item.id}">
                Puxar para venda
              </button>
            </div>
          `;
        })
        .join("")
    );

    document.querySelectorAll(".btn-puxar-producao").forEach((button) => {
      button.addEventListener("click", async () => {
        const itemId = toNumber(button.dataset.itemId, 0);
        if (!itemId) return;

        try {
          await puxarItemProducao(itemId);
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

  function collectAberturaPayload() {
    const empresaId = getEmpresaId();
    const operadorId = toNumber(els.caixaAberturaOperadorId?.value, 0);
    const operadorNome = String(els.caixaAberturaOperadorNome?.value || "").trim();
    const valorAbertura = requireNonNegativeNumber(
      els.caixaValorAbertura?.value,
      "Informe um valor inicial válido."
    );
    const observacoes = String(els.caixaObservacoesAbertura?.value || "").trim();

    if (!operadorId || !operadorNome) {
      throw new Error("Selecione o operador de abertura.");
    }

    const payload = {
      empresa_id: empresaId,
      usuario_responsavel_id: operadorId,
      usuario_responsavel_nome: operadorNome,
      usuario_abertura_id: operadorId,
      usuario_abertura_nome: operadorNome,
      valor_abertura_informado: valorAbertura,
      observacoes: observacoes || null,
    };

    if (!els.caixaAberturaDivergenciaBox?.classList.contains("pdv-hidden")) {
      const motivo = requireText(
        els.caixaMotivoDiferencaAbertura?.value,
        "Informe o motivo da divergência de abertura."
      );
      const gerenteId = toNumber(els.caixaGerenteAberturaId?.value, 0);
      const gerenteNome = String(els.caixaGerenteAberturaNome?.value || "").trim();
      const senhaGerente = requireText(
        els.caixaSenhaGerenteAbertura?.value,
        "Informe a senha do gerente."
      );

      if (!gerenteId || !gerenteNome) {
        throw new Error("Selecione o gerente autorizador da abertura.");
      }

      payload.motivo_diferenca_abertura = motivo;
      payload.gerente_abertura_id = gerenteId;
      payload.gerente_abertura_nome = gerenteNome;
      payload.senha_gerente = senhaGerente;
    }

    return payload;
  }

  function collectSangriaPayload() {
    const empresaId = getEmpresaId();
    const caixaSessaoId = getCaixaSessaoId();
    const operadorId = toNumber(els.caixaSangriaOperadorId?.value, 0);
    const operadorNome = String(els.caixaSangriaOperadorNome?.value || "").trim();
    const valor = requirePositiveNumber(
      els.caixaSangriaValor?.value,
      "Informe um valor de sangria maior que zero."
    );
    const motivo = requireText(els.caixaSangriaMotivo?.value, "Informe o motivo da sangria.");
    const observacoes = String(els.caixaSangriaObservacoes?.value || "").trim();

    if (!caixaSessaoId) {
      throw new Error("Nenhuma sessão de caixa aberta.");
    }

    if (!operadorId || !operadorNome) {
      throw new Error("Selecione o operador da sangria.");
    }

    const payload = {
      empresa_id: empresaId,
      caixa_sessao_id: caixaSessaoId,
      valor,
      usuario_id: operadorId,
      usuario_nome: operadorNome,
      motivo,
      observacoes: observacoes || null,
    };

    if (!els.caixaSangriaGerenteBox?.classList.contains("pdv-hidden")) {
      const gerenteId = toNumber(els.caixaGerenteSangriaId?.value, 0);
      const gerenteNome = String(els.caixaGerenteSangriaNome?.value || "").trim();
      const senhaGerente = requireText(
        els.caixaSenhaGerenteSangria?.value,
        "Informe a senha do gerente."
      );

      if (!gerenteId || !gerenteNome) {
        throw new Error("Selecione o gerente autorizador da sangria.");
      }

      payload.gerente_autorizador_id = gerenteId;
      payload.gerente_autorizador_nome = gerenteNome;
      payload.senha_gerente = senhaGerente;
    }

    return payload;
  }

  function collectSuprimentoPayload() {
    const empresaId = getEmpresaId();
    const caixaSessaoId = getCaixaSessaoId();
    const operadorId = toNumber(els.caixaSuprimentoOperadorId?.value, 0);
    const operadorNome = String(els.caixaSuprimentoOperadorNome?.value || "").trim();
    const valor = requirePositiveNumber(
      els.caixaSuprimentoValor?.value,
      "Informe um valor de suprimento maior que zero."
    );
    const motivo = requireText(
      els.caixaSuprimentoMotivo?.value,
      "Informe o motivo do suprimento."
    );
    const observacoes = String(els.caixaSuprimentoObservacoes?.value || "").trim();

    if (!caixaSessaoId) {
      throw new Error("Nenhuma sessão de caixa aberta.");
    }

    if (!operadorId || !operadorNome) {
      throw new Error("Selecione o operador do suprimento.");
    }

    const payload = {
      empresa_id: empresaId,
      caixa_sessao_id: caixaSessaoId,
      valor,
      usuario_id: operadorId,
      usuario_nome: operadorNome,
      motivo,
      observacoes: observacoes || null,
    };

    if (!els.caixaSuprimentoGerenteBox?.classList.contains("pdv-hidden")) {
      const gerenteId = toNumber(els.caixaGerenteSuprimentoId?.value, 0);
      const gerenteNome = String(els.caixaGerenteSuprimentoNome?.value || "").trim();
      const senhaGerente = requireText(
        els.caixaSenhaGerenteSuprimento?.value,
        "Informe a senha do gerente."
      );

      if (!gerenteId || !gerenteNome) {
        throw new Error("Selecione o gerente autorizador do suprimento.");
      }

      payload.gerente_autorizador_id = gerenteId;
      payload.gerente_autorizador_nome = gerenteNome;
      payload.senha_gerente = senhaGerente;
    }

    return payload;
  }

  function collectFechamentoPayload() {
    const operadorId = toNumber(els.caixaFechamentoOperadorId?.value, 0);
    const operadorNome = String(els.caixaFechamentoOperadorNome?.value || "").trim();
    const valorFechamento = requireNonNegativeNumber(
      els.caixaFechamentoValor?.value,
      "Informe a contagem final em dinheiro."
    );

    if (!operadorId || !operadorNome) {
      throw new Error("Selecione o operador do fechamento.");
    }

    const payload = {
      usuario_fechamento_id: operadorId,
      usuario_fechamento_nome: operadorNome,
      valor_fechamento_informado: valorFechamento,
    };

    if (!els.caixaFechamentoDivergenciaBox?.classList.contains("pdv-hidden")) {
      const motivo = requireText(
        els.caixaMotivoDiferencaFechamento?.value,
        "Informe o motivo da divergência de fechamento."
      );
      const gerenteId = toNumber(els.caixaGerenteFechamentoId?.value, 0);
      const gerenteNome = String(els.caixaGerenteFechamentoNome?.value || "").trim();
      const senhaGerente = requireText(
        els.caixaSenhaGerenteFechamento?.value,
        "Informe a senha do gerente."
      );

      if (!gerenteId || !gerenteNome) {
        throw new Error("Selecione o gerente autorizador do fechamento.");
      }

      payload.motivo_diferenca_fechamento = motivo;
      payload.gerente_fechamento_id = gerenteId;
      payload.gerente_fechamento_nome = gerenteNome;
      payload.senha_gerente = senhaGerente;
    }

    return payload;
  }

  async function submitAberturaCaixa() {
    const payload = collectAberturaPayload();

    try {
      const response = await request("/api/caixa/abrir", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      state.caixaAtual = response.caixa_sessao || null;
      if (state.caixaAtual?.id) {
        await carregarResumoCaixa(state.caixaAtual.id);
      }

      renderCaixa();
      closeAllModals();
      resetModalAbrirCaixa();
      showAlert(response.mensagem || "Caixa aberto com sucesso.", "success");
    } catch (error) {
      const msg = String(error.message || "");

      if (
        msg.includes("Motivo da diferença na abertura é obrigatório") ||
        msg.includes("Senha do gerente é obrigatória") ||
        msg.includes("Gerente autorizador")
      ) {
        showEl(els.caixaAberturaDivergenciaBox);
        showAlert("A abertura exige motivo e autorização gerencial.", "warning");
        return;
      }

      throw error;
    }
  }

  async function submitSangria() {
    const payload = collectSangriaPayload();

    try {
      const response = await request("/api/caixa/sangria", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      state.caixaAtual = response.caixa_sessao || state.caixaAtual;
      if (state.caixaAtual?.id) {
        await carregarResumoCaixa(state.caixaAtual.id);
      }

      renderCaixa();
      closeAllModals();
      resetModalSangria();
      showAlert(response.mensagem || "Sangria registrada com sucesso.", "success");
    } catch (error) {
      const msg = String(error.message || "");

      if (
        msg.includes("Senha do gerente é obrigatória") ||
        msg.includes("Gerente autorizador") ||
        msg.includes("perfil gerencial")
      ) {
        showEl(els.caixaSangriaGerenteBox);
        showAlert("A sangria exige autorização gerencial.", "warning");
        return;
      }

      throw error;
    }
  }

  async function submitSuprimento() {
    const payload = collectSuprimentoPayload();

    try {
      const response = await request("/api/caixa/suprimento", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      state.caixaAtual = response.caixa_sessao || state.caixaAtual;
      if (state.caixaAtual?.id) {
        await carregarResumoCaixa(state.caixaAtual.id);
      }

      renderCaixa();
      closeAllModals();
      resetModalSuprimento();
      showAlert(response.mensagem || "Suprimento registrado com sucesso.", "success");
    } catch (error) {
      const msg = String(error.message || "");

      if (
        msg.includes("Senha do gerente é obrigatória") ||
        msg.includes("Gerente autorizador") ||
        msg.includes("perfil gerencial")
      ) {
        showEl(els.caixaSuprimentoGerenteBox);
        showAlert("O suprimento exige autorização gerencial.", "warning");
        return;
      }

      throw error;
    }
  }

  async function submitFechamentoCaixa() {
    const caixaSessaoId = getCaixaSessaoId();
    if (!caixaSessaoId) {
      throw new Error("Nenhuma sessão de caixa aberta.");
    }

    const payload = collectFechamentoPayload();

    try {
      const response = await request(`/api/caixa/sessoes/${caixaSessaoId}/fechar`, {
        method: "POST",
        body: JSON.stringify(payload),
      });

      state.caixaAtual = response.caixa_sessao || null;
      state.caixaResumo = null;
      renderCaixa();
      closeAllModals();
      resetModalFecharCaixa();
      showAlert(response.mensagem || "Caixa fechado com sucesso.", "success");
    } catch (error) {
      const msg = String(error.message || "");

      if (
        msg.includes("Motivo da diferença no fechamento é obrigatório") ||
        msg.includes("Senha do gerente é obrigatória") ||
        msg.includes("Gerente autorizador")
      ) {
        showEl(els.caixaFechamentoDivergenciaBox);
        showAlert("O fechamento exige motivo e autorização gerencial.", "warning");
        return;
      }

      throw error;
    }
  }

  async function abrirCaixaModal() {
    if (hasCaixaAberto()) {
      throw new Error("Já existe um caixa aberto.");
    }

    resetModalAbrirCaixa();
    openModal("modal-abrir-caixa");
  }

  async function abrirSangriaModal() {
    if (!hasCaixaAberto()) {
      throw new Error("Abra o caixa antes de registrar sangria.");
    }

    resetModalSangria();
    openModal("modal-sangria");
  }

  async function abrirSuprimentoModal() {
    if (!hasCaixaAberto()) {
      throw new Error("Abra o caixa antes de registrar suprimento.");
    }

    resetModalSuprimento();
    openModal("modal-suprimento");
  }

  async function abrirFechamentoModal() {
    if (!hasCaixaAberto()) {
      throw new Error("Não existe caixa aberto para fechamento.");
    }

    resetModalFecharCaixa();

    const caixaSessaoId = getCaixaSessaoId();
    if (caixaSessaoId) {
      await carregarResumoCaixa(caixaSessaoId);
      renderCaixa();
    }

    setText(
      els.caixaFechamentoSaldoEsperado,
      formatMoney(state.caixaResumo?.saldo_dinheiro_esperado || 0)
    );

    openModal("modal-fechar-caixa");
  }

  async function iniciarVendaBalcao() {
    if (!hasCaixaAberto()) {
      throw new Error("Abra o caixa antes de iniciar uma venda balcão.");
    }

    const empresaId = getEmpresaId();
    const caixaSessaoId = getCaixaSessaoId();

    const payload = {
      empresa_id: empresaId,
      caixa_sessao_id: caixaSessaoId,
    };

    const venda = await request("/api/pdv/vendas/balcao", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    state.vendaAtual = venda;
    renderVenda();
    showAlert("Venda balcão iniciada.", "success");
  }

  async function iniciarVendaCliente(clienteId) {
    if (!hasCaixaAberto()) {
      throw new Error("Abra o caixa antes de iniciar uma venda.");
    }

    const empresaId = getEmpresaId();
    const caixaSessaoId = getCaixaSessaoId();

    const payload = {
      empresa_id: empresaId,
      cliente_id: clienteId,
      caixa_sessao_id: caixaSessaoId,
    };

    const venda = await request("/api/pdv/vendas/cliente", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    state.vendaAtual = venda;
    renderVenda();
    showAlert("Venda do cliente iniciada.", "success");
  }

  async function adicionarProdutoAvulso(termo) {
    if (!hasVendaAberta()) {
      throw new Error("Abra uma venda antes de adicionar produto.");
    }

    const descricao = window.prompt("Descrição do produto avulso:", termo || "");
    if (descricao === null || !String(descricao).trim()) {
      throw new Error("Descrição do produto é obrigatória.");
    }

    const quantidadeRaw = window.prompt("Quantidade:", "1");
    if (quantidadeRaw === null) {
      throw new Error("Quantidade inválida.");
    }
    const quantidade = requirePositiveNumber(quantidadeRaw, "Quantidade inválida.");

    const valorUnitarioRaw = window.prompt("Valor unitário:", "0,00");
    if (valorUnitarioRaw === null) {
      throw new Error("Valor unitário inválido.");
    }
    const valorUnitario = requireNonNegativeNumber(valorUnitarioRaw, "Valor unitário inválido.");

    const observacao = window.prompt("Observação do item (opcional):", "") || "";

    const payload = {
      tipo_item: "PRODUCT",
      descricao_snapshot: String(descricao).trim(),
      quantidade: Number(quantidade),
      valor_unitario: Number(valorUnitario.toFixed(2)),
      observacao: observacao || null,
    };

    const venda = await request(`/api/pdv/vendas/${state.vendaAtual.id}/itens/produto-avulso`, {
      method: "POST",
      body: JSON.stringify(payload),
    });

    state.vendaAtual = venda;
    renderVenda();
    showAlert("Produto avulso adicionado à venda.", "success");
  }

  async function buscarProdutoOuCliente() {
    const termo = String(els.buscaProduto?.value || "").trim();

    if (!termo) {
      renderBuscaResultadosVazio("Digite algo para buscar.");
      return;
    }

    if (!hasVendaAtual()) {
      try {
        const clientes = await request(
          `/api/pdv/clientes/busca?q=${encodeURIComponent(termo)}&empresa_id=${getEmpresaId()}`
        );
        state.clientesEncontrados = Array.isArray(clientes) ? clientes : [];
        renderClientesEncontrados();
        return;
      } catch (_error) {
        renderSugestaoProduto(termo);
        return;
      }
    }

    renderSugestaoProduto(termo);
  }

  async function carregarProducaoPronta() {
    try {
      const empresaId = getEmpresaId();
      const itens = await request(`/api/pdv/producao/prontos?empresa_id=${empresaId}`);
      state.producaoPronta = Array.isArray(itens) ? itens : [];
      renderProducao();
    } catch (error) {
      console.warn("Falha ao carregar produção pronta:", error);
      state.producaoPronta = [];
      renderProducao();
    }
  }

  async function puxarItemProducao(itemId) {
    if (!hasCaixaAberto()) {
      throw new Error("Abra o caixa antes de puxar item da produção.");
    }

    const empresaId = getEmpresaId();
    const caixaSessaoId = getCaixaSessaoId();

    const payload = {
      empresa_id: empresaId,
      caixa_sessao_id: caixaSessaoId,
      item_producao_id: itemId,
    };

    const venda = await request("/api/pdv/vendas/producao", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    state.vendaAtual = venda;
    renderVenda();
    showAlert("Item da produção puxado para venda.", "success");
  }

  async function finalizarVenda() {
    if (!hasVendaAberta()) {
      throw new Error("Não existe venda aberta para finalizar.");
    }

    if (!hasCaixaAberto()) {
      throw new Error("Abra o caixa antes de finalizar a venda.");
    }

    const formaPagamento = String(els.formaPagamento?.value || "DINHEIRO").trim();
    const valorPago = toNumber(els.valorPagamento?.value || 0, 0);

    const payload = {
      forma_pagamento: formaPagamento,
      valor_pago: Number(valorPago.toFixed(2)),
      caixa_sessao_id: getCaixaSessaoId(),
    };

    const venda = await request(`/api/pdv/vendas/${state.vendaAtual.id}/checkout`, {
      method: "POST",
      body: JSON.stringify(payload),
    });

    state.vendaAtual = venda;
    renderVenda();

    if (state.caixaAtual?.id) {
      await carregarResumoCaixa(state.caixaAtual.id);
      renderCaixa();
    }

    showAlert("Venda finalizada com sucesso.", "success");
  }

  async function cancelarVendaAtual() {
    if (!state.vendaAtual?.id) {
      throw new Error("Nenhuma venda disponível para cancelamento.");
    }

    const confirmar = window.confirm("Deseja cancelar a venda atual?");
    if (!confirmar) return;

    const motivo = window.prompt("Informe o motivo do cancelamento:", "");
    if (motivo === null || !String(motivo).trim()) {
      throw new Error("Motivo do cancelamento é obrigatório.");
    }

    const payload = { motivo: String(motivo).trim() };

    try {
      const venda = await request(`/api/pdv/vendas/${state.vendaAtual.id}/cancelar`, {
        method: "POST",
        body: JSON.stringify(payload),
      });

      state.vendaAtual = venda;
      renderVenda();
      showAlert("Venda cancelada com sucesso.", "warning");
    } catch (error) {
      const msg = String(error.message || "");

      if (
        msg.includes("gerente") ||
        msg.includes("Gerente") ||
        msg.includes("Senha do gerente")
      ) {
        const gerenteNome = window.prompt("Informe o nome do gerente:", "");
        if (gerenteNome === null || !String(gerenteNome).trim()) {
          throw new Error("Nome do gerente é obrigatório.");
        }

        const gerentes = await pesquisarUsuarios({
          termo: gerenteNome,
          apenasGerente: true,
        });

        if (!gerentes.length) {
          throw new Error("Nenhum gerente encontrado.");
        }

        const gerente = gerentes[0];
        const senhaGerente = window.prompt(`Informe a senha do gerente ${gerente.nome}:`, "");
        if (senhaGerente === null || !String(senhaGerente).trim()) {
          throw new Error("Senha do gerente é obrigatória.");
        }

        payload.gerente_id = gerente.id;
        payload.gerente_nome = gerente.nome;
        payload.senha_gerente = String(senhaGerente).trim();

        const venda = await request(`/api/pdv/vendas/${state.vendaAtual.id}/cancelar`, {
          method: "POST",
          body: JSON.stringify(payload),
        });

        state.vendaAtual = venda;
        renderVenda();
        showAlert("Venda cancelada com autorização gerencial.", "warning");
        return;
      }

      throw error;
    }
  }

  function bindModalSearches() {
    els.btnBuscarOperadorAbertura?.addEventListener("click", async () => {
      try {
        await handleSearchUsers({
          inputEl: els.caixaAberturaOperadorBusca,
          listEl: els.caixaAberturaOperadorLista,
          idEl: els.caixaAberturaOperadorId,
          nameEl: els.caixaAberturaOperadorNome,
          onlyManager: false,
          selectedLabel: "Operador",
          emptyMessage: "Nenhum operador encontrado.",
        });
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnBuscarGerenteAbertura?.addEventListener("click", async () => {
      try {
        await handleSearchUsers({
          inputEl: els.caixaGerenteAberturaBusca,
          listEl: els.caixaGerenteAberturaLista,
          idEl: els.caixaGerenteAberturaId,
          nameEl: els.caixaGerenteAberturaNome,
          onlyManager: true,
          selectedLabel: "Gerente",
          emptyMessage: "Nenhum gerente encontrado.",
        });
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnBuscarOperadorSangria?.addEventListener("click", async () => {
      try {
        await handleSearchUsers({
          inputEl: els.caixaSangriaOperadorBusca,
          listEl: els.caixaSangriaOperadorLista,
          idEl: els.caixaSangriaOperadorId,
          nameEl: els.caixaSangriaOperadorNome,
          onlyManager: false,
          selectedLabel: "Operador",
          emptyMessage: "Nenhum operador encontrado.",
        });
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnBuscarGerenteSangria?.addEventListener("click", async () => {
      try {
        await handleSearchUsers({
          inputEl: els.caixaGerenteSangriaBusca,
          listEl: els.caixaGerenteSangriaLista,
          idEl: els.caixaGerenteSangriaId,
          nameEl: els.caixaGerenteSangriaNome,
          onlyManager: true,
          selectedLabel: "Gerente",
          emptyMessage: "Nenhum gerente encontrado.",
        });
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnBuscarOperadorSuprimento?.addEventListener("click", async () => {
      try {
        await handleSearchUsers({
          inputEl: els.caixaSuprimentoOperadorBusca,
          listEl: els.caixaSuprimentoOperadorLista,
          idEl: els.caixaSuprimentoOperadorId,
          nameEl: els.caixaSuprimentoOperadorNome,
          onlyManager: false,
          selectedLabel: "Operador",
          emptyMessage: "Nenhum operador encontrado.",
        });
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnBuscarGerenteSuprimento?.addEventListener("click", async () => {
      try {
        await handleSearchUsers({
          inputEl: els.caixaGerenteSuprimentoBusca,
          listEl: els.caixaGerenteSuprimentoLista,
          idEl: els.caixaGerenteSuprimentoId,
          nameEl: els.caixaGerenteSuprimentoNome,
          onlyManager: true,
          selectedLabel: "Gerente",
          emptyMessage: "Nenhum gerente encontrado.",
        });
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnBuscarOperadorFechamento?.addEventListener("click", async () => {
      try {
        await handleSearchUsers({
          inputEl: els.caixaFechamentoOperadorBusca,
          listEl: els.caixaFechamentoOperadorLista,
          idEl: els.caixaFechamentoOperadorId,
          nameEl: els.caixaFechamentoOperadorNome,
          onlyManager: false,
          selectedLabel: "Operador",
          emptyMessage: "Nenhum operador encontrado.",
        });
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnBuscarGerenteFechamento?.addEventListener("click", async () => {
      try {
        await handleSearchUsers({
          inputEl: els.caixaGerenteFechamentoBusca,
          listEl: els.caixaGerenteFechamentoLista,
          idEl: els.caixaGerenteFechamentoId,
          nameEl: els.caixaGerenteFechamentoNome,
          onlyManager: true,
          selectedLabel: "Gerente",
          emptyMessage: "Nenhum gerente encontrado.",
        });
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });
  }

  function bindModalSubmits() {
    els.btnConfirmarAbrirCaixa?.addEventListener("click", async () => {
      try {
        await submitAberturaCaixa();
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnConfirmarSangria?.addEventListener("click", async () => {
      try {
        await submitSangria();
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnConfirmarSuprimento?.addEventListener("click", async () => {
      try {
        await submitSuprimento();
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnConfirmarFecharCaixa?.addEventListener("click", async () => {
      try {
        await submitFechamentoCaixa();
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });
  }

  function bindModalClose() {
    document.querySelectorAll("[data-close-modal]").forEach((button) => {
      button.addEventListener("click", () => {
        closeAllModals();
      });
    });

    els.modalOverlay?.addEventListener("click", () => {
      closeAllModals();
    });
  }

  function bindEvents() {
    els.btnAbrirCaixa?.addEventListener("click", async () => {
      try {
        await abrirCaixaModal();
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnSangria?.addEventListener("click", async () => {
      try {
        await abrirSangriaModal();
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnSuprimento?.addEventListener("click", async () => {
      try {
        await abrirSuprimentoModal();
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnFecharCaixa?.addEventListener("click", async () => {
      try {
        await abrirFechamentoModal();
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnVendaBalcao?.addEventListener("click", async () => {
      try {
        await iniciarVendaBalcao();
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnCancelarVenda?.addEventListener("click", async () => {
      try {
        await cancelarVendaAtual();
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnBuscarProduto?.addEventListener("click", async () => {
      try {
        await buscarProdutoOuCliente();
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.buscaProduto?.addEventListener("keydown", async (event) => {
      if (event.key !== "Enter") return;
      event.preventDefault();

      try {
        await buscarProdutoOuCliente();
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnAtualizarProducao?.addEventListener("click", async () => {
      try {
        await carregarProducaoPronta();
        showAlert("Lista de produção atualizada.", "info");
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnFinalizarVenda?.addEventListener("click", async () => {
      try {
        await finalizarVenda();
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.empresaId?.addEventListener("change", async () => {
      try {
        state.vendaAtual = null;
        state.clientesEncontrados = [];
        state.producaoPronta = [];
        state.caixaResumo = null;
        state.caixaAtual = null;

        renderVenda();
        renderProducao();
        renderCaixa();

        closeAllModals();
        resetModalAbrirCaixa();
        resetModalSangria();
        resetModalSuprimento();
        resetModalFecharCaixa();

        await carregarCaixaAtual();
        await carregarProducaoPronta();
        showAlert("Empresa atualizada.", "info");
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    bindModalSearches();
    bindModalSubmits();
    bindModalClose();
  }

  async function init() {
    renderCaixa();
    renderVenda();
    renderProducao();
    resetModalAbrirCaixa();
    resetModalSangria();
    resetModalSuprimento();
    resetModalFecharCaixa();
    bindEvents();

    try {
      await carregarCaixaAtual();
    } catch (error) {
      console.warn("Falha ao carregar caixa atual:", error);
    }

    try {
      await carregarProducaoPronta();
    } catch (error) {
      console.warn("Falha ao carregar produção pronta:", error);
    }
  }

  document.addEventListener("DOMContentLoaded", init);
})();