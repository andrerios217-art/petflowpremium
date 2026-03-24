(function () {
  const state = {
    empresaId: 1,
    caixaAtual: null,
    caixaResumo: null,
    vendaAtual: null,
    clientesEncontrados: [],
    producaoPronta: [],
    atendimentosProntos: [],
    operadores: [],
    produtosEncontrados: [],
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

    descontoPercent: document.getElementById("pdv-desconto-percent"),
    btnAplicarDesconto: document.getElementById("btn-aplicar-desconto"),
    btnZerarDesconto: document.getElementById("btn-zerar-desconto"),

    caixaCard: document.getElementById("pdv-caixa-card"),
    producaoSidebar: document.getElementById("pdv-producao-sidebar"),
    producaoCard: document.getElementById("pdv-producao-card"),

    floatingCard: document.getElementById("pdv-floating-card"),
    floatingBody: document.getElementById("pdv-floating-body"),
    btnFloatingMinimizar: document.getElementById("btn-floating-minimizar"),
    btnFloatingToggleCaixa: document.getElementById("btn-floating-toggle-caixa"),
    btnFloatingToggleProntos: document.getElementById("btn-floating-toggle-prontos"),
    btnFloatingAbrirCaixa: document.getElementById("btn-floating-abrir-caixa"),
    btnFloatingSangria: document.getElementById("btn-floating-sangria"),
    btnFloatingSuprimento: document.getElementById("btn-floating-suprimento"),
    btnFloatingFecharCaixa: document.getElementById("btn-floating-fechar-caixa"),
    btnFloatingAtualizarProntos: document.getElementById("btn-floating-atualizar-prontos"),

    producaoLista: document.getElementById("pdv-producao-lista"),
    btnAtualizarProducao: document.getElementById("btn-atualizar-producao"),

    atendimentosLista: document.getElementById("pdv-atendimentos-lista"),
    btnAtualizarAtendimentos: document.getElementById("btn-atualizar-atendimentos"),

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

    parcelasContainer: null,
    quantidadeParcelas: null,
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

    str = str.replace(/\s+/g, "");

    const hasComma = str.includes(",");
    const hasDot = str.includes(".");

    if (hasComma && hasDot) {
      if (str.lastIndexOf(",") > str.lastIndexOf(".")) {
        str = str.replace(/\./g, "").replace(",", ".");
      } else {
        str = str.replace(/,/g, "");
      }
    } else if (hasComma) {
      str = str.replace(",", ".");
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
    const email = usuario.email ? `<div class="pdv-muted">${escapeHtml(usuario.email)}</div>` : "";

    setHtml(
      listEl,
      `
      <div class="pdv-user-selected">
        <div><strong>${escapeHtml(usuario.nome || "Usuário")}${tipo}</strong></div>
        ${email}
        <div class="pdv-muted">${escapeHtml(extraLabel || "Selecionado")}</div>
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
          const email = usuario.email ? `<div class="pdv-muted">${escapeHtml(usuario.email)}</div>` : "";

          return `
          <div class="pdv-user-item">
            <div class="pdv-user-item-info">
              <div><strong>${escapeHtml(usuario.nome || "Usuário")}${tipo}</strong></div>
              ${email}
            </div>
            <button type="button" class="pdv-btn pdv-btn-primary" data-user-id="${usuario.id}">
              Selecionar
            </button>
          </div>
        `;
        })
        .join("")
    );

    listEl.querySelectorAll("[data-user-id]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const userId = toNumber(btn.getAttribute("data-user-id"), 0);
        const usuario = usuarios.find((u) => u.id === userId);
        if (usuario) onSelect(usuario);
      });
    });
  }

  function ensureParcelasControl() {
    if (!els.formaPagamento) return;

    let container = document.getElementById("pdv-parcelas-container");
    let select = document.getElementById("pdv-quantidade-parcelas");

    if (!container) {
      container = document.createElement("div");
      container.id = "pdv-parcelas-container";
      container.className = "pdv-hidden";
      container.style.marginTop = "12px";

      container.innerHTML = `
        <label for="pdv-quantidade-parcelas" style="display:block;margin-bottom:6px;font-weight:600;">
          Parcelas
        </label>
        <select id="pdv-quantidade-parcelas" class="form-select">
          ${Array.from({ length: 12 }, (_, index) => {
            const n = index + 1;
            return `<option value="${n}">${n}x</option>`;
          }).join("")}
        </select>
      `;
    }

    if (!container.parentElement) {
      const anchor =
        els.valorPagamento?.closest(".form-group") ||
        els.formaPagamento?.closest(".form-group") ||
        els.formaPagamento?.parentElement;

      if (anchor && anchor.parentElement) {
        anchor.insertAdjacentElement("afterend", container);
      } else if (els.formaPagamento.parentElement) {
        els.formaPagamento.parentElement.appendChild(container);
      }
    }

    select = container.querySelector("#pdv-quantidade-parcelas");

    els.parcelasContainer = container;
    els.quantidadeParcelas = select;

    if (els.quantidadeParcelas && !els.quantidadeParcelas.value) {
      els.quantidadeParcelas.value = "1";
    }
  }

  function getQuantidadeParcelasSelecionada() {
    const formaPagamento = String(els.formaPagamento?.value || "").trim();
    if (formaPagamento !== "CARTAO_CREDITO") return 1;

    const parcelas = toNumber(els.quantidadeParcelas?.value, 1);
    if (!Number.isFinite(parcelas) || parcelas < 1) return 1;
    if (parcelas > 12) return 12;
    return Math.trunc(parcelas);
  }

  function updateParcelasVisibility() {
    ensureParcelasControl();

    const formaPagamento = String(els.formaPagamento?.value || "").trim();
    const mostrar = formaPagamento === "CARTAO_CREDITO";

    if (mostrar) {
      showEl(els.parcelasContainer);
    } else {
      hideEl(els.parcelasContainer);
      if (els.quantidadeParcelas) {
        els.quantidadeParcelas.value = "1";
      }
    }
  }

  function renderProdutosResultado() {
    if (!els.produtosResultado) return;

    const produtos = state.produtosEncontrados || [];
    if (!produtos.length) {
      setHtml(els.produtosResultado, `<div class="pdv-empty-state">Nenhum produto encontrado.</div>`);
      return;
    }

    setHtml(
      els.produtosResultado,
      produtos
        .map((produto) => {
          const nome = escapeHtml(produto.nome || "Produto");
          const sku = produto.sku ? `<div class="pdv-muted">SKU: ${escapeHtml(produto.sku)}</div>` : "";
          const unidade = produto.unidade ? `<div class="pdv-muted">Unidade: ${escapeHtml(produto.unidade)}</div>` : "";
          const preco = formatMoney(produto.preco_venda_atual || 0);

          return `
          <div class="pdv-producao-item">
            <div class="pdv-producao-item__info">
              <strong>${nome}</strong>
              ${sku}
              ${unidade}
            </div>
            <div class="pdv-producao-item__actions">
              <strong>${preco}</strong>
              <button
                type="button"
                class="pdv-btn pdv-btn-primary"
                data-action="adicionar-produto"
                data-produto-id="${escapeHtml(produto.id)}"
              >
                Adicionar
              </button>
            </div>
          </div>
        `;
        })
        .join("")
    );
  }

  async function buscarProdutos(termo, limite = 20) {
    const empresaId = getEmpresaId();
    const q = String(termo || "").trim();

    if (!empresaId || empresaId <= 0) {
      throw new Error("empresa_id inválido para busca de produtos.");
    }

    if (!q) {
      state.produtosEncontrados = [];
      if (els.produtosResultado) {
        setHtml(els.produtosResultado, `<div class="pdv-empty-state">Digite algo para buscar produtos.</div>`);
      }
      return [];
    }

    if (els.produtosResultado) {
      setHtml(els.produtosResultado, `<div class="pdv-empty-state">Buscando produtos...</div>`);
    }

    const data = await request(
      `/api/pdv/produtos/busca?empresa_id=${empresaId}&q=${encodeURIComponent(q)}&limite=${limite}`
    );

    state.produtosEncontrados = Array.isArray(data) ? data : [];
    renderProdutosResultado();
    return state.produtosEncontrados;
  }

  async function handleBuscarProdutosAction(event) {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }

    const termo = String(els.buscaProduto?.value || "").trim();
    if (!termo) {
      state.produtosEncontrados = [];
      if (els.produtosResultado) {
        setHtml(els.produtosResultado, `<div class="pdv-empty-state">Digite algo para buscar produtos.</div>`);
      }
      showAlert("Digite o nome do produto para buscar.", "warning");
      return;
    }

    const btn = els.btnBuscarProduto;
    const textoOriginal = btn?.textContent || "Buscar";

    try {
      if (btn) {
        btn.disabled = true;
        btn.textContent = "Buscando...";
      }

      await buscarProdutos(termo);

      if (!(state.produtosEncontrados || []).length) {
        showAlert("Nenhum produto encontrado para a busca informada.", "warning");
      } else {
        showAlert(`Encontrado(s) ${state.produtosEncontrados.length} produto(s).`, "success");
      }
    } catch (error) {
      state.produtosEncontrados = [];
      if (els.produtosResultado) {
        setHtml(
          els.produtosResultado,
          `<div class="pdv-empty-state">Falha ao buscar produtos: ${escapeHtml(error.message || "erro inesperado")}</div>`
        );
      }
      throw error;
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = textoOriginal;
      }
    }
  }

  async function criarVendaBalcao() {
    if (!hasCaixaAberto()) throw new Error("Abra o caixa antes.");

    const empresaId = getEmpresaId();
    const caixaSessaoId = getCaixaSessaoId();
    if (!caixaSessaoId) throw new Error("Sessão de caixa inválida.");

    const venda = await request("/api/pdv/vendas", {
      method: "POST",
      body: JSON.stringify({
        empresa_id: empresaId,
        caixa_sessao_id: caixaSessaoId,
        modo_cliente: "WALK_IN",
      }),
    });

    state.vendaAtual = venda;
    renderVenda();
    renderControlsState();
    return venda;
  }

  async function adicionarProdutoNaVenda(produtoId) {
    if (!hasCaixaAberto()) throw new Error("Abra o caixa antes de adicionar produtos.");

    if (!hasVendaAberta()) {
      await criarVendaBalcao();
    }

    if (!hasVendaAberta()) throw new Error("Não foi possível abrir uma venda.");

    const produto = (state.produtosEncontrados || []).find((p) => Number(p.id) === Number(produtoId));
    if (!produto) throw new Error("Produto não encontrado no resultado da busca.");

    const payload = {
      tipo_item: "PRODUCT",
      produto_id: Number(produto.id),
      descricao_snapshot: produto.nome || "Produto",
      quantidade: 1,
      valor_unitario: Number(toNumber(produto.preco_venda_atual, 0).toFixed(2)),
      desconto_valor: 0,
    };

    const vendaAtualizada = await request(`/api/pdv/vendas/${state.vendaAtual.id}/itens`, {
      method: "POST",
      body: JSON.stringify(payload),
    });

    state.vendaAtual = vendaAtualizada;
    renderVenda();
    renderControlsState();
    showAlert("Produto adicionado na venda.", "success");
  }

  async function carregarOperadores(termo, limite = 50) {
    const empresaId = getEmpresaId();
    const q = String(termo || "").trim();
    if (!q) return [];
    const data = await request(
      `/api/pdv/operadores?empresa_id=${empresaId}&q=${encodeURIComponent(q)}&limite=${limite}`
    );
    state.operadores = Array.isArray(data) ? data : [];
    return state.operadores;
  }

  async function pesquisarUsuarios(termo, onlyManager = false) {
    const operadores = await carregarOperadores(termo, 50);
    if (!onlyManager) return operadores;
    return operadores.filter((u) => String(u.tipo || "").toLowerCase() === "gerente");
  }

  function closeAllModals() {
    hideEl(els.modalOverlay);
    hideEl(els.modalAbrirCaixa);
    hideEl(els.modalSangria);
    hideEl(els.modalSuprimento);
    hideEl(els.modalFecharCaixa);
  }

  function openModal(modalEl) {
    if (!modalEl) return;
    showEl(els.modalOverlay);
    showEl(modalEl);
  }

  function resetModalAbrirCaixa() {
    clearSelection(
      els.caixaAberturaOperadorLista,
      els.caixaAberturaOperadorId,
      els.caixaAberturaOperadorNome,
      "Nenhum operador selecionado."
    );
    clearSelection(
      els.caixaGerenteAberturaLista,
      els.caixaGerenteAberturaId,
      els.caixaGerenteAberturaNome,
      "Nenhum gerente selecionado."
    );

    setValue(els.caixaAberturaOperadorBusca, "");
    setValue(els.caixaGerenteAberturaBusca, "");
    setValue(els.caixaSenhaGerenteAbertura, "");
    setValue(els.caixaValorAbertura, "");
    setValue(els.caixaObservacoesAbertura, "");
    setValue(els.caixaMotivoDiferencaAbertura, "");

    hideEl(els.caixaAberturaDivergenciaBox);
  }

  function resetModalSangria() {
    clearSelection(
      els.caixaSangriaOperadorLista,
      els.caixaSangriaOperadorId,
      els.caixaSangriaOperadorNome,
      "Nenhum operador selecionado."
    );
    clearSelection(
      els.caixaGerenteSangriaLista,
      els.caixaGerenteSangriaId,
      els.caixaGerenteSangriaNome,
      "Nenhum gerente selecionado."
    );

    setValue(els.caixaSangriaOperadorBusca, "");
    setValue(els.caixaGerenteSangriaBusca, "");
    setValue(els.caixaSenhaGerenteSangria, "");
    setValue(els.caixaSangriaValor, "");
    setValue(els.caixaSangriaMotivo, "");
    setValue(els.caixaSangriaObservacoes, "");

    hideEl(els.caixaSangriaGerenteBox);
  }

  function resetModalSuprimento() {
    clearSelection(
      els.caixaSuprimentoOperadorLista,
      els.caixaSuprimentoOperadorId,
      els.caixaSuprimentoOperadorNome,
      "Nenhum operador selecionado."
    );
    clearSelection(
      els.caixaGerenteSuprimentoLista,
      els.caixaGerenteSuprimentoId,
      els.caixaGerenteSuprimentoNome,
      "Nenhum gerente selecionado."
    );

    setValue(els.caixaSuprimentoOperadorBusca, "");
    setValue(els.caixaGerenteSuprimentoBusca, "");
    setValue(els.caixaSenhaGerenteSuprimento, "");
    setValue(els.caixaSuprimentoValor, "");
    setValue(els.caixaSuprimentoMotivo, "");
    setValue(els.caixaSuprimentoObservacoes, "");

    hideEl(els.caixaSuprimentoGerenteBox);
  }

  function resetModalFecharCaixa() {
    clearSelection(
      els.caixaFechamentoOperadorLista,
      els.caixaFechamentoOperadorId,
      els.caixaFechamentoOperadorNome,
      "Nenhum operador selecionado."
    );
    clearSelection(
      els.caixaGerenteFechamentoLista,
      els.caixaGerenteFechamentoId,
      els.caixaGerenteFechamentoNome,
      "Nenhum gerente selecionado."
    );

    setValue(els.caixaFechamentoOperadorBusca, "");
    setValue(els.caixaGerenteFechamentoBusca, "");
    setValue(els.caixaSenhaGerenteFechamento, "");
    setValue(els.caixaFechamentoValor, "");
    setValue(els.caixaMotivoDiferencaFechamento, "");

    hideEl(els.caixaFechamentoDivergenciaBox);
  }

  async function handleSearchUsers(config) {
    const { inputEl, listEl, idEl, nameEl, onlyManager, selectedLabel, emptyMessage } = config;

    const termo = String(inputEl?.value || "").trim();
    if (!termo) {
      clearSelection(listEl, idEl, nameEl, emptyMessage);
      return;
    }

    const usuarios = await pesquisarUsuarios(termo, onlyManager);

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
      await carregarResumoCaixa();
    } else {
      state.caixaResumo = null;
    }

    renderCaixa();
    renderControlsState();
    return state.caixaAtual;
  }

  async function carregarResumoCaixa() {
    const caixaSessaoId = getCaixaSessaoId();
    if (!caixaSessaoId) return null;

    const data = await request(`/api/caixa/sessoes/${caixaSessaoId}/resumo`);
    state.caixaResumo = data || null;
    renderCaixa();
    return state.caixaResumo;
  }

  function renderCaixa() {
    if (!state.caixaAtual) {
      setText(els.caixaStatus, "Fechado");
      setText(els.caixaOperador, "-");
      setText(els.caixaAbertura, formatMoney(0));
      setText(els.caixaSaldo, formatMoney(0));
      return;
    }

    setText(els.caixaStatus, state.caixaAtual.status || "-");

    const operadorNome =
      state.caixaAtual.usuario_responsavel?.nome ||
      state.caixaAtual.usuario_abertura?.nome ||
      String(state.caixaAtual.usuario_responsavel_id || "-");

    setText(els.caixaOperador, operadorNome);

    setText(els.caixaAbertura, formatMoney(state.caixaAtual.valor_abertura_informado || 0));
    setText(els.caixaSaldo, formatMoney(state.caixaResumo?.saldo_dinheiro_esperado ?? 0));
  }

  function renderVendaContexto() {
    if (!hasVendaAtual()) {
      setText(els.vendaCliente, "Nenhuma venda iniciada");
      setText(els.vendaMeta, "Abra uma venda balcão ou puxe da produção.");
      setText(els.vendaNumero, "Sem venda");
      setText(els.vendaModo, "-");
      return;
    }

    const venda = state.vendaAtual;

    const nomeCliente =
      venda.modo_cliente === "REGISTERED_CLIENT"
        ? venda.nome_cliente_snapshot || "Cliente cadastrado"
        : venda.nome_cliente_snapshot || "Venda balcão";

    setText(els.vendaCliente, nomeCliente);
    setText(els.vendaMeta, venda.observacoes || "");
    setText(els.vendaNumero, venda.numero_venda || `#${venda.id}`);
    setText(els.vendaModo, venda.status || "-");
  }

  function renderTotais() {
    const venda = state.vendaAtual;
    setText(els.totalSubtotal, formatMoney(venda?.subtotal || 0));
    setText(els.totalDesconto, formatMoney(venda?.desconto_valor || 0));
    setText(els.totalAcrescimo, formatMoney(venda?.acrescimo_valor || 0));
    setText(els.totalFinal, formatMoney(venda?.valor_total || 0));

    if (els.descontoPercent) {
      const subtotal = toNumber(venda?.subtotal || 0, 0);
      const desc = toNumber(venda?.desconto_valor || 0, 0);
      const pct = subtotal > 0 ? (desc / subtotal) * 100 : 0;
      setValue(els.descontoPercent, venda ? pct.toFixed(2) : "");
    }

    syncValorPagamento();
    updateParcelasVisibility();
    renderControlsState();
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
      itens
        .map(
          (item) => `
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
      `
        )
        .join("")
    );
  }

  function renderVenda() {
    renderVendaContexto();
    renderTotais();
    renderCarrinho();
  }

  function setDisabled(el, disabled) {
    if (!el) return;
    el.disabled = !!disabled;
  }

  function toggleHidden(el) {
    if (!el) return;
    el.classList.toggle("pdv-hidden");
  }

  function syncValorPagamento() {
    if (!els.valorPagamento) return;

    els.valorPagamento.readOnly = true;

    if (!state.vendaAtual) {
      setValue(els.valorPagamento, "");
      return;
    }

    setValue(els.valorPagamento, toNumber(state.vendaAtual.valor_total, 0).toFixed(2));
  }

  function renderControlsState() {
    const podeFinalizar =
      hasCaixaAberto() && hasVendaAberta() && (state.vendaAtual?.itens?.length || 0) > 0;

    setDisabled(els.btnFinalizarVenda, !podeFinalizar);
    setDisabled(els.btnAplicarDesconto, !hasVendaAberta());
    setDisabled(els.btnZerarDesconto, !hasVendaAberta());
  }

  async function aplicarDescontoPercentual(percentValue) {
    if (!hasVendaAberta()) throw new Error("Abra uma venda antes de aplicar desconto.");

    const venda = state.vendaAtual;
    const vendaId = venda.id;

    const pct = requireNonNegativeNumber(percentValue, "Informe um desconto válido.");
    if (pct > 100) throw new Error("Desconto não pode ser maior que 100%.");

    const subtotal = toNumber(venda.subtotal, 0);
    const descontoValor = Math.max(0, Math.min(subtotal, (subtotal * pct) / 100));

    const payload = {
      desconto_valor: Number(descontoValor.toFixed(2)),
    };

    const vendaAtualizada = await request(`/api/pdv/vendas/${vendaId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });

    state.vendaAtual = vendaAtualizada;
    renderVenda();
    showAlert("Desconto aplicado.", "success");
  }

  async function zerarDesconto() {
    if (!hasVendaAberta()) throw new Error("Abra uma venda antes de zerar desconto.");

    const vendaId = state.vendaAtual.id;
    const venda = await request(`/api/pdv/vendas/${vendaId}`, {
      method: "PATCH",
      body: JSON.stringify({ desconto_valor: 0 }),
    });

    state.vendaAtual = venda;
    if (els.descontoPercent) setValue(els.descontoPercent, "0.00");
    renderVenda();
    showAlert("Desconto zerado.", "success");
  }

  async function finalizarVendaAtual() {
    if (!hasCaixaAberto()) throw new Error("Abra o caixa antes de finalizar a venda.");
    if (!hasVendaAberta()) throw new Error("Nenhuma venda aberta para finalizar.");

    const venda = state.vendaAtual;
    const vendaId = venda.id;

    const formaPagamento = String(els.formaPagamento?.value || "DINHEIRO").trim() || "DINHEIRO";
    const valor = toNumber(venda.valor_total, 0);
    const quantidadeParcelas = getQuantidadeParcelasSelecionada();

    if (valor < 0) throw new Error("Total inválido.");

    const payload = {
      pagamento: {
        forma_pagamento: formaPagamento,
        valor: Number(valor.toFixed(2)),
        quantidade_parcelas: quantidadeParcelas,
      },
    };

    const result = await request(`/api/pdv/vendas/${vendaId}/checkout`, {
      method: "POST",
      body: JSON.stringify(payload),
    });

    state.vendaAtual = null;

    if (els.buscaProduto) setValue(els.buscaProduto, "");
    state.produtosEncontrados = [];
    if (els.produtosResultado) {
      setHtml(els.produtosResultado, `<div class="pdv-empty-state">Nenhum produto pesquisado.</div>`);
    }
    if (els.descontoPercent) setValue(els.descontoPercent, "");
    if (els.quantidadeParcelas) setValue(els.quantidadeParcelas, "1");
    updateParcelasVisibility();

    renderVenda();
    renderControlsState();
    showAlert(result?.mensagem || "Venda finalizada com sucesso.", "success");

    try {
      await carregarResumoCaixa();
    } catch (error) {
      console.warn("Falha ao recarregar resumo do caixa:", error);
    }

    try {
      await carregarProducaoPronta();
      await carregarAtendimentosProntos();
    } catch (error) {
      console.warn("Falha ao atualizar prontos após finalizar:", error);
    }
  }

  function renderProducaoLista() {
    if (!els.producaoLista) return;

    const itens = state.producaoPronta || [];
    if (!itens.length) {
      setHtml(els.producaoLista, `<div class="pdv-empty-state">Nenhum item pronto para cobrança.</div>`);
      return;
    }

    setHtml(
      els.producaoLista,
      itens
        .map((item) => {
          const cliente = escapeHtml(item.cliente_nome || "Cliente");
          const pet = item.pet_nome ? ` - ${escapeHtml(item.pet_nome)}` : "";
          const descricao = escapeHtml(item.descricao || "");
          const valor = formatMoney(item.valor_total || 0);

          return `
          <div class="pdv-producao-item">
            <div class="pdv-producao-item__info">
              <strong>${cliente}${pet}</strong>
              <div class="pdv-muted">${descricao}</div>
            </div>
            <div class="pdv-producao-item__actions">
              <strong>${valor}</strong>
              <button
                type="button"
                class="pdv-btn pdv-btn-primary"
                data-action="puxar-producao"
                data-producao-id="${escapeHtml(item.producao_id)}"
              >
                Puxar
              </button>
            </div>
          </div>
        `;
        })
        .join("")
    );
  }

  async function carregarProducaoPronta() {
    const empresaId = getEmpresaId();
    const data = await request(`/api/pdv/producao/prontos?empresa_id=${empresaId}`);
    state.producaoPronta = Array.isArray(data) ? data : [];
    renderProducaoLista();
    return state.producaoPronta;
  }

  async function puxarProducaoParaVenda(producaoId) {
    if (!hasCaixaAberto()) throw new Error("Abra o caixa antes de puxar itens da produção.");

    const empresaId = getEmpresaId();
    const caixaSessaoId = getCaixaSessaoId();
    if (!caixaSessaoId) throw new Error("Sessão de caixa inválida.");

    const payload = {
      empresa_id: empresaId,
      caixa_sessao_id: caixaSessaoId,
      producao_id: Number(producaoId),
    };

    const venda = await request("/api/pdv/vendas/producao", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    state.vendaAtual = venda;
    renderVenda();
    renderControlsState();
    showAlert("Produção puxada para a venda atual.", "success");

    try {
      await carregarProducaoPronta();
    } catch (error) {
      console.warn("Falha ao atualizar prontos da produção:", error);
    }

    return venda;
  }

  function renderAtendimentosLista() {
    if (!els.atendimentosLista) return;

    const itens = state.atendimentosProntos || [];
    if (!itens.length) {
      setHtml(els.atendimentosLista, `<div class="pdv-empty-state">Nenhum atendimento pronto.</div>`);
      return;
    }

    setHtml(
      els.atendimentosLista,
      itens
        .map((a) => {
          const cliente = escapeHtml(a.cliente_nome || "Cliente");
          const pet = a.pet_nome ? ` - ${escapeHtml(a.pet_nome)}` : "";
          const descricao = escapeHtml(a.descricao || "Atendimento");
          const valor = formatMoney(a.valor_total || 0);

          return `
          <div class="pdv-producao-item">
            <div class="pdv-producao-item__info">
              <strong>${cliente}${pet}</strong>
              <div class="pdv-muted">${descricao}</div>
            </div>
            <div class="pdv-producao-item__actions">
              <strong>${valor}</strong>
              <button
                type="button"
                class="pdv-btn pdv-btn-primary"
                data-action="adicionar-atendimento"
                data-atendimento-id="${escapeHtml(a.atendimento_id)}"
                data-cliente-id="${escapeHtml(a.cliente_id)}"
              >
                Adicionar
              </button>
            </div>
          </div>
        `;
        })
        .join("")
    );
  }

  async function carregarAtendimentosProntos() {
    const empresaId = getEmpresaId();
    const data = await request(`/api/pdv/atendimentos/prontos?empresa_id=${empresaId}`);
    state.atendimentosProntos = Array.isArray(data) ? data : [];
    renderAtendimentosLista();
    return state.atendimentosProntos;
  }

  async function criarVendaParaCliente(clienteId) {
    if (!hasCaixaAberto()) throw new Error("Abra o caixa antes.");
    const empresaId = getEmpresaId();
    const caixaSessaoId = getCaixaSessaoId();
    if (!caixaSessaoId) throw new Error("Sessão de caixa inválida.");

    const venda = await request("/api/pdv/vendas", {
      method: "POST",
      body: JSON.stringify({
        empresa_id: empresaId,
        caixa_sessao_id: caixaSessaoId,
        modo_cliente: "REGISTERED_CLIENT",
        cliente_id: Number(clienteId),
      }),
    });

    state.vendaAtual = venda;
    renderVenda();
    renderControlsState();
    return venda;
  }

  async function adicionarAtendimentoNaVenda(atendimentoId, clienteId) {
    if (!hasCaixaAberto()) throw new Error("Abra o caixa antes.");

    if (!hasVendaAberta()) {
      await criarVendaParaCliente(clienteId);
    }

    if (!hasVendaAberta()) throw new Error("Não foi possível abrir uma venda.");

    if (state.vendaAtual.modo_cliente !== "REGISTERED_CLIENT") {
      throw new Error("Atendimento veterinário exige venda com cliente cadastrado.");
    }
    if (Number(state.vendaAtual.cliente_id) !== Number(clienteId)) {
      throw new Error("Esse atendimento é de outro cliente. Finalize/cancele a venda atual e tente novamente.");
    }

    const vendaId = state.vendaAtual.id;

    const vendaAtualizada = await request(`/api/pdv/vendas/${vendaId}/itens`, {
      method: "POST",
      body: JSON.stringify({
        tipo_item: "SERVICE",
        atendimento_clinico_id: Number(atendimentoId),
      }),
    });

    state.vendaAtual = vendaAtualizada;
    renderVenda();
    renderControlsState();
    showAlert("Atendimento adicionado na venda.", "success");

    state.atendimentosProntos = (state.atendimentosProntos || []).filter(
      (x) => Number(x.atendimento_id) !== Number(atendimentoId)
    );
    renderAtendimentosLista();
  }

  function bindFloatingActions() {
    els.btnFloatingMinimizar?.addEventListener("click", () => {
      if (!els.floatingBody) return;
      els.floatingBody.classList.toggle("pdv-hidden");
    });

    els.btnFloatingToggleCaixa?.addEventListener("click", () => toggleHidden(els.caixaCard));
    els.btnFloatingToggleProntos?.addEventListener("click", () => toggleHidden(els.producaoSidebar));

    els.btnFloatingAbrirCaixa?.addEventListener("click", () => els.btnAbrirCaixa?.click());
    els.btnFloatingSangria?.addEventListener("click", () => els.btnSangria?.click());
    els.btnFloatingSuprimento?.addEventListener("click", () => els.btnSuprimento?.click());
    els.btnFloatingFecharCaixa?.addEventListener("click", () => els.btnFecharCaixa?.click());
    els.btnFloatingAtualizarProntos?.addEventListener("click", () => els.btnAtualizarProducao?.click());
  }

  function collectAberturaPayload() {
    const empresaId = getEmpresaId();

    const operadorId = toNumber(els.caixaAberturaOperadorId?.value, 0);
    const operadorNome = String(els.caixaAberturaOperadorNome?.value || "").trim();

    const valorAbertura = requireNonNegativeNumber(
      els.caixaValorAbertura?.value,
      "Informe um valor de abertura válido."
    );

    const observacoes = String(els.caixaObservacoesAbertura?.value || "").trim();

    const motivoDiferencaAbertura = String(els.caixaMotivoDiferencaAbertura?.value || "").trim();

    const gerenteId = toNumber(els.caixaGerenteAberturaId?.value, 0);
    const gerenteNome = String(els.caixaGerenteAberturaNome?.value || "").trim();
    const senhaGerente = String(els.caixaSenhaGerenteAbertura?.value || "").trim();

    return {
      empresa_id: empresaId,
      usuario_responsavel_id: operadorId || null,
      usuario_responsavel_nome: operadorNome || null,
      usuario_abertura_id: operadorId || null,
      usuario_abertura_nome: operadorNome || null,
      valor_abertura_informado: valorAbertura,
      observacoes: observacoes || null,
      motivo_diferenca_abertura: motivoDiferencaAbertura || null,
      gerente_abertura_id: gerenteId || null,
      gerente_abertura_nome: gerenteNome || null,
      senha_gerente: senhaGerente || null,
    };
  }

  function collectSangriaPayload() {
    const empresaId = getEmpresaId();
    const caixaSessaoId = getCaixaSessaoId();
    if (!caixaSessaoId) throw new Error("Sessão de caixa inválida.");

    const operadorId = toNumber(els.caixaSangriaOperadorId?.value, 0);
    const operadorNome = String(els.caixaSangriaOperadorNome?.value || "").trim();

    const valor = requirePositiveNumber(els.caixaSangriaValor?.value, "Informe um valor de sangria válido.");

    const motivo = requireText(els.caixaSangriaMotivo?.value, "Informe um motivo.");
    const observacoes = String(els.caixaSangriaObservacoes?.value || "").trim();

    const gerenteId = toNumber(els.caixaGerenteSangriaId?.value, 0);
    const gerenteNome = String(els.caixaGerenteSangriaNome?.value || "").trim();
    const senhaGerente = String(els.caixaSenhaGerenteSangria?.value || "").trim();

    return {
      empresa_id: empresaId,
      caixa_sessao_id: caixaSessaoId,
      valor,
      usuario_id: operadorId || null,
      usuario_nome: operadorNome || null,
      motivo,
      observacoes: observacoes || null,
      gerente_autorizador_id: gerenteId || null,
      gerente_autorizador_nome: gerenteNome || null,
      senha_gerente: senhaGerente || null,
    };
  }

  function collectSuprimentoPayload() {
    const empresaId = getEmpresaId();
    const caixaSessaoId = getCaixaSessaoId();
    if (!caixaSessaoId) throw new Error("Sessão de caixa inválida.");

    const operadorId = toNumber(els.caixaSuprimentoOperadorId?.value, 0);
    const operadorNome = String(els.caixaSuprimentoOperadorNome?.value || "").trim();

    const valor = requirePositiveNumber(els.caixaSuprimentoValor?.value, "Informe um valor de suprimento válido.");

    const motivo = requireText(els.caixaSuprimentoMotivo?.value, "Informe um motivo.");
    const observacoes = String(els.caixaSuprimentoObservacoes?.value || "").trim();

    const gerenteId = toNumber(els.caixaGerenteSuprimentoId?.value, 0);
    const gerenteNome = String(els.caixaGerenteSuprimentoNome?.value || "").trim();
    const senhaGerente = String(els.caixaSenhaGerenteSuprimento?.value || "").trim();

    return {
      empresa_id: empresaId,
      caixa_sessao_id: caixaSessaoId,
      valor,
      usuario_id: operadorId || null,
      usuario_nome: operadorNome || null,
      motivo,
      observacoes: observacoes || null,
      gerente_autorizador_id: gerenteId || null,
      gerente_autorizador_nome: gerenteNome || null,
      senha_gerente: senhaGerente || null,
    };
  }

  function collectFechamentoPayload() {
    const caixaSessaoId = getCaixaSessaoId();
    if (!caixaSessaoId) throw new Error("Sessão de caixa inválida.");

    const operadorId = toNumber(els.caixaFechamentoOperadorId?.value, 0);
    const operadorNome = String(els.caixaFechamentoOperadorNome?.value || "").trim();

    const valor = requireNonNegativeNumber(els.caixaFechamentoValor?.value, "Informe um valor de fechamento válido.");

    const motivo = String(els.caixaMotivoDiferencaFechamento?.value || "").trim();

    const gerenteId = toNumber(els.caixaGerenteFechamentoId?.value, 0);
    const gerenteNome = String(els.caixaGerenteFechamentoNome?.value || "").trim();
    const senhaGerente = String(els.caixaSenhaGerenteFechamento?.value || "").trim();

    return {
      usuario_fechamento_id: operadorId || null,
      usuario_fechamento_nome: operadorNome || null,
      valor_fechamento_informado: valor,
      motivo_diferenca_fechamento: motivo || null,
      gerente_fechamento_id: gerenteId || null,
      gerente_fechamento_nome: gerenteNome || null,
      senha_gerente: senhaGerente || null,
    };
  }

  async function submitAberturaCaixa() {
    const payload = collectAberturaPayload();

    const result = await request("/api/caixa/abrir", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    if (result?.caixa_sessao) {
      state.caixaAtual = result.caixa_sessao;
      await carregarResumoCaixa();
    }

    closeAllModals();
    showAlert(result?.mensagem || "Caixa aberto.", "success");
    renderCaixa();
    renderControlsState();
  }

  async function submitSangria() {
    const payload = collectSangriaPayload();

    const result = await request("/api/caixa/sangria", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    if (result?.caixa_sessao) {
      state.caixaAtual = result.caixa_sessao;
      await carregarResumoCaixa();
    }

    closeAllModals();
    showAlert(result?.mensagem || "Sangria registrada.", "success");
    renderCaixa();
    renderControlsState();
  }

  async function submitSuprimento() {
    const payload = collectSuprimentoPayload();

    const result = await request("/api/caixa/suprimento", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    if (result?.caixa_sessao) {
      state.caixaAtual = result.caixa_sessao;
      await carregarResumoCaixa();
    }

    closeAllModals();
    showAlert(result?.mensagem || "Suprimento registrado.", "success");
    renderCaixa();
    renderControlsState();
  }

  async function submitFechamentoCaixa() {
    const caixaSessaoId = getCaixaSessaoId();
    if (!caixaSessaoId) throw new Error("Sessão de caixa inválida.");

    const payload = collectFechamentoPayload();

    const result = await request(`/api/caixa/sessoes/${caixaSessaoId}/fechar`, {
      method: "POST",
      body: JSON.stringify(payload),
    });

    if (result?.caixa_sessao) {
      state.caixaAtual = result.caixa_sessao;
      await carregarResumoCaixa();
    }

    closeAllModals();
    showAlert(result?.mensagem || "Caixa fechado.", "success");
    renderCaixa();
    renderControlsState();
  }

  async function openFecharCaixaModal() {
    if (!hasCaixaAberto()) throw new Error("Não há caixa aberto para fechar.");

    resetModalFecharCaixa();

    if (els.caixaFechamentoSaldoEsperado) {
      setText(els.caixaFechamentoSaldoEsperado, formatMoney(state.caixaResumo?.saldo_dinheiro_esperado ?? 0));
    }

    openModal(els.modalFecharCaixa);
  }

  function bindModalSearch(buttonEl, config) {
    buttonEl?.addEventListener("click", async () => {
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

    els.btnAtualizarProducao?.addEventListener("click", async () => {
      try {
        await carregarProducaoPronta();
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnAtualizarAtendimentos?.addEventListener("click", async () => {
      try {
        await carregarAtendimentosProntos();
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnBuscarProduto?.addEventListener("click", async (event) => {
      try {
        await handleBuscarProdutosAction(event);
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.buscaProduto?.addEventListener("keydown", async (event) => {
      if (event.key !== "Enter") return;
      try {
        await handleBuscarProdutosAction(event);
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.formaPagamento?.addEventListener("change", () => {
      updateParcelasVisibility();
    });

    els.produtosResultado?.addEventListener("click", async (event) => {
      const btn = event.target?.closest?.('[data-action="adicionar-produto"]');
      if (!btn) return;

      try {
        const produtoId = btn.getAttribute("data-produto-id");
        if (!produtoId) throw new Error("Produto inválido.");
        await adicionarProdutoNaVenda(produtoId);
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.producaoLista?.addEventListener("click", async (event) => {
      const btn = event.target?.closest?.('[data-action="puxar-producao"]');
      if (!btn) return;

      try {
        const producaoId = btn.getAttribute("data-producao-id");
        if (!producaoId) throw new Error("Produção inválida.");
        await puxarProducaoParaVenda(producaoId);
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.atendimentosLista?.addEventListener("click", async (event) => {
      const btn = event.target?.closest?.('[data-action="adicionar-atendimento"]');
      if (!btn) return;

      try {
        const atendimentoId = btn.getAttribute("data-atendimento-id");
        const clienteId = btn.getAttribute("data-cliente-id");
        if (!atendimentoId || !clienteId) throw new Error("Atendimento inválido.");
        await adicionarAtendimentoNaVenda(atendimentoId, clienteId);
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnVendaBalcao?.addEventListener("click", async () => {
      try {
        await criarVendaBalcao();
        showAlert("Venda balcão iniciada.", "success");
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnAplicarDesconto?.addEventListener("click", async () => {
      try {
        await aplicarDescontoPercentual(els.descontoPercent?.value);
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnZerarDesconto?.addEventListener("click", async () => {
      try {
        await zerarDesconto();
      } catch (error) {
        showAlert(error.message, "danger");
      }
    });

    els.btnFinalizarVenda?.addEventListener("click", async () => {
      try {
        await finalizarVendaAtual();
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
    syncValorPagamento();

    if (els.produtosResultado) {
      setHtml(els.produtosResultado, `<div class="pdv-empty-state">Nenhum produto pesquisado.</div>`);
    }

    ensureParcelasControl();
    updateParcelasVisibility();

    bindEvents();
    bindFloatingActions();

    try {
      await carregarCaixaAtual();
    } catch (error) {
      console.warn("Falha ao carregar caixa atual:", error);
    }

    try {
      await carregarProducaoPronta();
      await carregarAtendimentosProntos();
    } catch (error) {
      console.warn("Falha ao carregar prontos (produção/atendimentos):", error);
    }
  }

  document.addEventListener("DOMContentLoaded", init);
})();