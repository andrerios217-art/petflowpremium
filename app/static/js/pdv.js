(function () {
  const state = {
    empresaId: 1,
    vendaAtual: null,
    clientes: [],
    atendimentos: [],
    loading: false,
  };

  const els = {
    alertaGeral: document.getElementById("pdv-alerta-geral"),

    empresaId: document.getElementById("pdv-empresa-id"),
    clienteBusca: document.getElementById("pdv-cliente-busca"),
    clientesLista: document.getElementById("pdv-clientes-lista"),

    btnBuscarCliente: document.getElementById("btn-buscar-cliente"),
    btnIniciarBalcao: document.getElementById("btn-iniciar-balcao"),
    btnRecarregarPdv: document.getElementById("btn-recarregar-pdv"),
    btnRecarregarAtendimentos: document.getElementById("btn-recarregar-atendimentos"),

    contextoStatus: document.getElementById("pdv-contexto-status"),
    contextoNumero: document.getElementById("pdv-contexto-numero"),
    contextoModo: document.getElementById("pdv-contexto-modo"),
    contextoCliente: document.getElementById("pdv-contexto-cliente"),

    atendimentosLista: document.getElementById("pdv-atendimentos-lista"),
    atendimentosAlerta: document.getElementById("pdv-atendimentos-alerta"),

    produtoId: document.getElementById("pdv-produto-id"),
    produtoQuantidade: document.getElementById("pdv-produto-quantidade"),
    produtoDescricao: document.getElementById("pdv-produto-descricao"),
    produtoValorUnitario: document.getElementById("pdv-produto-valor-unitario"),
    produtoDesconto: document.getElementById("pdv-produto-desconto"),
    produtoObservacao: document.getElementById("pdv-produto-observacao"),
    btnAdicionarProduto: document.getElementById("btn-adicionar-produto"),

    carrinhoLista: document.getElementById("pdv-carrinho-lista"),

    descontoVenda: document.getElementById("pdv-desconto-venda"),
    acrescimoVenda: document.getElementById("pdv-acrescimo-venda"),
    observacoesVenda: document.getElementById("pdv-observacoes-venda"),
    btnAtualizarVenda: document.getElementById("btn-atualizar-venda"),

    totalSubtotal: document.getElementById("pdv-total-subtotal"),
    totalDesconto: document.getElementById("pdv-total-desconto"),
    totalAcrescimo: document.getElementById("pdv-total-acrescimo"),
    totalFinal: document.getElementById("pdv-total-final"),

    formaPagamento: document.getElementById("pdv-forma-pagamento"),
    valorPagamento: document.getElementById("pdv-valor-pagamento"),
    referenciaPagamento: document.getElementById("pdv-referencia-pagamento"),
    observacoesPagamento: document.getElementById("pdv-observacoes-pagamento"),
    btnFinalizarVenda: document.getElementById("btn-finalizar-venda"),

    btnCancelarVenda: document.getElementById("btn-cancelar-venda"),
  };

  function toNumber(value, fallback = 0) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function formatMoney(value) {
    const number = toNumber(value, 0);
    return number.toLocaleString("pt-BR", {
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
    if (!els.alertaGeral) return;

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
      const detail =
        (isJson && (data.detail || data.message)) ||
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

  function hasVendaAberta() {
    return !!state.vendaAtual && state.vendaAtual.status === "ABERTA";
  }

  function isWalkIn() {
    return hasVendaAberta() && state.vendaAtual.modo_cliente === "WALK_IN";
  }

  function isRegisteredClient() {
    return hasVendaAberta() && state.vendaAtual.modo_cliente === "REGISTERED_CLIENT";
  }

  function syncVendaFields() {
    const venda = state.vendaAtual;

    if (!venda) {
      els.descontoVenda.value = "0";
      els.acrescimoVenda.value = "0";
      els.observacoesVenda.value = "";
      els.valorPagamento.value = "";
      return;
    }

    els.descontoVenda.value = toNumber(venda.desconto_valor, 0).toFixed(2);
    els.acrescimoVenda.value = toNumber(venda.acrescimo_valor, 0).toFixed(2);
    els.observacoesVenda.value = venda.observacoes || "";
    els.valorPagamento.value = toNumber(venda.valor_total, 0).toFixed(2);
  }

  function renderContexto() {
    const venda = state.vendaAtual;

    if (!venda) {
      els.contextoStatus.textContent = "Nenhuma venda aberta";
      els.contextoNumero.textContent = "-";
      els.contextoModo.textContent = "-";
      els.contextoCliente.textContent = "-";
      return;
    }

    const clienteNome =
      venda.cliente?.nome ||
      venda.nome_cliente_snapshot ||
      (venda.modo_cliente === "WALK_IN" ? "Venda balcão" : "-");

    els.contextoStatus.textContent = venda.status || "-";
    els.contextoNumero.textContent = venda.numero_venda || `#${venda.id}`;
    els.contextoModo.textContent =
      venda.modo_cliente === "WALK_IN" ? "Balcão" : "Cliente cadastrado";
    els.contextoCliente.textContent = clienteNome;
  }

  function renderTotais() {
    const venda = state.vendaAtual;

    els.totalSubtotal.textContent = formatMoney(venda?.subtotal || 0);
    els.totalDesconto.textContent = formatMoney(venda?.desconto_valor || 0);
    els.totalAcrescimo.textContent = formatMoney(venda?.acrescimo_valor || 0);
    els.totalFinal.textContent = formatMoney(venda?.valor_total || 0);
  }

  function renderCarrinho() {
    const venda = state.vendaAtual;
    const itens = venda?.itens || [];

    if (!itens.length) {
      els.carrinhoLista.innerHTML =
        '<div class="pdv-list-empty">Nenhum item adicionado na venda.</div>';
      return;
    }

    els.carrinhoLista.innerHTML = itens
      .map((item) => {
        const badgeClass =
          item.tipo_item === "SERVICE" ? "pdv-badge-blue" : "pdv-badge-green";
        const badgeText = item.tipo_item === "SERVICE" ? "Atendimento" : "Produto";

        return `
          <div class="pdv-cart-item">
            <div class="pdv-cart-item-top">
              <div>
                <div class="pdv-item-card-title">${escapeHtml(item.descricao_snapshot)}</div>
                <div class="pdv-item-card-subtitle">
                  Qtde: ${toNumber(item.quantidade, 0)} |
                  Unitário: ${formatMoney(item.valor_unitario)} |
                  Desconto: ${formatMoney(item.desconto_valor)}
                </div>
                ${
                  item.observacao
                    ? `<div class="pdv-item-card-subtitle">${escapeHtml(item.observacao)}</div>`
                    : ""
                }
              </div>

              <div style="display:flex; flex-direction:column; align-items:end; gap:8px;">
                <span class="pdv-badge ${badgeClass}">${badgeText}</span>
                <strong>${formatMoney(item.valor_total)}</strong>
              </div>
            </div>

            <div class="pdv-item-card-actions">
              <button
                class="pdv-btn pdv-btn-danger btn-remover-item"
                type="button"
                data-item-id="${item.id}"
              >
                Remover
              </button>
            </div>
          </div>
        `;
      })
      .join("");

    document.querySelectorAll(".btn-remover-item").forEach((button) => {
      button.addEventListener("click", async () => {
        const itemId = button.dataset.itemId;
        if (!itemId || !state.vendaAtual) return;

        const confirmar = window.confirm("Deseja remover este item da venda?");
        if (!confirmar) return;

        try {
          const venda = await request(
            `/api/pdv/vendas/${state.vendaAtual.id}/itens/${itemId}`,
            {
              method: "DELETE",
            }
          );
          state.vendaAtual = venda;
          renderVendaCompleta();
          showAlert("Item removido da venda.", "info");
        } catch (error) {
          showAlert(error.message, "danger");
        }
      });
    });
  }

  function renderClientes() {
    if (!state.clientes.length) {
      els.clientesLista.innerHTML =
        '<div class="pdv-list-empty">Nenhum cliente encontrado.</div>';
      return;
    }

    els.clientesLista.innerHTML = state.clientes
      .map((cliente) => {
        const subtitleParts = [];
        if (cliente.cpf) subtitleParts.push(`CPF: ${escapeHtml(cliente.cpf)}`);
        if (cliente.telefone) subtitleParts.push(`Tel.: ${escapeHtml(cliente.telefone)}`);

        return `
          <div class="pdv-item-card">
            <div class="pdv-item-card-header">
              <div>
                <div class="pdv-item-card-title">${escapeHtml(cliente.nome)}</div>
                <div class="pdv-item-card-subtitle">${subtitleParts.join(" | ") || "Sem dados complementares"}</div>
              </div>
            </div>

            <div class="pdv-item-card-actions">
              <button
                class="pdv-btn pdv-btn-primary btn-selecionar-cliente"
                type="button"
                data-cliente-id="${cliente.id}"
                data-cliente-nome="${escapeHtml(cliente.nome)}"
              >
                Iniciar venda
              </button>
            </div>
          </div>
        `;
      })
      .join("");

    document.querySelectorAll(".btn-selecionar-cliente").forEach((button) => {
      button.addEventListener("click", async () => {
        const clienteId = toNumber(button.dataset.clienteId, 0);
        if (!clienteId) return;
        await iniciarVendaCliente(clienteId);
      });
    });
  }

  function renderAtendimentos() {
    if (isWalkIn()) {
      els.atendimentosLista.innerHTML =
        '<div class="pdv-list-empty">Venda balcão não permite adicionar atendimentos.</div>';
      return;
    }

    if (!state.atendimentos.length) {
      els.atendimentosLista.innerHTML =
        '<div class="pdv-list-empty">Nenhum atendimento pronto para cobrança encontrado.</div>';
      return;
    }

    els.atendimentosLista.innerHTML = state.atendimentos
      .map((atendimento) => {
        return `
          <div class="pdv-item-card">
            <div class="pdv-item-card-header">
              <div>
                <div class="pdv-item-card-title">${escapeHtml(atendimento.descricao)}</div>
                <div class="pdv-item-card-subtitle">
                  Cliente: ${escapeHtml(atendimento.cliente_nome || "-")}
                  ${atendimento.pet_nome ? ` | Pet: ${escapeHtml(atendimento.pet_nome)}` : ""}
                </div>
              </div>
              <div class="pdv-item-card-value">${formatMoney(atendimento.valor_total)}</div>
            </div>

            <div class="pdv-item-card-actions">
              <button
                class="pdv-btn pdv-btn-primary btn-adicionar-atendimento"
                type="button"
                data-atendimento-id="${atendimento.atendimento_id}"
              >
                Adicionar
              </button>
            </div>
          </div>
        `;
      })
      .join("");

    document.querySelectorAll(".btn-adicionar-atendimento").forEach((button) => {
      button.addEventListener("click", async () => {
        const atendimentoId = toNumber(button.dataset.atendimentoId, 0);
        if (!atendimentoId) return;
        await adicionarAtendimentoNaVenda(atendimentoId);
      });
    });
  }

  function renderVendaCompleta() {
    renderContexto();
    renderTotais();
    renderCarrinho();
    syncVendaFields();

    if (!state.vendaAtual) {
      showAlert(
        "Selecione um cliente cadastrado ou inicie uma venda balcão para começar.",
        "info"
      );
      return;
    }

    if (state.vendaAtual.modo_cliente === "WALK_IN") {
      showAlert(
        "Venda em modo balcão aberta. Você pode adicionar produtos e fechar com pagamento integral.",
        "info"
      );
    } else {
      showAlert(
        "Venda com cliente cadastrado aberta. Você pode adicionar atendimentos e produtos.",
        "info"
      );
    }
  }

  async function carregarAtendimentos() {
    try {
      const empresaId = getEmpresaId();
      const clienteId = isRegisteredClient() ? state.vendaAtual.cliente_id : null;

      let url = `/api/pdv/atendimentos/prontos?empresa_id=${empresaId}`;
      if (clienteId) {
        url += `&cliente_id=${clienteId}`;
      }

      const data = await request(url);
      state.atendimentos = Array.isArray(data) ? data : [];
      renderAtendimentos();
    } catch (error) {
      state.atendimentos = [];
      renderAtendimentos();
      showAlert(error.message, "danger");
    }
  }

  async function buscarClientes() {
    try {
      const empresaId = getEmpresaId();
      const termo = (els.clienteBusca?.value || "").trim();

      if (!termo) {
        showAlert("Informe um termo para buscar clientes.", "warning");
        return;
      }

      const url = `/api/pdv/clientes/busca?empresa_id=${empresaId}&q=${encodeURIComponent(
        termo
      )}&limite=20`;

      const data = await request(url);
      state.clientes = Array.isArray(data) ? data : [];
      renderClientes();

      if (!state.clientes.length) {
        showAlert("Nenhum cliente encontrado para a busca informada.", "warning");
      } else {
        showAlert("Clientes carregados com sucesso.", "info");
      }
    } catch (error) {
      state.clientes = [];
      renderClientes();
      showAlert(error.message, "danger");
    }
  }

  async function iniciarVendaCliente(clienteId) {
    try {
      const payload = {
        empresa_id: getEmpresaId(),
        modo_cliente: "REGISTERED_CLIENT",
        cliente_id: clienteId,
        observacoes: "",
      };

      const venda = await request("/api/pdv/vendas", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      state.vendaAtual = venda;
      renderVendaCompleta();
      await carregarAtendimentos();
      showAlert("Venda com cliente cadastrada criada com sucesso.", "info");
    } catch (error) {
      showAlert(error.message, "danger");
    }
  }

  async function iniciarVendaBalcao() {
    try {
      const payload = {
        empresa_id: getEmpresaId(),
        modo_cliente: "WALK_IN",
        nome_cliente_snapshot: "Venda balcão",
        observacoes: "",
      };

      const venda = await request("/api/pdv/vendas", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      state.vendaAtual = venda;
      state.atendimentos = [];
      renderVendaCompleta();
      renderAtendimentos();
      showAlert("Venda balcão criada com sucesso.", "info");
    } catch (error) {
      showAlert(error.message, "danger");
    }
  }

  async function adicionarProdutoNaVenda() {
    try {
      if (!hasVendaAberta()) {
        showAlert("Abra uma venda antes de adicionar produtos.", "warning");
        return;
      }

      const produtoId = toNumber(els.produtoId?.value, 0);
      const quantidade = toNumber(els.produtoQuantidade?.value, 1);
      const descricao = (els.produtoDescricao?.value || "").trim();
      const valorUnitario = toNumber(els.produtoValorUnitario?.value, NaN);
      const desconto = toNumber(els.produtoDesconto?.value, 0);
      const observacao = (els.produtoObservacao?.value || "").trim();

      if (!produtoId) {
        showAlert("Informe o ID do produto.", "warning");
        return;
      }

      if (!descricao) {
        showAlert("Informe a descrição do produto.", "warning");
        return;
      }

      if (!Number.isFinite(valorUnitario) || valorUnitario < 0) {
        showAlert("Informe um valor unitário válido.", "warning");
        return;
      }

      const payload = {
        tipo_item: "PRODUCT",
        produto_id: produtoId,
        descricao_snapshot: descricao,
        quantidade: quantidade,
        valor_unitario: valorUnitario,
        desconto_valor: desconto,
        observacao: observacao || null,
      };

      const venda = await request(`/api/pdv/vendas/${state.vendaAtual.id}/itens`, {
        method: "POST",
        body: JSON.stringify(payload),
      });

      state.vendaAtual = venda;
      renderVendaCompleta();

      els.produtoId.value = "";
      els.produtoQuantidade.value = "1";
      els.produtoDescricao.value = "";
      els.produtoValorUnitario.value = "";
      els.produtoDesconto.value = "0";
      els.produtoObservacao.value = "";

      showAlert("Produto adicionado na venda.", "info");
    } catch (error) {
      showAlert(error.message, "danger");
    }
  }

  async function adicionarAtendimentoNaVenda(atendimentoId) {
    try {
      if (!hasVendaAberta()) {
        showAlert("Abra uma venda antes de adicionar atendimentos.", "warning");
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
      renderVendaCompleta();
      await carregarAtendimentos();
      showAlert("Atendimento adicionado na venda.", "info");
    } catch (error) {
      showAlert(error.message, "danger");
    }
  }

  async function atualizarVendaAtual() {
    try {
      if (!hasVendaAberta()) {
        showAlert("Abra uma venda antes de atualizar os ajustes.", "warning");
        return;
      }

      const payload = {
        desconto_valor: toNumber(els.descontoVenda?.value, 0),
        acrescimo_valor: toNumber(els.acrescimoVenda?.value, 0),
        observacoes: (els.observacoesVenda?.value || "").trim() || null,
      };

      const venda = await request(`/api/pdv/vendas/${state.vendaAtual.id}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });

      state.vendaAtual = venda;
      renderVendaCompleta();
      showAlert("Venda atualizada com sucesso.", "info");
    } catch (error) {
      showAlert(error.message, "danger");
    }
  }

  async function finalizarVendaAtual() {
    try {
      if (!hasVendaAberta()) {
        showAlert("Abra uma venda antes de finalizar.", "warning");
        return;
      }

      const valorTotal = toNumber(state.vendaAtual?.valor_total, 0);
      const valorPagamento = toNumber(els.valorPagamento?.value, NaN);

      if (!Number.isFinite(valorPagamento) || valorPagamento <= 0) {
        showAlert("Informe um valor de pagamento válido.", "warning");
        return;
      }

      if (valorPagamento !== valorTotal) {
        showAlert("A venda só pode ser finalizada com pagamento integral.", "warning");
        return;
      }

      const confirmar = window.confirm(
        `Confirmar fechamento da venda no valor de ${formatMoney(valorTotal)}?`
      );
      if (!confirmar) return;

      const payload = {
        pagamento: {
          forma_pagamento: els.formaPagamento?.value || "DINHEIRO",
          valor: valorPagamento,
          referencia: (els.referenciaPagamento?.value || "").trim() || null,
          observacoes: (els.observacoesPagamento?.value || "").trim() || null,
          usuario_id: null,
        },
        observacoes: (els.observacoesVenda?.value || "").trim() || null,
      };

      const result = await request(`/api/pdv/vendas/${state.vendaAtual.id}/checkout`, {
        method: "POST",
        body: JSON.stringify(payload),
      });

      state.vendaAtual = result.venda || null;
      renderVendaCompleta();
      await carregarAtendimentos();

      showAlert(result.mensagem || "Venda finalizada com sucesso.", "info");
    } catch (error) {
      showAlert(error.message, "danger");
    }
  }

  async function cancelarVendaAtual() {
    try {
      if (!state.vendaAtual) {
        showAlert("Nenhuma venda carregada para cancelamento.", "warning");
        return;
      }

      const confirmar = window.confirm("Deseja realmente cancelar a venda atual?");
      if (!confirmar) return;

      const payload = {
        motivo_cancelamento: "Cancelamento manual pelo operador",
        usuario_cancelamento_id: null,
      };

      const result = await request(`/api/pdv/vendas/${state.vendaAtual.id}/cancelar`, {
        method: "POST",
        body: JSON.stringify(payload),
      });

      state.vendaAtual = result.venda || null;
      renderVendaCompleta();
      await carregarAtendimentos();

      showAlert(result.mensagem || "Venda cancelada com sucesso.", "info");
    } catch (error) {
      showAlert(error.message, "danger");
    }
  }

  function bindEvents() {
    els.btnBuscarCliente?.addEventListener("click", buscarClientes);
    els.btnIniciarBalcao?.addEventListener("click", iniciarVendaBalcao);
    els.btnRecarregarPdv?.addEventListener("click", async () => {
      state.clientes = [];
      renderClientes();
      await carregarAtendimentos();
      renderVendaCompleta();
      showAlert("Dados do PDV recarregados.", "info");
    });

    els.btnRecarregarAtendimentos?.addEventListener("click", carregarAtendimentos);
    els.btnAdicionarProduto?.addEventListener("click", adicionarProdutoNaVenda);
    els.btnAtualizarVenda?.addEventListener("click", atualizarVendaAtual);
    els.btnFinalizarVenda?.addEventListener("click", finalizarVendaAtual);
    els.btnCancelarVenda?.addEventListener("click", cancelarVendaAtual);

    els.clienteBusca?.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        buscarClientes();
      }
    });

    els.empresaId?.addEventListener("change", async () => {
      getEmpresaId();
      await carregarAtendimentos();
    });
  }

  function init() {
    getEmpresaId();
    renderContexto();
    renderTotais();
    renderCarrinho();
    renderClientes();
    renderAtendimentos();
    bindEvents();
    carregarAtendimentos();
  }

  init();
})();