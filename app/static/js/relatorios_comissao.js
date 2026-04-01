let dados = [];
const EMPRESA_ID = 1;

document.addEventListener("DOMContentLoaded", () => {
    const campoCompetencia = document.getElementById("filtro-competencia");
    const hoje = new Date();
    const ano = hoje.getFullYear();
    const mes = String(hoje.getMonth() + 1).padStart(2, "0");

    if (campoCompetencia && !campoCompetencia.value) {
        campoCompetencia.value = `${ano}-${mes}`;
    }

    const botaoCarregar = document.getElementById("btn-carregar");
    if (botaoCarregar) {
        botaoCarregar.onclick = carregar;
    }

    carregar();
});

async function carregar() {
    const competencia = getCompetencia();
    const container = document.getElementById("relatorios-container");
    const botaoCarregar = document.getElementById("btn-carregar");

    if (!container) return;

    if (!competencia) {
        container.innerHTML = `
            <div class="relatorio-empty">
                <h3>Competência não informada</h3>
                <p>Selecione o mês da competência para carregar os lançamentos.</p>
            </div>
        `;
        return;
    }

    try {
        setLoadingState(true);

        const url = `/api/comissao/lancamentos?empresa_id=${EMPRESA_ID}&competencia=${encodeURIComponent(competencia)}`;
        console.log("[COMISSAO] Carregando:", url);

        container.innerHTML = `
            <div class="relatorio-empty">
                <h3>Carregando</h3>
                <p>Buscando lançamentos da competência selecionada...</p>
            </div>
        `;

        const data = await fetchJsonSafe(url);
        console.log("[COMISSAO] Resposta da API:", data);

        dados = Array.isArray(data.funcionarios) ? data.funcionarios : [];
        render();
    } catch (error) {
        console.error("[COMISSAO] Erro ao carregar:", error);

        container.innerHTML = `
            <div class="relatorio-empty">
                <h3>Erro ao carregar relatórios</h3>
                <p>${escapeHtml(error.message || "Não foi possível buscar os lançamentos de comissão.")}</p>
            </div>
        `;

        notifyToast(error.message || "Erro ao carregar relatórios", "error");
    } finally {
        if (botaoCarregar) {
            setLoadingState(false);
        }
    }
}

function render() {
    const container = document.getElementById("relatorios-container");
    if (!container) return;

    container.innerHTML = "";

    if (!dados.length) {
        container.innerHTML = `
            <div class="relatorio-empty">
                <h3>Nenhum lançamento encontrado</h3>
                <p>Não há dados de comissão para a competência selecionada na empresa ${EMPRESA_ID}.</p>
            </div>
        `;
        return;
    }

    dados.forEach((funcionario) => {
        const card = document.createElement("div");
        card.className = "relatorio-card";

        const statusAtual = String(funcionario.status || "").toUpperCase();

        const badgeStatus = funcionario.fechado
            ? `<span class="relatorio-badge relatorio-badge-fechado">Fechado</span>`
            : `<span class="relatorio-badge relatorio-badge-status">${escapeHtml(funcionario.status || "CAPTURADO")}</span>`;

        let botoes = "";

        if (funcionario.fechado) {
            botoes = `
                <button onclick="verDemonstrativo(${Number(funcionario.fechamento_id || 0)})" class="btn btn-primary">
                    Ver Demonstrativo
                </button>
            `;
        } else if (statusAtual === "APROVADO") {
            botoes = `
                <button class="btn btn-success" disabled>Aprovado</button>
                <button onclick="fecharComissao(${Number(funcionario.funcionario_id)})" class="btn btn-primary">Fechar Comissão</button>
            `;
        } else {
            botoes = `
                <button onclick="aprovar(${Number(funcionario.funcionario_id)})" class="btn btn-success">Aprovar</button>
                <button onclick="rejeitar(${Number(funcionario.funcionario_id)})" class="btn btn-danger">Rejeitar</button>
            `;
        }

        const valorPrincipal = funcionario.fechado
            ? formatarMoeda(funcionario.valor_fechado || 0)
            : formatarMoeda(funcionario.valor_estimado || 0);

        const pontosPrincipal = funcionario.fechado
            ? Number(funcionario.pontos_fechados ?? funcionario.pontos_total ?? 0)
            : Number(funcionario.pontos_total || 0);

        const lancamentosHtml = Array.isArray(funcionario.lancamentos) && funcionario.lancamentos.length
            ? funcionario.lancamentos.map((lancamento) => `
                <div class="relatorio-item">
                    <div class="relatorio-item-left">
                        <span class="relatorio-etapa">${escapeHtml(lancamento.etapa || "-")}</span>
                        <small>${escapeHtml(lancamento.status || "-")}</small>
                    </div>
                    <strong>${Number(lancamento.pontos || 0)} pts</strong>
                </div>
            `).join("")
            : `
                <div class="relatorio-empty">
                    <p>Sem lançamentos detalhados para este funcionário.</p>
                </div>
            `;

        card.innerHTML = `
            <div class="relatorio-header-card">
                <div>
                    <div class="relatorio-title-row">
                        <h2>${escapeHtml(funcionario.funcionario_nome || "Funcionário")}</h2>
                        ${badgeStatus}
                    </div>
                    <span class="relatorio-subtitle">Competência: ${escapeHtml(formatarCompetencia(funcionario.competencia || "-"))}</span>
                </div>

                <div class="relatorio-total">
                    <strong>${pontosPrincipal} pts</strong>
                    <span>${valorPrincipal}</span>
                </div>
            </div>

            <div class="relatorio-body">
                ${lancamentosHtml}
            </div>

            <div class="relatorio-actions">
                ${botoes}
            </div>
        `;

        container.appendChild(card);
    });
}

