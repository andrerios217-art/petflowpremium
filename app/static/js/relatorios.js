const EMPRESA_ID = 1;

document.addEventListener("DOMContentLoaded", () => {
    configurarPeriodoInicial();
    vincularEventosFaturamento();
    vincularEventosRelatorioVendas();
});

function configurarPeriodoInicial() {
    const hoje = new Date();
    const primeiroDia = new Date(hoje.getFullYear(), hoje.getMonth(), 1);

    const faturamentoInicio = document.getElementById("faturamento-data-inicio");
    const faturamentoFim = document.getElementById("faturamento-data-fim");
    const vendasInicio = document.getElementById("relatorio-vendas-data-inicio");
    const vendasFim = document.getElementById("relatorio-vendas-data-fim");

    if (faturamentoInicio) {
        faturamentoInicio.value = formatarDataInput(primeiroDia);
    }

    if (faturamentoFim) {
        faturamentoFim.value = formatarDataInput(hoje);
    }

    if (vendasInicio) {
        vendasInicio.value = formatarDataInput(primeiroDia);
    }

    if (vendasFim) {
        vendasFim.value = formatarDataInput(hoje);
    }
}

function vincularEventosFaturamento() {
    const botao = document.getElementById("btn-carregar-faturamento");
    if (!botao) return;

    botao.addEventListener("click", carregarFaturamentoPeriodo);
}

function vincularEventosRelatorioVendas() {
    const botao = document.getElementById("btn-carregar-relatorio-vendas");
    if (!botao) return;

    botao.addEventListener("click", carregarRelatorioVendas);
}

async function carregarFaturamentoPeriodo() {
    const campoInicio = document.getElementById("faturamento-data-inicio");
    const campoFim = document.getElementById("faturamento-data-fim");
    const botao = document.getElementById("btn-carregar-faturamento");

    const dataInicio = campoInicio ? campoInicio.value : "";
    const dataFim = campoFim ? campoFim.value : "";

    if (!dataInicio || !dataFim) {
        atualizarStatusFaturamento("Informe data inicial e final.");
        renderizarEstadoVazioFaturamento(
            "Período inválido",
            "Preencha a data inicial e a data final para consultar o faturamento."
        );
        notifyToast("Informe o período para consultar o faturamento.", "error");
        return;
    }

    if (dataFim < dataInicio) {
        atualizarStatusFaturamento("Período inválido.");
        renderizarEstadoVazioFaturamento(
            "Período inválido",
            "A data final não pode ser menor que a data inicial."
        );
        notifyToast("A data final não pode ser menor que a data inicial.", "error");
        return;
    }

    try {
        setLoadingFaturamento(true, botao);

        const url = `/api/pdv/relatorios/faturamento-periodo?empresa_id=${EMPRESA_ID}&data_inicio=${encodeURIComponent(dataInicio)}&data_fim=${encodeURIComponent(dataFim)}`;
        const data = await fetchJsonSafe(url);

        preencherResumoFaturamento(data);
        renderizarResultadoFaturamento(data);
        atualizarStatusFaturamento("Dados carregados com sucesso.");
    } catch (error) {
        atualizarResumoFaturamento({
            quantidade_vendas: 0,
            total_faturado: 0,
            ticket_medio: 0
        });

        atualizarStatusFaturamento("Erro ao carregar.");
        renderizarEstadoVazioFaturamento(
            "Erro ao carregar faturamento",
            error.message || "Não foi possível buscar os dados do período."
        );
        notifyToast(error.message || "Erro ao carregar faturamento.", "error");
    } finally {
        setLoadingFaturamento(false, botao);
    }
}

async function carregarRelatorioVendas() {
    const campoInicio = document.getElementById("relatorio-vendas-data-inicio");
    const campoFim = document.getElementById("relatorio-vendas-data-fim");
    const botao = document.getElementById("btn-carregar-relatorio-vendas");

    const dataInicio = campoInicio ? campoInicio.value : "";
    const dataFim = campoFim ? campoFim.value : "";

    if (!dataInicio || !dataFim) {
        atualizarStatusRelatorioVendas("Informe data inicial e final.");
        renderizarEstadoVazioRelatorioVendas(
            "Período inválido",
            "Preencha a data inicial e a data final para consultar o relatório de vendas."
        );
        notifyToast("Informe o período para consultar o relatório de vendas.", "error");
        return;
    }

    if (dataFim < dataInicio) {
        atualizarStatusRelatorioVendas("Período inválido.");
        renderizarEstadoVazioRelatorioVendas(
            "Período inválido",
            "A data final não pode ser menor que a data inicial."
        );
        notifyToast("A data final não pode ser menor que a data inicial.", "error");
        return;
    }

    try {
        setLoadingRelatorioVendas(true, botao);

        const url = `/api/pdv/relatorios/vendas?empresa_id=${EMPRESA_ID}&data_inicio=${encodeURIComponent(dataInicio)}&data_fim=${encodeURIComponent(dataFim)}`;
        const data = await fetchJsonSafe(url);

        preencherResumoRelatorioVendas(data);
        renderizarResultadoRelatorioVendas(data);
        atualizarStatusRelatorioVendas("Dados carregados com sucesso.");
    } catch (error) {
        atualizarResumoRelatorioVendas({
            quantidade_vendas: 0,
            total_faturado: 0,
            ticket_medio: 0,
            total_descontos: 0,
            total_acrescimos: 0
        });

        atualizarStatusRelatorioVendas("Erro ao carregar.");
        renderizarEstadoVazioRelatorioVendas(
            "Erro ao carregar relatório de vendas",
            error.message || "Não foi possível buscar os dados do período."
        );
        notifyToast(error.message || "Erro ao carregar relatório de vendas.", "error");
    } finally {
        setLoadingRelatorioVendas(false, botao);
    }
}

