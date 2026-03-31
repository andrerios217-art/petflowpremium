const FINANCEIRO_EMPRESA_ID = 1;

let financeiroContas = [];
let financeiroModo = "receber"; // receber | pagar

document.addEventListener("DOMContentLoaded", () => {
    const btnNovaConta = document.getElementById("btn-nova-conta");
    const btnCancelarConta = document.getElementById("btn-cancelar-conta");
    const btnSalvarConta = document.getElementById("btn-salvar-conta");
    const btnRecarregar = document.getElementById("btn-recarregar-financeiro");

    const btnTabReceber = document.getElementById("btn-tab-receber");
    const btnTabPagar = document.getElementById("btn-tab-pagar");

    if (btnNovaConta) {
        btnNovaConta.onclick = abrirFormularioConta;
    }

    if (btnCancelarConta) {
        btnCancelarConta.onclick = fecharFormularioConta;
    }

    if (btnSalvarConta) {
        btnSalvarConta.onclick = salvarConta;
    }

    if (btnRecarregar) {
        btnRecarregar.onclick = carregarFinanceiro;
    }

    if (btnTabReceber) {
        btnTabReceber.onclick = () => {
            financeiroModo = "receber";
            atualizarAbasFinanceiro();
            atualizarRotulosFormulario();
            fecharFormularioConta();
            carregarFinanceiro();
        };
    }

    if (btnTabPagar) {
        btnTabPagar.onclick = () => {
            financeiroModo = "pagar";
            atualizarAbasFinanceiro();
            atualizarRotulosFormulario();
            fecharFormularioConta();
            carregarFinanceiro();
        };
    }

    definirVencimentoPadrao();
    atualizarAbasFinanceiro();
    atualizarRotulosFormulario();
    carregarFinanceiro();
});

async function carregarFinanceiro() {
    try {
        const endpointContas =
            financeiroModo === "receber"
                ? `/api/financeiro/receber?empresa_id=${FINANCEIRO_EMPRESA_ID}`
                : `/api/financeiro/pagar/?empresa_id=${FINANCEIRO_EMPRESA_ID}`;

        const [contasData, dashboardData] = await Promise.all([
            fetchJsonSafe(endpointContas),
            fetchJsonSafe(`/api/financeiro/dashboard/?empresa_id=${FINANCEIRO_EMPRESA_ID}`)
        ]);

        financeiroContas = Array.isArray(contasData.contas) ? contasData.contas : [];

        preencherResumo(contasData.resumo || {});
        preencherDashboardPremium(dashboardData || {});
        renderizarGrafico7Dias(dashboardData.grafico_7_dias || []);
        renderizarContas();
    } catch (error) {
        console.error("[FINANCEIRO] Erro ao carregar:", error);
        notifyToast(error.message || "Erro ao carregar financeiro.", "error");

        const container = document.getElementById("financeiro-contas");
        if (container) {
            container.innerHTML = `
                <div class="financeiro-empty">
                    <h3>Erro ao carregar contas</h3>
                    <p>${escapeHtml(error.message || "Não foi possível carregar o financeiro.")}</p>
                </div>
            `;
        }
    }
}

function preencherDashboardPremium(data) {
    const entradasHoje = Number(data.entradas_hoje ?? data.caixa_hoje ?? 0);
    const saidasHoje = Number(data.saidas_hoje ?? 0);
    const lucroHoje = Number(data.lucro_hoje ?? (entradasHoje - saidasHoje));

    const receitaMes = Number(data.receita_mes ?? 0);
    const despesaMes = Number(data.despesa_mes ?? 0);
    const lucroMes = Number(data.lucro_mes ?? (receitaMes - despesaMes));

    setText("financeiro-entradas-hoje", formatarMoeda(entradasHoje));
    setText("financeiro-saidas-hoje", formatarMoeda(saidasHoje));
    setText("financeiro-lucro-hoje", formatarMoeda(lucroHoje));
    setText("financeiro-lucro-mes", formatarMoeda(lucroMes));

    setText("financeiro-dre-receita", formatarMoeda(receitaMes));
    setText("financeiro-dre-despesa", formatarMoeda(despesaMes));
    setText("financeiro-dre-lucro", formatarMoeda(lucroMes));

    setText("financeiro-dre-receita-resumo", formatarMoeda(receitaMes));
    setText("financeiro-dre-despesa-resumo", formatarMoeda(despesaMes));

    aplicarCorLucro("financeiro-lucro-hoje", lucroHoje);
    aplicarCorLucro("financeiro-lucro-mes", lucroMes);
    aplicarCorLucro("financeiro-dre-lucro", lucroMes);
}