async function aprovar(funcionario_id) {
    try {
        await fetchJsonSafe("/api/comissao/aprovar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                empresa_id: EMPRESA_ID,
                funcionario_id,
                competencia: getCompetencia()
            })
        });

        notifyToast("Aprovado com sucesso", "success");
        await carregar();
    } catch (error) {
        notifyToast(error.message || "Erro ao aprovar", "error");
    }
}

async function rejeitar(funcionario_id) {
    const motivo = prompt("Motivo da rejeição:");

    if (!motivo) return;

    try {
        await fetchJsonSafe("/api/comissao/rejeitar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                empresa_id: EMPRESA_ID,
                funcionario_id,
                competencia: getCompetencia(),
                motivo
            })
        });

        notifyToast("Rejeitado com sucesso", "success");
        await carregar();
    } catch (error) {
        notifyToast(error.message || "Erro ao rejeitar", "error");
    }
}

async function fecharComissao(funcionario_id) {
    try {
        const resultado = await fetchJsonSafe("/api/comissao/fechar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                empresa_id: EMPRESA_ID,
                funcionario_id,
                competencia: getCompetencia()
            })
        });

        notifyToast(`Comissão fechada: ${formatarMoeda(resultado.valor_final || 0)}`, "success");
        await carregar();

        if (resultado.fechamento_id) {
            setTimeout(() => {
                verDemonstrativo(resultado.fechamento_id);
            }, 300);
        }
    } catch (error) {
        notifyToast(error.message || "Erro ao fechar comissão", "error");
    }
}

function verDemonstrativo(fechamentoId) {
    const id = Number(fechamentoId || 0);

    if (!id) {
        notifyToast("Demonstrativo indisponível para este fechamento.", "error");
        return;
    }

    window.open(`/relatorios/comissao/demonstrativo/${id}`, "_blank");
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

function getCompetencia() {
    const campo = document.getElementById("filtro-competencia");
    return campo ? campo.value : "";
}

function setLoadingState(isLoading) {
    const botaoCarregar = document.getElementById("btn-carregar");

    if (!botaoCarregar) return;

    botaoCarregar.disabled = isLoading;
    botaoCarregar.textContent = isLoading ? "Carregando..." : "Carregar";
}

function formatarMoeda(valor) {
    return Number(valor || 0).toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL"
    });
}

function formatarCompetencia(valor) {
    if (!valor) return "-";

    const texto = String(valor);

    if (/^\d{4}-\d{2}-\d{2}$/.test(texto)) {
        return texto.slice(0, 7);
    }

    if (/^\d{4}-\d{2}$/.test(texto)) {
        return texto;
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