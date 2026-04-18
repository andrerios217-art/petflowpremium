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

    garantirModalRejeicao();
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
                <button onclick="abrirModalRejeicao(${Number(funcionario.funcionario_id)}, '${escapeJs(funcionario.funcionario_nome || "Funcionário")}')" class="btn btn-danger">Rejeitar</button>
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

function garantirModalRejeicao() {
    if (document.getElementById("modal-rejeicao-comissao")) {
        return;
    }

    injetarEstilosModalRejeicao();

    const modal = document.createElement("div");
    modal.id = "modal-rejeicao-comissao";
    modal.className = "rejeicao-modal-backdrop hidden";
    modal.innerHTML = `
        <div class="rejeicao-modal-card" role="dialog" aria-modal="true" aria-labelledby="rejeicao-modal-titulo">
            <div class="rejeicao-modal-header">
                <div>
                    <span class="rejeicao-modal-badge">Auditoria de comissão</span>
                    <h3 id="rejeicao-modal-titulo">Rejeitar comissão</h3>
                    <p id="rejeicao-modal-subtitulo">Informe o motivo da rejeição para continuar.</p>
                </div>
                <button type="button" class="rejeicao-modal-close" id="btn-fechar-modal-rejeicao" aria-label="Fechar">✕</button>
            </div>

            <div class="rejeicao-modal-body">
                <label class="rejeicao-modal-field" for="motivo-rejeicao-input">
                    <span>Motivo da rejeição</span>
                    <textarea
                        id="motivo-rejeicao-input"
                        class="rejeicao-modal-textarea"
                        placeholder="Descreva o motivo da rejeição"
                        rows="4"
                    ></textarea>
                </label>
                <div id="motivo-rejeicao-erro" class="rejeicao-modal-erro hidden"></div>
            </div>

            <div class="rejeicao-modal-actions">
                <button type="button" class="btn btn-secondary" id="btn-cancelar-modal-rejeicao">Cancelar</button>
                <button type="button" class="btn btn-danger" id="btn-confirmar-modal-rejeicao">Confirmar rejeição</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    modal.addEventListener("click", (event) => {
        if (event.target === modal) {
            fecharModalRejeicao();
        }
    });

    document.getElementById("btn-fechar-modal-rejeicao")?.addEventListener("click", fecharModalRejeicao);
    document.getElementById("btn-cancelar-modal-rejeicao")?.addEventListener("click", fecharModalRejeicao);
    document.getElementById("btn-confirmar-modal-rejeicao")?.addEventListener("click", confirmarRejeicaoModal);

    document.addEventListener("keydown", (event) => {
        const modalAtivo = document.getElementById("modal-rejeicao-comissao");
        if (!modalAtivo || modalAtivo.classList.contains("hidden")) return;

        if (event.key === "Escape") {
            fecharModalRejeicao();
        }
    });
}

function injetarEstilosModalRejeicao() {
    if (document.getElementById("rejeicao-modal-styles")) {
        return;
    }

    const style = document.createElement("style");
    style.id = "rejeicao-modal-styles";
    style.textContent = `
        .rejeicao-modal-backdrop {
            position: fixed;
            inset: 0;
            background: rgba(15, 23, 42, 0.42);
            backdrop-filter: blur(6px);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            z-index: 9999;
        }

        .rejeicao-modal-backdrop.hidden {
            display: none;
        }

        .rejeicao-modal-card {
            width: 100%;
            max-width: 560px;
            border-radius: 26px;
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid rgba(0, 0, 0, 0.06);
            box-shadow: 0 24px 60px rgba(15, 23, 42, 0.18);
            overflow: hidden;
            animation: rejeicaoModalFadeIn 0.18s ease;
        }

        .rejeicao-modal-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 14px;
            padding: 22px 24px 14px;
            background: linear-gradient(135deg, rgba(35, 50, 74, 0.98), rgba(49, 76, 115, 0.95));
        }

        .rejeicao-modal-header h3 {
            margin: 8px 0 6px;
            color: #ffffff;
            font-size: 1.25rem;
            font-weight: 800;
            letter-spacing: -0.03em;
        }

        .rejeicao-modal-header p {
            margin: 0;
            color: rgba(255, 255, 255, 0.82);
            font-size: 0.92rem;
            line-height: 1.45;
        }

        .rejeicao-modal-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 30px;
            padding: 6px 12px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.14);
            color: #ffffff;
            font-size: 0.74rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }

        .rejeicao-modal-close {
            width: 38px;
            height: 38px;
            border-radius: 12px;
            border: none;
            background: rgba(255, 255, 255, 0.14);
            color: #ffffff;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 800;
        }

        .rejeicao-modal-body {
            padding: 20px 24px 14px;
        }

        .rejeicao-modal-field {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .rejeicao-modal-field span {
            color: #23324a;
            font-size: 0.88rem;
            font-weight: 800;
            letter-spacing: 0.02em;
        }

        .rejeicao-modal-textarea {
            width: 100%;
            min-height: 112px;
            resize: vertical;
            border-radius: 18px;
            border: 1px solid rgba(0, 0, 0, 0.08);
            background: rgba(255, 255, 255, 0.95);
            padding: 14px 16px;
            color: #23324a;
            outline: none;
            box-sizing: border-box;
            font: inherit;
            line-height: 1.5;
        }

        .rejeicao-modal-textarea:focus {
            border-color: rgba(49, 76, 115, 0.32);
            box-shadow: 0 0 0 4px rgba(49, 76, 115, 0.08);
        }

        .rejeicao-modal-erro {
            margin-top: 10px;
            padding: 12px 14px;
            border-radius: 14px;
            background: rgba(220, 38, 38, 0.08);
            border: 1px solid rgba(220, 38, 38, 0.12);
            color: #b91c1c;
            font-size: 0.9rem;
            font-weight: 700;
        }

        .rejeicao-modal-erro.hidden {
            display: none;
        }

        .rejeicao-modal-actions {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            padding: 0 24px 22px;
            flex-wrap: wrap;
        }

        @keyframes rejeicaoModalFadeIn {
            from {
                opacity: 0;
                transform: translateY(8px) scale(0.98);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        @media (max-width: 640px) {
            .rejeicao-modal-card {
                max-width: 100%;
                border-radius: 22px;
            }

            .rejeicao-modal-header,
            .rejeicao-modal-body,
            .rejeicao-modal-actions {
                padding-left: 16px;
                padding-right: 16px;
            }

            .rejeicao-modal-actions .btn {
                width: 100%;
            }
        }
    `;
    document.head.appendChild(style);
}

function abrirModalRejeicao(funcionarioId, funcionarioNome) {
    garantirModalRejeicao();

    const modal = document.getElementById("modal-rejeicao-comissao");
    const input = document.getElementById("motivo-rejeicao-input");
    const subtitulo = document.getElementById("rejeicao-modal-subtitulo");

    if (!modal || !input) return;

    modal.dataset.funcionarioId = String(funcionarioId || "");
    input.value = "";

    if (subtitulo) {
        subtitulo.textContent = `Informe o motivo da rejeição para ${funcionarioNome || "o funcionário selecionado"}.`;
    }

    limparErroModalRejeicao();
    modal.classList.remove("hidden");

    setTimeout(() => {
        input.focus();
    }, 20);
}

function fecharModalRejeicao() {
    const modal = document.getElementById("modal-rejeicao-comissao");
    const input = document.getElementById("motivo-rejeicao-input");

    if (!modal) return;

    modal.classList.add("hidden");
    modal.dataset.funcionarioId = "";

    if (input) {
        input.value = "";
    }

    limparErroModalRejeicao();
}

function mostrarErroModalRejeicao(message) {
    const erro = document.getElementById("motivo-rejeicao-erro");
    if (!erro) return;

    erro.textContent = message;
    erro.classList.remove("hidden");
}

function limparErroModalRejeicao() {
    const erro = document.getElementById("motivo-rejeicao-erro");
    if (!erro) return;

    erro.textContent = "";
    erro.classList.add("hidden");
}

async function confirmarRejeicaoModal() {
    const modal = document.getElementById("modal-rejeicao-comissao");
    const input = document.getElementById("motivo-rejeicao-input");
    const botaoConfirmar = document.getElementById("btn-confirmar-modal-rejeicao");

    if (!modal || !input || !botaoConfirmar) return;

    const funcionario_id = Number(modal.dataset.funcionarioId || 0);
    const motivo = String(input.value || "").trim();

    if (!funcionario_id) {
        mostrarErroModalRejeicao("Funcionário inválido para rejeição.");
        return;
    }

    if (!motivo) {
        mostrarErroModalRejeicao("Informe o motivo da rejeição.");
        input.focus();
        return;
    }

    try {
        limparErroModalRejeicao();
        botaoConfirmar.disabled = true;
        botaoConfirmar.textContent = "Rejeitando...";

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

        fecharModalRejeicao();
        notifyToast("Rejeitado com sucesso", "success");
        await carregar();
    } catch (error) {
        mostrarErroModalRejeicao(error.message || "Erro ao rejeitar.");
    } finally {
        botaoConfirmar.disabled = false;
        botaoConfirmar.textContent = "Confirmar rejeição";
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

    window.location.href = `/relatorios/comissao/demonstrativo/${id}`;
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

function escapeJs(valor) {
    return String(valor ?? "")
        .replaceAll("\\", "\\\\")
        .replaceAll("'", "\\'")
        .replaceAll('"', '\\"')
        .replaceAll("\n", " ")
        .replaceAll("\r", " ");
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
}