function aplicarCorLucro(id, valor) {
    const el = document.getElementById(id);
    if (!el) return;

    el.classList.remove("valor-positivo", "valor-negativo");

    if (Number(valor || 0) >= 0) {
        el.classList.add("valor-positivo");
    } else {
        el.classList.add("valor-negativo");
    }
}

function renderizarGrafico7Dias(dados) {
    const container = document.getElementById("financeiro-chart-bars");
    const empty = document.getElementById("financeiro-chart-empty");

    if (!container || !empty) {
        return;
    }

    container.innerHTML = "";

    const lista = Array.isArray(dados) ? dados : [];

    const maximo = lista.reduce((acc, item) => {
        const entrada = Number(item.entrada ?? item.valor ?? 0);
        const saida = Number(item.saida ?? 0);
        return Math.max(acc, entrada, saida);
    }, 0);

    if (!lista.length || maximo === 0) {
        empty.style.display = "flex";
        container.style.display = "none";
        return;
    }

    empty.style.display = "none";
    container.style.display = "grid";

    lista.forEach((item) => {
        const entrada = Number(item.entrada ?? item.valor ?? 0);
        const saida = Number(item.saida ?? 0);

        const alturaEntrada = maximo > 0 ? Math.max((entrada / maximo) * 180, entrada > 0 ? 18 : 0) : 0;
        const alturaSaida = maximo > 0 ? Math.max((saida / maximo) * 180, saida > 0 ? 18 : 0) : 0;

        const coluna = document.createElement("div");
        coluna.className = "financeiro-chart-col";

        coluna.innerHTML = `
            <div class="financeiro-chart-bar-wrap financeiro-chart-bar-wrap-dual">
                <div class="financeiro-chart-value-group">
                    <div class="financeiro-chart-value financeiro-chart-value-entrada">
                        E: ${formatarMoeda(entrada)}
                    </div>
                    <div class="financeiro-chart-value financeiro-chart-value-saida">
                        S: ${formatarMoeda(saida)}
                    </div>
                </div>

                <div class="financeiro-chart-bars-dual">
                    <div class="financeiro-chart-bar financeiro-chart-bar-entrada" style="height: ${alturaEntrada}px;"></div>
                    <div class="financeiro-chart-bar financeiro-chart-bar-saida" style="height: ${alturaSaida}px;"></div>
                </div>
            </div>
            <div class="financeiro-chart-label">${formatarDataCurta(item.data)}</div>
        `;

        container.appendChild(coluna);
    });
}

function preencherResumo(resumo) {
    setText("financeiro-total-pendente", formatarMoeda(resumo.total_pendente || 0));
    setText("financeiro-total-pago", formatarMoeda(resumo.total_pago || 0));
    setText("financeiro-total-vencido", formatarMoeda(resumo.total_vencido || 0));

    setText(
        "financeiro-qtd-pendente",
        `${Number(resumo.quantidade_pendente || 0)} conta(s)`
    );
    setText(
        "financeiro-qtd-pago",
        `${Number(resumo.quantidade_paga || 0)} conta(s)`
    );
    setText(
        "financeiro-qtd-vencido",
        `${Number(resumo.quantidade_vencida || 0)} conta(s)`
    );
}

