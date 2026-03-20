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
    if (el) el.textContent = value ?? "";
  }

  function setHtml(el, value) {
    if (el) el.innerHTML = value ?? "";
  }

  function setValue(el, value) {
    if (el) el.value = value ?? "";
  }

  function showEl(el) {
    if (el) el.classList.remove("pdv-hidden");
  }

  function hideEl(el) {
    if (el) el.classList.add("pdv-hidden");
  }

  function toNumber(value, fallback = 0) {
  if (value === null || value === undefined || value === "") return fallback;

  let str = String(value).trim();

  if (!str) return fallback;

  // Remove espaços
  str = str.replace(/\s+/g, "");

  const hasComma = str.includes(",");
  const hasDot = str.includes(".");

  if (hasComma && hasDot) {
    // Se tiver vírgula e ponto, assume que o último separador é o decimal
    if (str.lastIndexOf(",") > str.lastIndexOf(".")) {
      // Ex.: 10.000,50 -> 10000.50
      str = str.replace(/\./g, "").replace(",", ".");
    } else {
      // Ex.: 10,000.50 -> 10000.50
      str = str.replace(/,/g, "");
    }
  } else if (hasComma) {
    // Ex.: 100,50 -> 100.50
    str = str.replace(",", ".");
  } else {
    // Se só tem ponto, mantém como decimal normal
    // Ex.: 100.50 -> 100.50
    // Não remove ponto aqui
  }

  const parsed = Number(str);
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

  function requireText(value, message) {
    const v = String(value ?? "").trim();
    if (!v) throw new Error(message);
    return v;
  }

  function requirePositiveNumber(value, message) {
    const n = toNumber(value, NaN);
    if (!Number.isFinite(n) || n <= 0) throw new Error(message);
    return Number(n.toFixed(2));
  }

  function requireNonNegativeNumber(value, message) {
    const n = toNumber(value, NaN);
    if (!Number.isFinite(n) || n < 0) throw new Error(message);
    return Number(n.toFixed(2));
  }

  function clearSelection(listEl, idEl, nameEl, emptyMessage) {
    setValue(idEl, "");
    setValue(nameEl, "");
    setHtml(listEl, `<div class="pdv-empty-state">${escapeHtml(emptyMessage)}</div>`);
  }

  function setSelectedUser(listEl, idEl, nameEl, usuario, extraLabel = "") {
    setValue(idEl, usuario.id);
    setValue(nameEl, usuario.nome || "");
    const tipo = usuario.tipo ? ` (${escapeHtml(usuario.tipo)})` : "";
    const email = usuario.email
      ? `<div class="pdv-selection-meta">${escapeHtml(usuario.email)}</div>`
      : "";
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
    if (!usuarios || !usuarios.length) {
      setHtml(listEl, `<div class="pdv-empty-state">${escapeHtml(emptyMessage)}</div>`);
      return;
    }

    setHtml(
      listEl,
      usuarios
        .map((usuario) => {
          const tipo = usuario.tipo ? ` (${escapeHtml(usuario.tipo)})` : "";
          const email = usuario.email
            ? `<div class="pdv-selection-meta">${escapeHtml(usuario.email)}</div>`
            : "";
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
      `/api/pdv/operadores?empresa_id=${empresaId}&q=${encodeURIComponent(q)}&limite=${limite}`
    );
    state.operadores = Array.isArray(data) ? data : [];
    return state.operadores;
  }

  async function pesquisarUsuarios({ termo, apenasGerente = false }) {
    let usuarios = await carregarOperadores(termo, 20);

    if (apenasGerente) {
      usuarios = usuarios.filter((item) => {
        const tipo = String(item.tipo || "").toLowerCase();
        return tipo === "gerente" || tipo === "admin";
      });
    }

    return usuarios;
  }

  function closeAllModals() {
    [els.modalAbrirCaixa, els.modalSangria, els.modalSuprimento, els.modalFecharCaixa].forEach(hideEl);
    hideEl(els.modalOverlay);
  }

  function openModal(modal) {
    closeAllModals();
    showEl(els.modalOverlay);
    showEl(modal);
  }

  function resetModalAbrirCaixa() {
    setValue(els.caixaAberturaOperadorBusca, "");
    clearSelection(els.caixaAberturaOperadorLista, els.caixaAberturaOperadorId, els.caixaAberturaOperadorNome, "Nenhum operador selecionado.");
    setValue(els.caixaValorAbertura, "");
    setValue(els.caixaObservacoesAbertura, "");
    setValue(els.caixaMotivoDiferencaAbertura, "");
    setValue(els.caixaGerenteAberturaBusca, "");
    setValue(els.caixaSenhaGerenteAbertura, "");
    clearSelection(els.caixaGerenteAberturaLista, els.caixaGerenteAberturaId, els.caixaGerenteAberturaNome, "Nenhum gerente selecionado.");
    hideEl(els.caixaAberturaDivergenciaBox);
  }

  function resetModalSangria() {
    setValue(els.caixaSangriaOperadorBusca, "");
    clearSelection(els.caixaSangriaOperadorLista, els.caixaSangriaOperadorId, els.caixaSangriaOperadorNome, "Nenhum operador selecionado.");
    setValue(els.caixaSangriaValor, "");
    setValue(els.caixaSangriaMotivo, "");
    setValue(els.caixaSangriaObservacoes, "");
    setValue(els.caixaGerenteSangriaBusca, "");
    setValue(els.caixaSenhaGerenteSangria, "");
    clearSelection(els.caixaGerenteSangriaLista, els.caixaGerenteSangriaId, els.caixaGerenteSangriaNome, "Nenhum gerente selecionado.");
    hideEl(els.caixaSangriaGerenteBox);
  }

  function resetModalSuprimento() {
    setValue(els.caixaSuprimentoOperadorBusca, "");
    clearSelection(els.caixaSuprimentoOperadorLista, els.caixaSuprimentoOperadorId, els.caixaSuprimentoOperadorNome, "Nenhum operador selecionado.");
    setValue(els.caixaSuprimentoValor, "");
    setValue(els.caixaSuprimentoMotivo, "");
    setValue(els.caixaSuprimentoObservacoes, "");
    setValue(els.caixaGerenteSuprimentoBusca, "");
    setValue(els.caixaSenhaGerenteSuprimento, "");
    clearSelection(els.caixaGerenteSuprimentoLista, els.caixaGerenteSuprimentoId, els.caixaGerenteSuprimentoNome, "Nenhum gerente selecionado.");
    hideEl(els.caixaSuprimentoGerenteBox);
  }

  function resetModalFecharCaixa() {
    setValue(els.caixaFechamentoOperadorBusca, "");
    clearSelection(els.caixaFechamentoOperadorLista, els.caixaFechamentoOperadorId, els.caixaFechamentoOperadorNome, "Nenhum operador selecionado.");
    setValue(els.caixaFechamentoValor, "");
    setValue(els.caixaMotivoDiferencaFechamento, "");
    setValue(els.caixaGerenteFechamentoBusca, "");
    setValue(els.caixaSenhaGerenteFechamento, "");
    clearSelection(els.caixaGerenteFechamentoLista, els.caixaGerenteFechamentoId, els.caixaGerenteFechamentoNome, "Nenhum gerente selecionado.");
    setText(els.caixaFechamentoSaldoEsperado, formatMoney(0));
    hideEl(els.caixaFechamentoDivergenciaBox);
  }

  async function handleSearchUsers({ inputEl, listEl, idEl, nameEl, onlyManager = false, selectedLabel = "Selecionado", emptyMessage = "Nenhum usuário encontrado." }) {
    const termo = String(inputEl?.value || "").trim();
    if (!termo) throw new Error("Digite um nome para pesquisar.");

    const usuarios = await pesquisarUsuarios({ termo, apenasGerente: onlyManager });

    renderSelectionList(listEl, usuarios, (usuario) => {
      setSelectedUser(listEl, idEl, nameEl, usuario, selectedLabel);
    }, emptyMessage);
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
    setText(els.vendaModo, venda.modo_cliente === "WALK_IN" ? "Balcão" : "Cliente cadastrado");
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
      setHtml(els.carrinhoLista, `<div class="pdv-empty-state">Nenhum item adicionado.</div>`);
      return;
    }

    setHtml(
      els.carrinhoLista,
      itens.map((item) => `
        <div class="pdv-item-card">
          <div class="pdv-item-card__header">
            <strong>${escapeHtml(item.descricao_snapshot || "Item sem descrição")}</strong>
            <span class="pdv-badge">${item.tipo_item === "SERVICE" ? "Atendimento" : "Produto"}</span>
          </div>
          <div class="pdv-item-card__meta">
            Qtde: ${toNumber(item.quantidade, 0)} |
            Unitário: ${formatMoney(item.valor_unitario)} |
            Desconto: ${formatMoney(item.desconto_valor)}
          </div>
          ${item.observacao ? `<div class="pdv-item-card__obs">${escapeHtml(item.observacao)}</div>` : ""}
          <div class="pdv-item-card__footer">
            <strong>${formatMoney(item.valor_total)}</strong>
          </div>
        </div>
      `).join("")
    );
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
    const valorAbertura = requireNonNegativeNumber(els.caixaValorAbertura?.value, "Informe um valor inicial válido.");
    const observacoes = String(els.caixaObservacoesAbertura?.value || "").trim();

    if (!operadorId || !operadorNome) throw new Error("Selecione o operador de abertura.");

    const payload = {
      empresa_id: empresaId,
      usuario_responsavel_id: operadorId,
      usuario_responsavel_nome: operadorNome,
      usuario_abertura_id: operadorId,
      usuario_abertura_nome: operadorNome,
      valor_abertura_informado: valorAbertura,
      observacoes: observacoes || null,
    };

    if (!els.caixaAberturaDivergenciaBox.classList.contains("pdv-hidden")) {
      const motivo = requireText(els.caixaMotivoDiferencaAbertura?.value, "Informe o motivo da divergência de abertura.");
      const gerenteId = toNumber(els.caixaGerenteAberturaId?.value, 0);
      const gerenteNome = String(els.caixaGerenteAberturaNome?.value || "").trim();
      const senhaGerente = requireText(els.caixaSenhaGerenteAbertura?.value, "Informe a senha do gerente.");

      if (!gerenteId || !gerenteNome) throw new Error("Selecione o gerente autorizador da abertura.");

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
    const valor = requirePositiveNumber(els.caixaSangriaValor?.value, "Informe um valor de sangria maior que zero.");
    const motivo = requireText(els.caixaSangriaMotivo?.value, "Informe o motivo da sangria.");
    const observacoes = String(els.caixaSangriaObservacoes?.value || "").trim();

    if (!caixaSessaoId) throw new Error("Nenhuma sessão de caixa aberta.");
    if (!operadorId || !operadorNome) throw new Error("Selecione o operador da sangria.");

    const payload = {
      empresa_id: empresaId,
      caixa_sessao_id: caixaSessaoId,
      valor,
      usuario_id: operadorId,
      usuario_nome: operadorNome,
      motivo,
      observacoes: observacoes || null,
    };

    if (!els.caixaSangriaGerenteBox.classList.contains("pdv-hidden")) {
      const gerenteId = toNumber(els.caixaGerenteSangriaId?.value, 0);
      const gerenteNome = String(els.caixaGerenteSangriaNome?.value || "").trim();
      const senhaGerente = requireText(els.caixaSenhaGerenteSangria?.value, "Informe a senha do gerente.");

      if (!gerenteId || !gerenteNome) throw new Error("Selecione o gerente autorizador da sangria.");

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
    const valor = requirePositiveNumber(els.caixaSuprimentoValor?.value, "Informe um valor de suprimento maior que zero.");
    const motivo = requireText(els.caixaSuprimentoMotivo?.value, "Informe o motivo do suprimento.");
    const observacoes = String(els.caixaSuprimentoObservacoes?.value || "").trim();

    if (!caixaSessaoId) throw new Error("Nenhuma sessão de caixa aberta.");
    if (!operadorId || !operadorNome) throw new Error("Selecione o operador do suprimento.");

    const payload = {
      empresa_id: empresaId,
      caixa_sessao_id: caixaSessaoId,
      valor,
      usuario_id: operadorId,
      usuario_nome: operadorNome,
      motivo,
      observacoes: observacoes || null,
    };

    if (!els.caixaSuprimentoGerenteBox.classList.contains("pdv-hidden")) {
      const gerenteId = toNumber(els.caixaGerenteSuprimentoId?.value, 0);
      const gerenteNome = String(els.caixaGerenteSuprimentoNome?.value || "").trim();
      const senhaGerente = requireText(els.caixaSenhaGerenteSuprimento?.value, "Informe a senha do gerente.");

      if (!gerenteId || !gerenteNome) throw new Error("Selecione o gerente autorizador do suprimento.");

      payload.gerente_autorizador_id = gerenteId;
      payload.gerente_autorizador_nome = gerenteNome;
      payload.senha_gerente = senhaGerente;
    }

    return payload;
  }

  function collectFechamentoPayload() {
    const operadorId = toNumber(els.caixaFechamentoOperadorId?.value, 0);
    const operadorNome = String(els.caixaFechamentoOperadorNome?.value || "").trim();
    const valorFechamento = requireNonNegativeNumber(els.caixaFechamentoValor?.value, "Informe a contagem final em dinheiro.");

    if (!operadorId || !operadorNome) throw new Error("Selecione o operador do fechamento.");

    const payload = {
      usuario_fechamento_id: operadorId,
      usuario_fechamento_nome: operadorNome,
      valor_fechamento_informado: valorFechamento,
    };

    if (!els.caixaFechamentoDivergenciaBox.classList.contains("pdv-hidden")) {
      const motivo = requireText(els.caixaMotivoDiferencaFechamento?.value, "Informe o motivo da divergência de fechamento.");
      const gerenteId = toNumber(els.caixaGerenteFechamentoId?.value, 0);
      const gerenteNome = String(els.caixaGerenteFechamentoNome?.value || "").trim();
      const senhaGerente = requireText(els.caixaSenhaGerenteFechamento?.value, "Informe a senha do gerente.");

      if (!gerenteId || !gerenteNome) throw new Error("Selecione o gerente autorizador do fechamento.");

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
      if (state.caixaAtual?.id) await carregarResumoCaixa(state.caixaAtual.id);

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
      if (state.caixaAtual?.id) await carregarResumoCaixa(state.caixaAtual.id);

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
      if (state.caixaAtual?.id) await carregarResumoCaixa(state.caixaAtual.id);

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
    if (!caixaSessaoId) throw new Error("Nenhuma sessão de caixa aberta.");

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

  async function openFecharCaixaModal() {
    if (!hasCaixaAberto()) throw new Error("Não existe caixa aberto para fechamento.");
    resetModalFecharCaixa();
    const caixaSessaoId = getCaixaSessaoId();
    if (caixaSessaoId) await carregarResumoCaixa(caixaSessaoId);
    setText(els.caixaFechamentoSaldoEsperado, formatMoney(state.caixaResumo?.saldo_dinheiro_esperado || 0));
    openModal(els.modalFecharCaixa);
  }

  function bindModalSearch(button, config) {
    button?.addEventListener("click", async () => {
      try {
        await handleSearchUsers(config);
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });
  }

  function bindEvents() {
    els.btnAbrirCaixa?.addEventListener("click", () => {
      try {
        resetModalAbrirCaixa();
        openModal(els.modalAbrirCaixa);
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnSangria?.addEventListener("click", () => {
      try {
        if (!hasCaixaAberto()) throw new Error("Abra o caixa antes de registrar sangria.");
        resetModalSangria();
        openModal(els.modalSangria);
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnSuprimento?.addEventListener("click", () => {
      try {
        if (!hasCaixaAberto()) throw new Error("Abra o caixa antes de registrar suprimento.");
        resetModalSuprimento();
        openModal(els.modalSuprimento);
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnFecharCaixa?.addEventListener("click", async () => {
      try {
        await openFecharCaixaModal();
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

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

    document.querySelectorAll("[data-close-modal]").forEach((button) => {
      button.addEventListener("click", closeAllModals);
    });

    els.modalOverlay?.addEventListener("click", closeAllModals);

    bindModalSearch(els.btnBuscarOperadorAbertura, {
      inputEl: els.caixaAberturaOperadorBusca,
      listEl: els.caixaAberturaOperadorLista,
      idEl: els.caixaAberturaOperadorId,
      nameEl: els.caixaAberturaOperadorNome,
      onlyManager: false,
      selectedLabel: "Operador",
      emptyMessage: "Nenhum operador encontrado.",
    });

    bindModalSearch(els.btnBuscarGerenteAbertura, {
      inputEl: els.caixaGerenteAberturaBusca,
      listEl: els.caixaGerenteAberturaLista,
      idEl: els.caixaGerenteAberturaId,
      nameEl: els.caixaGerenteAberturaNome,
      onlyManager: true,
      selectedLabel: "Gerente",
      emptyMessage: "Nenhum gerente encontrado.",
    });

    bindModalSearch(els.btnBuscarOperadorSangria, {
      inputEl: els.caixaSangriaOperadorBusca,
      listEl: els.caixaSangriaOperadorLista,
      idEl: els.caixaSangriaOperadorId,
      nameEl: els.caixaSangriaOperadorNome,
      onlyManager: false,
      selectedLabel: "Operador",
      emptyMessage: "Nenhum operador encontrado.",
    });

    bindModalSearch(els.btnBuscarGerenteSangria, {
      inputEl: els.caixaGerenteSangriaBusca,
      listEl: els.caixaGerenteSangriaLista,
      idEl: els.caixaGerenteSangriaId,
      nameEl: els.caixaGerenteSangriaNome,
      onlyManager: true,
      selectedLabel: "Gerente",
      emptyMessage: "Nenhum gerente encontrado.",
    });

    bindModalSearch(els.btnBuscarOperadorSuprimento, {
      inputEl: els.caixaSuprimentoOperadorBusca,
      listEl: els.caixaSuprimentoOperadorLista,
      idEl: els.caixaSuprimentoOperadorId,
      nameEl: els.caixaSuprimentoOperadorNome,
      onlyManager: false,
      selectedLabel: "Operador",
      emptyMessage: "Nenhum operador encontrado.",
    });

    bindModalSearch(els.btnBuscarGerenteSuprimento, {
      inputEl: els.caixaGerenteSuprimentoBusca,
      listEl: els.caixaGerenteSuprimentoLista,
      idEl: els.caixaGerenteSuprimentoId,
      nameEl: els.caixaGerenteSuprimentoNome,
      onlyManager: true,
      selectedLabel: "Gerente",
      emptyMessage: "Nenhum gerente encontrado.",
    });

    bindModalSearch(els.btnBuscarOperadorFechamento, {
      inputEl: els.caixaFechamentoOperadorBusca,
      listEl: els.caixaFechamentoOperadorLista,
      idEl: els.caixaFechamentoOperadorId,
      nameEl: els.caixaFechamentoOperadorNome,
      onlyManager: false,
      selectedLabel: "Operador",
      emptyMessage: "Nenhum operador encontrado.",
    });

    bindModalSearch(els.btnBuscarGerenteFechamento, {
      inputEl: els.caixaGerenteFechamentoBusca,
      listEl: els.caixaGerenteFechamentoLista,
      idEl: els.caixaGerenteFechamentoId,
      nameEl: els.caixaGerenteFechamentoNome,
      onlyManager: true,
      selectedLabel: "Gerente",
      emptyMessage: "Nenhum gerente encontrado.",
    });
  }

  async function init() {
    renderCaixa();
    renderVenda();
    bindEvents();

    try {
      await carregarCaixaAtual();
    } catch (error) {
      console.warn("Falha ao carregar caixa atual:", error);
    }
  }

  document.addEventListener("DOMContentLoaded", init);
})();