function preencherResumoFaturamento(data) {
    const resumo = data?.resumo || {};

    atualizarResumoFaturamento({
        quantidade_vendas: Number(resumo.quantidade_vendas || 0),
        total_faturado: Number(resumo.total_faturado || 0),
        ticket_medio: Number(resumo.ticket_medio || 0)
    });
}

function preencherResumoRelatorioVendas(data) {
    const resumo = data?.resumo || {};

    atualizarResumoRelatorioVendas({
        quantidade_vendas: Number(resumo.quantidade_vendas || 0),
        total_faturado: Number(resumo.total_faturado || 0),
        ticket_medio: Number(resumo.ticket_medio || 0),
        total_descontos: Number(resumo.total_descontos || 0),
        total_acrescimos: Number(resumo.total_acrescimos || 0)
    });
}

function atualizarResumoFaturamento(resumo) {
    const quantidade = document.getElementById("faturamento-quantidade-vendas");
    const total = document.getElementById("faturamento-total-faturado");
    const ticket = document.getElementById("faturamento-ticket-medio");

    if (quantidade) {
        quantidade.textContent = String(resumo.quantidade_vendas || 0);
    }

    if (total) {
        total.textContent = formatarMoeda(resumo.total_faturado || 0);
    }

    if (ticket) {
        ticket.textContent = formatarMoeda(resumo.ticket_medio || 0);
    }
}

function atualizarResumoRelatorioVendas(resumo) {
    const quantidade = document.getElementById("relatorio-vendas-quantidade-vendas");
    const total = document.getElementById("relatorio-vendas-total-faturado");
    const ticket = document.getElementById("relatorio-vendas-ticket-medio");
    const descontos = document.getElementById("relatorio-vendas-total-descontos");
    const acrescimos = document.getElementById("relatorio-vendas-total-acrescimos");

    if (quantidade) {
        quantidade.textContent = String(resumo.quantidade_vendas || 0);
    }

    if (total) {
        total.textContent = formatarMoeda(resumo.total_faturado || 0);
    }

    if (ticket) {
        ticket.textContent = formatarMoeda(resumo.ticket_medio || 0);
    }

    if (descontos) {
        descontos.textContent = formatarMoeda(resumo.total_descontos || 0);
    }

    if (acrescimos) {
        acrescimos.textContent = formatarMoeda(resumo.total_acrescimos || 0);
    }
}

function atualizarStatusFaturamento(texto) {
    const status = document.getElementById("faturamento-status");
    if (status) {
        status.textContent = texto || "-";
    }
}

function atualizarStatusRelatorioVendas(texto) {
    const status = document.getElementById("relatorio-vendas-status");
    if (status) {
        status.textContent = texto || "-";
    }
}