function renderizarContas() {
    const container = document.getElementById("financeiro-contas");
    if (!container) return;

    container.innerHTML = "";

    if (!financeiroContas.length) {
        container.innerHTML = `
            <div class="financeiro-empty">
                <h3>Nenhuma conta encontrada</h3>
                <p>${
                    financeiroModo === "receber"
                        ? "Cadastre a primeira conta a receber para começar o controle financeiro."
                        : "Cadastre a primeira conta a pagar para começar o controle financeiro."
                }</p>
            </div>
        `;
        return;
    }

    financeiroContas.forEach((conta) => {
        const card = document.createElement("div");
        card.className = "financeiro-card";

        const statusAtual = String(conta.status_atual || conta.status || "PENDENTE").toUpperCase();
        const statusClass = obterClasseStatus(statusAtual);

        let subtitulo = "";
        if (financeiroModo === "receber") {
            subtitulo = `Cliente: ${escapeHtml(
                conta.cliente_nome || (conta.cliente_id ? "ID " + conta.cliente_id : "Não informado")
            )}`;
        } else {
            subtitulo = `Fornecedor: ${escapeHtml(conta.fornecedor || "Não informado")}`;
        }

        let acoes = `
            <button class="btn btn-success" onclick="baixarConta(${Number(conta.id)})">
                ${financeiroModo === "receber" ? "Baixar Recebimento" : "Baixar Pagamento"}
            </button>
        `;

        if (statusAtual === "PAGO") {
            acoes = `<button class="btn btn-secondary" disabled>Conta Paga</button>`;
        }

        if (statusAtual === "CANCELADO") {
            acoes = `<button class="btn btn-secondary" disabled>Conta Cancelada</button>`;
        }

        card.innerHTML = `
            <div class="financeiro-card-header">
                <div class="financeiro-card-title-wrap">
                    <h3 class="financeiro-card-title">${escapeHtml(conta.descricao || (financeiroModo === "receber" ? "Conta a receber" : "Conta a pagar"))}</h3>
                    <span class="financeiro-card-subtitle">${subtitulo}</span>
                </div>

                <div class="financeiro-card-aside">
                    <span class="financeiro-status ${statusClass}">${escapeHtml(statusAtual)}</span>

                    <div class="financeiro-mini-total">
                        <span>Valor</span>
                        <strong>${formatarMoeda(conta.valor || 0)}</strong>
                    </div>
                </div>
            </div>

            <div class="financeiro-card-body">
                <div class="financeiro-info">
                    <span class="financeiro-info-label">Vencimento</span>
                    <span class="financeiro-info-value">${escapeHtml(formatarData(conta.vencimento))}</span>
                </div>

                <div class="financeiro-info">
                    <span class="financeiro-info-label">${financeiroModo === "receber" ? "Valor Recebido" : "Valor Pago"}</span>
                    <span class="financeiro-info-value">${formatarMoeda(conta.valor_pago || 0)}</span>
                </div>

                <div class="financeiro-info">
                    <span class="financeiro-info-label">${financeiroModo === "receber" ? "Recebimento" : "Pagamento"}</span>
                    <span class="financeiro-info-value">${escapeHtml(conta.data_pagamento ? formatarData(conta.data_pagamento) : "Sem baixa")}</span>
                </div>

                <div class="financeiro-info">
                    <span class="financeiro-info-label">Observação</span>
                    <span class="financeiro-info-value">${escapeHtml(conta.observacao || "Sem observação")}</span>
                </div>
            </div>

            <div class="financeiro-card-actions">
                ${acoes}
            </div>
        `;

        container.appendChild(card);
    });
}

async function salvarConta() {
    const descricao = getValue("financeiro-descricao");
    const valor = getValue("financeiro-valor");
    const vencimento = getValue("financeiro-vencimento");
    const observacao = getValue("financeiro-observacao");

    const clienteIdRaw = getValue("financeiro-cliente-id");
    const fornecedor = getValue("financeiro-fornecedor");

    if (!descricao || descricao.trim().length < 2) {
        notifyToast("Informe uma descrição válida.", "error");
        return;
    }

    if (!valor || Number(valor) <= 0) {
        notifyToast("Informe um valor maior que zero.", "error");
        return;
    }

    if (!vencimento) {
        notifyToast("Informe a data de vencimento.", "error");
        return;
    }

    const endpoint =
        financeiroModo === "receber"
            ? "/api/financeiro/receber"
            : "/api/financeiro/pagar/";

    const payload =
        financeiroModo === "receber"
            ? {
                empresa_id: FINANCEIRO_EMPRESA_ID,
                cliente_id: clienteIdRaw ? Number(clienteIdRaw) : null,
                origem_tipo: null,
                origem_id: null,
                descricao: descricao.trim(),
                observacao: observacao ? observacao.trim() : null,
                valor: Number(valor),
                vencimento: vencimento
            }
            : {
                empresa_id: FINANCEIRO_EMPRESA_ID,
                descricao: descricao.trim(),
                fornecedor: fornecedor ? fornecedor.trim() : null,
                observacao: observacao ? observacao.trim() : null,
                valor: Number(valor),
                vencimento: vencimento
            };

    try {
        await fetchJsonSafe(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        notifyToast(
            financeiroModo === "receber"
                ? "Conta a receber criada com sucesso."
                : "Conta a pagar criada com sucesso.",
            "success"
        );

        limparFormularioConta();
        fecharFormularioConta();
        await carregarFinanceiro();
    } catch (error) {
        notifyToast(error.message || "Erro ao salvar conta.", "error");
    }
}

async function baixarConta(contaId) {
    const confirmar = window.confirm(
        financeiroModo === "receber"
            ? "Confirma a baixa deste recebimento?"
            : "Confirma a baixa deste pagamento?"
    );

    if (!confirmar) return;

    try {
        const endpoint =
            financeiroModo === "receber"
                ? `/api/financeiro/receber/${contaId}/baixar`
                : `/api/financeiro/pagar/${contaId}/baixar`;

        await fetchJsonSafe(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({})
        });

        notifyToast(
            financeiroModo === "receber"
                ? "Recebimento baixado com sucesso."
                : "Pagamento baixado com sucesso.",
            "success"
        );

        await carregarFinanceiro();
    } catch (error) {
        notifyToast(error.message || "Erro ao baixar conta.", "error");
    }
}

