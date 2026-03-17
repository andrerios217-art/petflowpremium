let dados = [];

document.addEventListener("DOMContentLoaded", () => {
    const campoCompetencia = document.getElementById("filtro-competencia");
    const hoje = new Date();
    const ano = hoje.getFullYear();
    const mes = String(hoje.getMonth() + 1).padStart(2, "0");
    campoCompetencia.value = `${ano}-${mes}`;

    document.getElementById("btn-carregar").onclick = carregar;
    carregar();
});

async function carregar() {
    const competencia = document.getElementById("filtro-competencia").value;

    const res = await fetch(`/api/comissao/lancamentos?empresa_id=1&competencia=${competencia}`);
    const data = await res.json();

    dados = data.funcionarios || [];
    render();
}

function render() {
    const container = document.getElementById("relatorios-container");
    container.innerHTML = "";

    if (!dados.length) {
        container.innerHTML = `
            <div class="relatorio-empty">
                <h3>Nenhum lançamento encontrado</h3>
                <p>Não há dados de comissão para a competência selecionada.</p>
            </div>
        `;
        return;
    }

    dados.forEach((f) => {
        const card = document.createElement("div");
        card.className = "relatorio-card";

        const statusAtual = String(f.status || "").toUpperCase();

        const badgeStatus = f.fechado
            ? `<span class="relatorio-badge relatorio-badge-fechado">Fechado</span>`
            : `<span class="relatorio-badge relatorio-badge-status">${escapeHtml(f.status || "CAPTURADO")}</span>`;

        let botoes = "";

        if (f.fechado) {
            botoes = `<button class="btn btn-secondary" disabled>Comissão Fechada</button>`;
        } else if (statusAtual === "APROVADO") {
            botoes = `
                <button class="btn btn-success" disabled>Aprovado</button>
                <button onclick="fecharComissao(${f.funcionario_id})" class="btn btn-primary">Fechar Comissão</button>
            `;
        } else {
            botoes = `
                <button onclick="aprovar(${f.funcionario_id})" class="btn btn-success">Aprovar</button>
                <button onclick="rejeitar(${f.funcionario_id})" class="btn btn-danger">Rejeitar</button>
            `;
        }

        const valorPrincipal = f.fechado
            ? formatarMoeda(f.valor_fechado || 0)
            : formatarMoeda(f.valor_estimado || 0);

        card.innerHTML = `
            <div class="relatorio-header-card">
                <div>
                    <div class="relatorio-title-row">
                        <h2>${escapeHtml(f.funcionario_nome || "Funcionário")}</h2>
                        ${badgeStatus}
                    </div>
                    <span class="relatorio-subtitle">Competência: ${escapeHtml(f.competencia || "-")}</span>
                </div>

                <div class="relatorio-total">
                    <strong>${Number(f.pontos_total || 0)} pts</strong>
                    <span>${valorPrincipal}</span>
                </div>
            </div>

            <div class="relatorio-body">
                ${(f.lancamentos || []).map((l) => `
                    <div class="relatorio-item">
                        <div class="relatorio-item-left">
                            <span class="relatorio-etapa">${escapeHtml(l.etapa || "-")}</span>
                            <small>${escapeHtml(l.status || "-")}</small>
                        </div>
                        <strong>${Number(l.pontos || 0)} pts</strong>
                    </div>
                `).join("")}
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
                empresa_id: 1,
                funcionario_id,
                competencia: getCompetencia()
            })
        });

        showToast("Aprovado com sucesso");
        carregar();
    } catch (error) {
        showToast(error.message || "Erro ao aprovar", "error");
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
                empresa_id: 1,
                funcionario_id,
                competencia: getCompetencia(),
                motivo
            })
        });

        showToast("Rejeitado com sucesso");
        carregar();
    } catch (error) {
        showToast(error.message || "Erro ao rejeitar", "error");
    }
}

async function fecharComissao(funcionario_id) {
    try {
        const resultado = await fetchJsonSafe("/api/comissao/fechar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                empresa_id: 1,
                funcionario_id,
                competencia: getCompetencia()
            })
        });

        showToast(`Comissão fechada: ${formatarMoeda(resultado.valor_final || 0)}`);
        carregar();
    } catch (error) {
        showToast(error.message || "Erro ao fechar comissão", "error");
    }
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
    return document.getElementById("filtro-competencia").value;
}

function formatarMoeda(valor) {
    return Number(valor || 0).toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL"
    });
}

function escapeHtml(valor) {
    return String(valor ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function showToast(message, type = "success") {
    if (window.showToast && typeof window.showToast === "function") {
        window.showToast(message, type);
        return;
    }

    console.log(message);
}