function renderizarResultadoFaturamento(data) {
    const container = document.getElementById("faturamento-resultado");
    if (!container) return;

    const vendas = Array.isArray(data?.vendas) ? data.vendas : [];
    const porDia = Array.isArray(data?.por_dia) ? data.por_dia : [];

    if (!vendas.length) {
        renderizarEstadoVazioFaturamento(
            "Nenhuma venda encontrada",
            "Não há vendas fechadas no período informado."
        );
        return;
    }

    const cardsDias = porDia.map((item) => `
        <div class="financeiro-info">
            <span class="financeiro-info-label">${escapeHtml(formatarDataBrasil(item.data || "-"))}</span>
            <span class="financeiro-info-value">${formatarMoeda(item.total_faturado || 0)}</span>
            <small>${Number(item.quantidade_vendas || 0)} venda(s)</small>
        </div>
    `).join("");

    const cardsVendas = vendas.map((venda) => `
        <div class="relatorio-card">
            <div class="relatorio-header-card">
                <div>
                    <div class="relatorio-title-row">
                        <h2>${escapeHtml(venda.numero_venda || `Venda #${venda.id || "-"}`)}</h2>
                        <span class="relatorio-badge relatorio-badge-fechado">${escapeHtml(venda.status || "FECHADA")}</span>
                    </div>
                    <span class="relatorio-subtitle">
                        Cliente: ${escapeHtml(obterNomeCliente(venda))}
                    </span>
                </div>

                <div class="relatorio-total">
                    <strong>${formatarMoeda(venda.valor_total || 0)}</strong>
                    <span>${escapeHtml(formatarDataHora(venda.fechada_em))}</span>
                </div>
            </div>

            <div class="relatorio-body">
                <div class="relatorio-item">
                    <div class="relatorio-item-left">
                        <span class="relatorio-etapa">Subtotal</span>
                        <small>Valor bruto da venda</small>
                    </div>
                    <strong>${formatarMoeda(venda.subtotal || 0)}</strong>
                </div>

                <div class="relatorio-item">
                    <div class="relatorio-item-left">
                        <span class="relatorio-etapa">Desconto</span>
                        <small>Descontos aplicados</small>
                    </div>
                    <strong>${formatarMoeda(venda.desconto_valor || 0)}</strong>
                </div>

                <div class="relatorio-item">
                    <div class="relatorio-item-left">
                        <span class="relatorio-etapa">Acréscimo</span>
                        <small>Acréscimos aplicados</small>
                    </div>
                    <strong>${formatarMoeda(venda.acrescimo_valor || 0)}</strong>
                </div>

                <div class="relatorio-item">
                    <div class="relatorio-item-left">
                        <span class="relatorio-etapa">Origem</span>
                        <small>Canal da venda</small>
                    </div>
                    <strong>${escapeHtml(venda.origem || "-")}</strong>
                </div>
            </div>
        </div>
    `).join("");

    container.innerHTML = `
        <div class="financeiro-card">
            <div class="financeiro-card-body">
                ${cardsDias}
            </div>
        </div>

        <div class="relatorios-container">
            ${cardsVendas}
        </div>
    `;
}

function renderizarResultadoRelatorioVendas(data) {
    const container = document.getElementById("relatorio-vendas-resultado");
    if (!container) return;

    const vendas = Array.isArray(data?.vendas) ? data.vendas : [];
    const porOrigem = Array.isArray(data?.por_origem) ? data.por_origem : [];

    if (!vendas.length) {
        renderizarEstadoVazioRelatorioVendas(
            "Nenhuma venda encontrada",
            "Não há vendas fechadas no período informado."
        );
        return;
    }

    const cardsOrigem = porOrigem.map((item) => `
        <div class="financeiro-info">
            <span class="financeiro-info-label">${escapeHtml(item.origem || "NÃO INFORMADA")}</span>
            <span class="financeiro-info-value">${formatarMoeda(item.total_faturado || 0)}</span>
            <small>${Number(item.quantidade_vendas || 0)} venda(s)</small>
        </div>
    `).join("");

    const cardsVendas = vendas.map((venda) => {
        const itens = Array.isArray(venda.itens) ? venda.itens : [];
        const pagamentos = Array.isArray(venda.pagamentos) ? venda.pagamentos : [];

        const itensHtml = itens.length
            ? itens.map((item) => `
                <div class="relatorio-item">
                    <div class="relatorio-item-left">
                        <span class="relatorio-etapa">${escapeHtml(item.descricao_snapshot || "Item")}</span>
                        <small>${escapeHtml(item.tipo_item || "-")} • ${Number(item.quantidade || 0)} un.</small>
                    </div>
                    <strong>${formatarMoeda(item.valor_total || 0)}</strong>
                </div>
            `).join("")
            : `
                <div class="relatorio-item">
                    <div class="relatorio-item-left">
                        <span class="relatorio-etapa">Itens</span>
                        <small>Nenhum item encontrado</small>
                    </div>
                    <strong>-</strong>
                </div>
            `;

        const pagamentosHtml = pagamentos.length
            ? pagamentos.map((pagamento) => `
                <div class="relatorio-item">
                    <div class="relatorio-item-left">
                        <span class="relatorio-etapa">${escapeHtml(pagamento.forma_pagamento || "Pagamento")}</span>
                        <small>${escapeHtml(pagamento.status || "-")}</small>
                    </div>
                    <strong>${formatarMoeda(pagamento.valor || 0)}</strong>
                </div>
            `).join("")
            : `
                <div class="relatorio-item">
                    <div class="relatorio-item-left">
                        <span class="relatorio-etapa">Pagamentos</span>
                        <small>Nenhum pagamento encontrado</small>
                    </div>
                    <strong>-</strong>
                </div>
            `;

        return `
            <div class="relatorio-card">
                <div class="relatorio-header-card">
                    <div>
                        <div class="relatorio-title-row">
                            <h2>${escapeHtml(venda.numero_venda || `Venda #${venda.id || "-"}`)}</h2>
                            <span class="relatorio-badge relatorio-badge-fechado">${escapeHtml(venda.status || "FECHADA")}</span>
                        </div>
                        <span class="relatorio-subtitle">
                            Cliente: ${escapeHtml(obterNomeCliente(venda))} • Origem: ${escapeHtml(venda.origem || "-")}
                        </span>
                    </div>

                    <div class="relatorio-total">
                        <strong>${formatarMoeda(venda.valor_total || 0)}</strong>
                        <span>${escapeHtml(formatarDataHora(venda.fechada_em))}</span>
                    </div>
                </div>

                <div class="relatorio-body">
                    <div class="relatorio-item">
                        <div class="relatorio-item-left">
                            <span class="relatorio-etapa">Resumo financeiro</span>
                            <small>Subtotal / desconto / acréscimo</small>
                        </div>
                        <strong>${formatarMoeda(venda.subtotal || 0)} / ${formatarMoeda(venda.desconto_valor || 0)} / ${formatarMoeda(venda.acrescimo_valor || 0)}</strong>
                    </div>

                    ${itensHtml}
                    ${pagamentosHtml}
                </div>
            </div>
        `;
    }).join("");

    container.innerHTML = `
        <div class="financeiro-card">
            <div class="financeiro-card-body">
                ${cardsOrigem}
            </div>
        </div>

        <div class="relatorios-container">
            ${cardsVendas}
        </div>
    `;
}

function renderizarEstadoVazioFaturamento(titulo, mensagem) {
    const container = document.getElementById("faturamento-resultado");
    if (!container) return;

    container.innerHTML = `
        <div class="relatorio-empty">
            <h3>${escapeHtml(titulo)}</h3>
            <p>${escapeHtml(mensagem)}</p>
        </div>
    `;
}

function renderizarEstadoVazioRelatorioVendas(titulo, mensagem) {
    const container = document.getElementById("relatorio-vendas-resultado");
    if (!container) return;

    container.innerHTML = `
        <div class="relatorio-empty">
            <h3>${escapeHtml(titulo)}</h3>
            <p>${escapeHtml(mensagem)}</p>
        </div>
    `;
}

function obterNomeCliente(venda) {
    return (
        venda?.cliente?.nome ||
        venda?.nome_cliente_snapshot ||
        "Cliente não informado"
    );
}

function setLoadingFaturamento(isLoading, botao = null) {
    const alvo = botao || document.getElementById("btn-carregar-faturamento");
    if (!alvo) return;

    alvo.disabled = isLoading;
    alvo.textContent = isLoading ? "Carregando..." : "Carregar Faturamento";
}

function setLoadingRelatorioVendas(isLoading, botao = null) {
    const alvo = botao || document.getElementById("btn-carregar-relatorio-vendas");
    if (!alvo) return;

    alvo.disabled = isLoading;
    alvo.textContent = isLoading ? "Carregando..." : "Carregar Relatório de Vendas";
}

async function fetchJsonSafe(url, options = {}) {
    const response = await fetch(url, options);
    const raw = await response.text();

    let data = {};
    try {
        data = raw ? JSON.parse(raw) : {};
    } catch (error) {
        if (!response.ok) {
            throw new Error(raw || "Erro na requisição.");
        }
        return {};
    }

    if (!response.ok) {
        throw new Error(data.detail || data.message || "Erro na requisição.");
    }

    if (data?.erro) {
        throw new Error(data.erro);
    }

    return data;
}

function formatarMoeda(valor) {
    return Number(valor || 0).toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL"
    });
}

function formatarDataInput(data) {
    const ano = data.getFullYear();
    const mes = String(data.getMonth() + 1).padStart(2, "0");
    const dia = String(data.getDate()).padStart(2, "0");
    return `${ano}-${mes}-${dia}`;
}

function formatarDataBrasil(dataIso) {
    if (!dataIso) return "-";

    const partes = String(dataIso).split("-");
    if (partes.length !== 3) return dataIso;

    return `${partes[2]}/${partes[1]}/${partes[0]}`;
}

function formatarDataHora(valor) {
    if (!valor) return "-";

    const data = new Date(valor);
    if (Number.isNaN(data.getTime())) return String(valor);

    return data.toLocaleString("pt-BR");
}

function escapeHtml(valor) {
    return String(valor ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function notifyToast(message, type = "success") {
    const externalToast =
        typeof window !== "undefined" &&
        typeof window.showToast === "function" &&
        window.showToast !== notifyToast
            ? window.showToast
            : null;

    if (externalToast) {
        externalToast(message, type);
        return;
    }

    console.log(`[${type}] ${message}`);
    alert(message);
}