function abrirFormularioConta() {
    const card = document.getElementById("financeiro-form-card");
    if (card) {
        card.style.display = "block";
    }
}

function fecharFormularioConta() {
    const card = document.getElementById("financeiro-form-card");
    if (card) {
        card.style.display = "none";
    }
}

function limparFormularioConta() {
    setValue("financeiro-cliente-id", "");
    setValue("financeiro-fornecedor", "");
    setValue("financeiro-descricao", "");
    setValue("financeiro-valor", "");
    setValue("financeiro-observacao", "");
    definirVencimentoPadrao();
}

function definirVencimentoPadrao() {
    const input = document.getElementById("financeiro-vencimento");
    if (!input) return;

    const hoje = new Date();
    const ano = hoje.getFullYear();
    const mes = String(hoje.getMonth() + 1).padStart(2, "0");
    const dia = String(hoje.getDate()).padStart(2, "0");
    input.value = `${ano}-${mes}-${dia}`;
}

function atualizarAbasFinanceiro() {
    const btnReceber = document.getElementById("btn-tab-receber");
    const btnPagar = document.getElementById("btn-tab-pagar");

    if (btnReceber) {
        btnReceber.classList.toggle("is-active", financeiroModo === "receber");
    }

    if (btnPagar) {
        btnPagar.classList.toggle("is-active", financeiroModo === "pagar");
    }
}

function atualizarRotulosFormulario() {
    const tituloSecao = document.getElementById("financeiro-titulo-form");
    const badgeSecao = document.getElementById("financeiro-badge-form");
    const tituloLista = document.getElementById("financeiro-titulo-lista");
    const badgeLista = document.getElementById("financeiro-badge-lista");
    const labelCliente = document.getElementById("financeiro-label-cliente-id");
    const fieldCliente = document.getElementById("financeiro-field-cliente-id");
    const fieldFornecedor = document.getElementById("financeiro-field-fornecedor");
    const btnSalvar = document.getElementById("btn-salvar-conta");

    if (tituloSecao) {
        tituloSecao.textContent =
            financeiroModo === "receber" ? "Nova Conta a Receber" : "Nova Conta a Pagar";
    }

    if (badgeSecao) {
        badgeSecao.textContent =
            financeiroModo === "receber" ? "Recebimento" : "Pagamento";
    }

    if (tituloLista) {
        tituloLista.textContent =
            financeiroModo === "receber" ? "Contas a Receber" : "Contas a Pagar";
    }

    if (badgeLista) {
        badgeLista.textContent = "Operacional";
    }

    if (labelCliente) {
        labelCliente.textContent = "Cliente ID";
    }

    if (fieldCliente) {
        fieldCliente.style.display = financeiroModo === "receber" ? "flex" : "none";
    }

    if (fieldFornecedor) {
        fieldFornecedor.style.display = financeiroModo === "pagar" ? "flex" : "none";
    }

    if (btnSalvar) {
        btnSalvar.textContent =
            financeiroModo === "receber" ? "Salvar Conta a Receber" : "Salvar Conta a Pagar";
    }
}

function obterClasseStatus(status) {
    if (status === "PAGO") {
        return "financeiro-status-pago";
    }

    if (status === "VENCIDO") {
        return "financeiro-status-vencido";
    }

    if (status === "CANCELADO") {
        return "financeiro-status-cancelado";
    }

    return "financeiro-status-pendente";
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

    return data;
}

function formatarMoeda(valor) {
    return Number(valor || 0).toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL"
    });
}

function formatarData(valor) {
    if (!valor) return "-";

    const texto = String(valor);

    if (/^\d{4}-\d{2}-\d{2}$/.test(texto)) {
        const [ano, mes, dia] = texto.split("-");
        return `${dia}/${mes}/${ano}`;
    }

    return texto;
}

function formatarDataCurta(valor) {
    if (!valor) return "-";

    const texto = String(valor);

    if (/^\d{4}-\d{2}-\d{2}$/.test(texto)) {
        const [, mes, dia] = texto.split("-");
        return `${dia}/${mes}`;
    }

    return texto;
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

function getValue(id) {
    const el = document.getElementById(id);
    return el ? el.value : "";
}

function setValue(id, value) {
    const el = document.getElementById(id);
    if (el) {
        el.value = value;
    }
}

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = value;
    }
}