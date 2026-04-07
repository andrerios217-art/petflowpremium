const FINANCEIRO_EMPRESA_ID = 1;

let financeiroContas = [];
let financeiroModo = "receber"; // receber | pagar
let financeiroCompetencia = obterCompetenciaAtual();
let financeiroPlanoDre = [];
let financeiroWizardStep = 1;

document.addEventListener("DOMContentLoaded", () => {
    const btnNovaConta = document.getElementById("btn-nova-conta");
    const btnCancelarConta = document.getElementById("btn-cancelar-conta");
    const btnSalvarConta = document.getElementById("btn-salvar-conta");
    const btnRecarregar = document.getElementById("btn-recarregar-financeiro");

    const btnTabReceber = document.getElementById("btn-tab-receber");
    const btnTabPagar = document.getElementById("btn-tab-pagar");

    const btnAplicarCompetencia = document.getElementById("btn-aplicar-competencia-financeiro");
    const btnMesAtual = document.getElementById("btn-mes-atual-financeiro");

    const btnFecharModal = document.getElementById("btn-fechar-modal-financeiro");
    const btnVoltarStep = document.getElementById("btn-voltar-step-financeiro");
    const btnAvancarStep = document.getElementById("btn-avancar-step-financeiro");
    const modalOverlay = document.getElementById("financeiro-modal-overlay");

    const selectGrupoDre = document.getElementById("financeiro-grupo-dre");
    const selectCategoriaDre = document.getElementById("financeiro-categoria-dre");

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
        btnTabPagar.onclick = async () => {
            financeiroModo = "pagar";
            atualizarAbasFinanceiro();
            atualizarRotulosFormulario();
            fecharFormularioConta();
            await carregarPlanoDre();
            carregarFinanceiro();
        };
    }

    if (btnAplicarCompetencia) {
        btnAplicarCompetencia.onclick = () => {
            if (!atualizarCompetenciaDosCampos()) {
                return;
            }

            carregarFinanceiro();
        };
    }

    if (btnMesAtual) {
        btnMesAtual.onclick = () => {
            financeiroCompetencia = obterCompetenciaAtual();
            preencherCamposCompetencia();
            atualizarLabelCompetencia();
            carregarFinanceiro();
        };
    }

    if (btnFecharModal) {
        btnFecharModal.onclick = fecharFormularioConta;
    }

    if (btnVoltarStep) {
        btnVoltarStep.onclick = voltarStepFinanceiro;
    }

    if (btnAvancarStep) {
        btnAvancarStep.onclick = avancarStepFinanceiro;
    }

    if (modalOverlay) {
        modalOverlay.addEventListener("click", (event) => {
            const target = event.target;
            if (target && target.dataset && target.dataset.closeFinanceiroModal === "true") {
                fecharFormularioConta();
            }
        });
    }

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            const overlay = document.getElementById("financeiro-modal-overlay");
            if (overlay && overlay.style.display !== "none") {
                fecharFormularioConta();
            }
        }
    });

    if (selectGrupoDre) {
        selectGrupoDre.onchange = () => {
            preencherCategoriasDre();
            preencherSubcategoriasDre();
            atualizarResumoWizardFinanceiro();
        };
    }

    if (selectCategoriaDre) {
        selectCategoriaDre.onchange = () => {
            preencherSubcategoriasDre();
            atualizarResumoWizardFinanceiro();
        };
    }

    const camposResumo = [
        "financeiro-cliente-id",
        "financeiro-fornecedor",
        "financeiro-descricao",
        "financeiro-valor",
        "financeiro-vencimento",
        "financeiro-observacao",
        "financeiro-subcategoria-dre"
    ];

    camposResumo.forEach((id) => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener("input", atualizarResumoWizardFinanceiro);
            el.addEventListener("change", atualizarResumoWizardFinanceiro);
        }
    });

    definirVencimentoPadrao();
    preencherCamposCompetencia();
    atualizarLabelCompetencia();
    atualizarAbasFinanceiro();
    atualizarRotulosFormulario();
    atualizarWizardFinanceiro();
    carregarFinanceiro();
});

async function carregarFinanceiro() {
    try {
        const query = montarQueryFinanceiro();

        const endpointContas =
            financeiroModo === "receber"
                ? `/api/financeiro/receber?${query}`
                : `/api/financeiro/pagar/?${query}`;

        const [contasData, dashboardData] = await Promise.all([
            fetchJsonSafe(endpointContas),
            fetchJsonSafe(`/api/financeiro/dashboard/?${query}`)
        ]);

        financeiroContas = Array.isArray(contasData.contas) ? contasData.contas : [];

        preencherResumo(contasData.resumo || {});
        preencherDashboardPremium(dashboardData || {});
        renderizarGrafico7Dias(dashboardData.grafico_7_dias || []);
        renderizarDreDetalhado(dashboardData || {});
        atualizarLabelCompetencia();
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

        renderizarDreDetalhado({});
    }
}

async function carregarPlanoDre() {
    try {
        const data = await fetchJsonSafe(
            `/api/financeiro/dre/?empresa_id=${FINANCEIRO_EMPRESA_ID}&ativo=true`
        );

        financeiroPlanoDre = Array.isArray(data.itens) ? data.itens : [];
        preencherGruposDre();
        preencherCategoriasDre();
        preencherSubcategoriasDre();
    } catch (error) {
        console.error("[FINANCEIRO] Erro ao carregar plano DRE:", error);
        financeiroPlanoDre = [];
        preencherGruposDre();
        preencherCategoriasDre();
        preencherSubcategoriasDre();
        notifyToast(error.message || "Erro ao carregar plano DRE.", "error");
    }
}

function preencherGruposDre() {
    const select = document.getElementById("financeiro-grupo-dre");
    if (!select) return;

    const valorAtual = select.value;
    const grupos = [...new Set(
        financeiroPlanoDre
            .map((item) => (item.grupo || "").trim())
            .filter(Boolean)
    )].sort((a, b) => a.localeCompare(b, "pt-BR"));

    select.innerHTML = `<option value="">Selecione o grupo</option>`;

    grupos.forEach((grupo) => {
        const option = document.createElement("option");
        option.value = grupo;
        option.textContent = grupo;
        select.appendChild(option);
    });

    if (grupos.includes(valorAtual)) {
        select.value = valorAtual;
    } else {
        select.value = "";
    }
}

function preencherCategoriasDre() {
    const selectGrupo = document.getElementById("financeiro-grupo-dre");
    const selectCategoria = document.getElementById("financeiro-categoria-dre");
    if (!selectGrupo || !selectCategoria) return;

    const grupoSelecionado = (selectGrupo.value || "").trim();
    const valorAtual = selectCategoria.value;

    const categorias = [...new Set(
        financeiroPlanoDre
            .filter((item) => !grupoSelecionado || String(item.grupo || "").trim() === grupoSelecionado)
            .map((item) => (item.categoria || "").trim())
            .filter(Boolean)
    )].sort((a, b) => a.localeCompare(b, "pt-BR"));

    selectCategoria.innerHTML = `<option value="">Selecione a categoria</option>`;

    categorias.forEach((categoria) => {
        const option = document.createElement("option");
        option.value = categoria;
        option.textContent = categoria;
        selectCategoria.appendChild(option);
    });

    selectCategoria.disabled = categorias.length === 0;

    if (categorias.includes(valorAtual)) {
        selectCategoria.value = valorAtual;
    } else {
        selectCategoria.value = "";
    }
}

function preencherSubcategoriasDre() {
    const selectGrupo = document.getElementById("financeiro-grupo-dre");
    const selectCategoria = document.getElementById("financeiro-categoria-dre");
    const selectSubcategoria = document.getElementById("financeiro-subcategoria-dre");

    if (!selectGrupo || !selectCategoria || !selectSubcategoria) return;

    const grupoSelecionado = (selectGrupo.value || "").trim();
    const categoriaSelecionada = (selectCategoria.value || "").trim();
    const valorAtual = selectSubcategoria.value;

    const subcategorias = financeiroPlanoDre
        .filter((item) => !grupoSelecionado || String(item.grupo || "").trim() === grupoSelecionado)
        .filter((item) => !categoriaSelecionada || String(item.categoria || "").trim() === categoriaSelecionada)
        .sort((a, b) => {
            const ordemA = Number(a.ordem || 0);
            const ordemB = Number(b.ordem || 0);

            if (ordemA !== ordemB) {
                return ordemA - ordemB;
            }

            return String(a.subcategoria || "").localeCompare(String(b.subcategoria || ""), "pt-BR");
        });

    selectSubcategoria.innerHTML = `<option value="">Selecione a subcategoria</option>`;

    subcategorias.forEach((item) => {
        const option = document.createElement("option");
        option.value = String(item.id);
        option.textContent = item.subcategoria || "Sem subcategoria";
        option.dataset.grupo = item.grupo || "";
        option.dataset.categoria = item.categoria || "";
        selectSubcategoria.appendChild(option);
    });

    selectSubcategoria.disabled = subcategorias.length === 0;

    if (subcategorias.some((item) => String(item.id) === String(valorAtual))) {
        selectSubcategoria.value = String(valorAtual);
    } else {
        selectSubcategoria.value = "";
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

function renderizarDreDetalhado(data) {
    const containerGrupos = document.getElementById("financeiro-dre-grupos");
    const containerCategorias = document.getElementById("financeiro-dre-categorias");
    const containerSubcategorias = document.getElementById("financeiro-dre-subcategorias");

    if (!containerGrupos || !containerCategorias || !containerSubcategorias) {
        return;
    }

    const grupos = Array.isArray(data.dre_despesas_por_grupo) ? data.dre_despesas_por_grupo : [];
    const categorias = Array.isArray(data.dre_despesas_por_categoria) ? data.dre_despesas_por_categoria : [];
    const subcategorias = Array.isArray(data.dre_despesas_por_subcategoria) ? data.dre_despesas_por_subcategoria : [];

    renderizarListaDre(
        containerGrupos,
        grupos,
        (item) => `
            <div class="financeiro-info">
                <span class="financeiro-info-label">${escapeHtml(item.grupo_dre || "Sem grupo")}</span>
                <span class="financeiro-info-value">${formatarMoeda(item.total || 0)}</span>
            </div>
        `,
        "Nenhuma despesa classificada por grupo no período."
    );

    renderizarListaDre(
        containerCategorias,
        categorias,
        (item) => `
            <div class="financeiro-info">
                <span class="financeiro-info-label">
                    ${escapeHtml(item.grupo_dre || "Sem grupo")} › ${escapeHtml(item.categoria_dre || "Sem categoria")}
                </span>
                <span class="financeiro-info-value">${formatarMoeda(item.total || 0)}</span>
            </div>
        `,
        "Nenhuma despesa classificada por categoria no período."
    );

    renderizarListaDre(
        containerSubcategorias,
        subcategorias,
        (item) => `
            <div class="financeiro-info">
                <span class="financeiro-info-label">
                    ${escapeHtml(item.grupo_dre || "Sem grupo")} ›
                    ${escapeHtml(item.categoria_dre || "Sem categoria")} ›
                    ${escapeHtml(item.subcategoria_dre || "Sem subcategoria")}
                </span>
                <span class="financeiro-info-value">${formatarMoeda(item.total || 0)}</span>
            </div>
        `,
        "Nenhuma despesa classificada por subcategoria no período."
    );
}

function renderizarListaDre(container, itens, renderItem, mensagemVazia) {
    container.innerHTML = "";

    if (!Array.isArray(itens) || !itens.length) {
        container.innerHTML = `
            <div class="financeiro-empty">
                <p>${escapeHtml(mensagemVazia)}</p>
            </div>
        `;
        return;
    }

    itens.forEach((item) => {
        const bloco = document.createElement("div");
        bloco.className = "financeiro-card";
        bloco.innerHTML = `
            <div class="financeiro-card-body">
                ${renderItem(item)}
            </div>
        `;
        container.appendChild(bloco);
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

        const blocoDre =
            financeiroModo === "pagar"
                ? `
                <div class="financeiro-info">
                    <span class="financeiro-info-label">Grupo DRE</span>
                    <span class="financeiro-info-value">${escapeHtml(conta.grupo_dre || "Não informado")}</span>
                </div>

                <div class="financeiro-info">
                    <span class="financeiro-info-label">Categoria DRE</span>
                    <span class="financeiro-info-value">${escapeHtml(conta.categoria_dre || "Não informado")}</span>
                </div>

                <div class="financeiro-info">
                    <span class="financeiro-info-label">Subcategoria DRE</span>
                    <span class="financeiro-info-value">${escapeHtml(conta.subcategoria_dre || "Não informado")}</span>
                </div>
                `
                : "";

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

                ${blocoDre}

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
    const classificacaoDreId = getValue("financeiro-subcategoria-dre");

    if (!descricao || descricao.trim().length < 2) {
        notifyToast("Informe uma descrição válida.", "error");
        irParaStepFinanceiro(1);
        return;
    }

    if (!valor || Number(valor) <= 0) {
        notifyToast("Informe um valor maior que zero.", "error");
        irParaStepFinanceiro(1);
        return;
    }

    if (!vencimento) {
        notifyToast("Informe a data de vencimento.", "error");
        irParaStepFinanceiro(1);
        return;
    }

    if (financeiroModo === "pagar" && !classificacaoDreId) {
        notifyToast("Selecione grupo, categoria e subcategoria do DRE.", "error");
        irParaStepFinanceiro(2);
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
                classificacao_dre_id: Number(classificacaoDreId),
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
    const overlay = document.getElementById("financeiro-modal-overlay");
    const card = document.getElementById("financeiro-modal-card");

    if (!overlay || !card) {
        console.error("Modal não encontrado.");
        return;
    }

    if (overlay.parentElement !== document.body) {
        document.body.appendChild(overlay);
    }

    limparFormularioConta();
    financeiroWizardStep = 1;
    atualizarRotulosFormulario();
    atualizarWizardFinanceiro();

    overlay.removeAttribute("style");
    card.removeAttribute("style");

    overlay.style.display = "block";
    overlay.style.position = "fixed";
    overlay.style.top = "0";
    overlay.style.left = "0";
    overlay.style.width = "100vw";
    overlay.style.height = "100vh";
    overlay.style.background = "rgba(15, 23, 42, 0.45)";
    overlay.style.zIndex = "999999";

    card.style.position = "fixed";
    card.style.top = "50%";
    card.style.left = "50%";
    card.style.transform = "translate(-50%, -50%)";
    card.style.width = "min(920px, calc(100vw - 32px))";
    card.style.maxHeight = "calc(100vh - 32px)";
    card.style.overflow = "auto";
    card.style.background = "#fff";
    card.style.borderRadius = "20px";
    card.style.boxShadow = "0 24px 80px rgba(15, 23, 42, 0.28)";
    card.style.zIndex = "1000000";
    card.style.display = "block";

    document.body.classList.add("financeiro-modal-open");

    if (financeiroModo === "pagar") {
        carregarPlanoDre();
    }
}

function fecharFormularioConta() {
    const overlay = document.getElementById("financeiro-modal-overlay");
    const card = document.getElementById("financeiro-modal-card");

    if (overlay) {
        overlay.style.display = "none";
    }

    if (card) {
        card.removeAttribute("style");
    }

    document.body.classList.remove("financeiro-modal-open");
    financeiroWizardStep = 1;
    atualizarWizardFinanceiro();
}

function limparFormularioConta() {
    setValue("financeiro-cliente-id", "");
    setValue("financeiro-fornecedor", "");
    setValue("financeiro-descricao", "");
    setValue("financeiro-valor", "");
    setValue("financeiro-observacao", "");
    setValue("financeiro-grupo-dre", "");
    setValue("financeiro-categoria-dre", "");
    setValue("financeiro-subcategoria-dre", "");
    definirVencimentoPadrao();
    preencherCategoriasDre();
    preencherSubcategoriasDre();
    atualizarResumoWizardFinanceiro();
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
    const tituloModal = document.getElementById("financeiro-modal-title");
    const subtituloModal = document.getElementById("financeiro-modal-subtitle");
    const tituloLista = document.getElementById("financeiro-titulo-lista");
    const badgeLista = document.getElementById("financeiro-badge-lista");
    const labelCliente = document.getElementById("financeiro-label-cliente-id");
    const fieldCliente = document.getElementById("financeiro-field-cliente-id");
    const fieldFornecedor = document.getElementById("financeiro-field-fornecedor");
    const fieldDre = document.getElementById("financeiro-dre-fields");
    const dreEmpty = document.getElementById("financeiro-step-2-empty");
    const btnSalvar = document.getElementById("btn-salvar-conta");
    const reviewTipo = document.getElementById("financeiro-review-tipo");

    if (tituloModal) {
        tituloModal.textContent =
            financeiroModo === "receber" ? "Nova Conta a Receber" : "Nova Conta a Pagar";
    }

    if (subtituloModal) {
        subtituloModal.textContent =
            financeiroModo === "receber"
                ? "Preencha os dados e conclua o lançamento do recebimento."
                : "Preencha os dados e classifique a despesa antes de salvar.";
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

    if (fieldDre) {
        fieldDre.style.display = financeiroModo === "pagar" ? "grid" : "none";
    }

    if (dreEmpty) {
        dreEmpty.style.display = financeiroModo === "receber" ? "block" : "none";
    }

    if (btnSalvar) {
        btnSalvar.textContent =
            financeiroModo === "receber" ? "Salvar Conta a Receber" : "Salvar Conta a Pagar";
    }

    if (reviewTipo) {
        reviewTipo.textContent =
            financeiroModo === "receber" ? "Conta a Receber" : "Conta a Pagar";
    }

    atualizarResumoWizardFinanceiro();
    atualizarWizardFinanceiro();
}

function avancarStepFinanceiro() {
    if (!validarStepAtualFinanceiro()) {
        return;
    }

    if (financeiroModo === "receber" && financeiroWizardStep === 1) {
        financeiroWizardStep = 3;
    } else {
        financeiroWizardStep += 1;
    }

    if (financeiroWizardStep > 3) {
        financeiroWizardStep = 3;
    }

    atualizarResumoWizardFinanceiro();
    atualizarWizardFinanceiro();
}

function voltarStepFinanceiro() {
    if (financeiroModo === "receber" && financeiroWizardStep === 3) {
        financeiroWizardStep = 1;
    } else {
        financeiroWizardStep -= 1;
    }

    if (financeiroWizardStep < 1) {
        financeiroWizardStep = 1;
    }

    atualizarWizardFinanceiro();
}

function irParaStepFinanceiro(step) {
    financeiroWizardStep = step;
    atualizarResumoWizardFinanceiro();
    atualizarWizardFinanceiro();
}

function validarStepAtualFinanceiro() {
    if (financeiroWizardStep === 1) {
        const descricao = getValue("financeiro-descricao");
        const valor = getValue("financeiro-valor");
        const vencimento = getValue("financeiro-vencimento");

        if (!descricao || descricao.trim().length < 2) {
            notifyToast("Informe uma descrição válida.", "error");
            return false;
        }

        if (!valor || Number(valor) <= 0) {
            notifyToast("Informe um valor maior que zero.", "error");
            return false;
        }

        if (!vencimento) {
            notifyToast("Informe a data de vencimento.", "error");
            return false;
        }

        return true;
    }

    if (financeiroWizardStep === 2 && financeiroModo === "pagar") {
        const classificacaoDreId = getValue("financeiro-subcategoria-dre");

        if (!classificacaoDreId) {
            notifyToast("Selecione grupo, categoria e subcategoria do DRE.", "error");
            return false;
        }
    }

    return true;
}

function atualizarWizardFinanceiro() {
    const step1 = document.getElementById("financeiro-step-1");
    const step2 = document.getElementById("financeiro-step-2");
    const step3 = document.getElementById("financeiro-step-3");

    const indicador1 = document.getElementById("financeiro-step-indicador-1");
    const indicador2 = document.getElementById("financeiro-step-indicador-2");
    const indicador3 = document.getElementById("financeiro-step-indicador-3");

    const btnVoltar = document.getElementById("btn-voltar-step-financeiro");
    const btnAvancar = document.getElementById("btn-avancar-step-financeiro");
    const btnSalvar = document.getElementById("btn-salvar-conta");

    [step1, step2, step3].forEach((el) => {
        if (el) {
            el.classList.remove("is-active");
        }
    });

    [indicador1, indicador2, indicador3].forEach((el) => {
        if (el) {
            el.classList.remove("is-active", "is-done");
        }
    });

    if (step1 && financeiroWizardStep === 1) step1.classList.add("is-active");
    if (step2 && financeiroWizardStep === 2) step2.classList.add("is-active");
    if (step3 && financeiroWizardStep === 3) step3.classList.add("is-active");

    if (indicador1) {
        indicador1.classList.add("is-active");
        if (financeiroWizardStep > 1) {
            indicador1.classList.remove("is-active");
            indicador1.classList.add("is-done");
        }
    }

    if (indicador2) {
        if (financeiroModo === "receber") {
            indicador2.classList.remove("is-active", "is-done");
        } else if (financeiroWizardStep === 2) {
            indicador2.classList.add("is-active");
        } else if (financeiroWizardStep > 2) {
            indicador2.classList.add("is-done");
        }
    }

    if (indicador3 && financeiroWizardStep === 3) {
        indicador3.classList.add("is-active");
    }

    if (btnVoltar) {
        btnVoltar.style.display = financeiroWizardStep > 1 ? "inline-flex" : "none";
    }

    if (btnAvancar) {
        btnAvancar.style.display = financeiroWizardStep < 3 ? "inline-flex" : "none";
        btnAvancar.textContent =
            financeiroModo === "receber" && financeiroWizardStep === 1
                ? "Ir para Revisão"
                : "Avançar";
    }

    if (btnSalvar) {
        btnSalvar.style.display = financeiroWizardStep === 3 ? "inline-flex" : "none";
    }
}

function atualizarResumoWizardFinanceiro() {
    const pessoa =
        financeiroModo === "receber"
            ? (getValue("financeiro-cliente-id") || "Não informado")
            : (getValue("financeiro-fornecedor") || "Não informado");

    const descricao = getValue("financeiro-descricao") || "-";
    const valor = Number(getValue("financeiro-valor") || 0);
    const vencimento = getValue("financeiro-vencimento");
    const observacao = getValue("financeiro-observacao") || "Sem observação";

    const selectGrupo = document.getElementById("financeiro-grupo-dre");
    const selectCategoria = document.getElementById("financeiro-categoria-dre");
    const selectSubcategoria = document.getElementById("financeiro-subcategoria-dre");

    const grupo = selectGrupo?.selectedOptions?.[0]?.textContent || "-";
    const categoria = selectCategoria?.selectedOptions?.[0]?.textContent || "-";
    const subcategoria = selectSubcategoria?.selectedOptions?.[0]?.textContent || "-";

    setText("financeiro-review-pessoa", String(pessoa));
    setText("financeiro-review-descricao", descricao);
    setText("financeiro-review-valor", formatarMoeda(valor));
    setText("financeiro-review-vencimento", vencimento ? formatarData(vencimento) : "-");
    setText("financeiro-review-grupo", financeiroModo === "pagar" ? grupo : "Não se aplica");
    setText("financeiro-review-categoria", financeiroModo === "pagar" ? categoria : "Não se aplica");
    setText("financeiro-review-subcategoria", financeiroModo === "pagar" ? subcategoria : "Não se aplica");
    setText("financeiro-review-observacao", observacao);
}

function preencherCamposCompetencia() {
    const selectMes = document.getElementById("financeiro-mes");
    const inputAno = document.getElementById("financeiro-ano");

    if (selectMes) {
        selectMes.value = String(financeiroCompetencia.mes);
    }

    if (inputAno) {
        inputAno.value = String(financeiroCompetencia.ano);
    }
}

function atualizarCompetenciaDosCampos() {
    const selectMes = document.getElementById("financeiro-mes");
    const inputAno = document.getElementById("financeiro-ano");

    const mes = Number(selectMes?.value || 0);
    const ano = Number(inputAno?.value || 0);

    if (!mes || mes < 1 || mes > 12) {
        notifyToast("Selecione um mês válido.", "error");
        return false;
    }

    if (!ano || ano < 2000 || ano > 2100) {
        notifyToast("Informe um ano válido.", "error");
        return false;
    }

    financeiroCompetencia = { mes, ano };
    atualizarLabelCompetencia();
    return true;
}

function atualizarLabelCompetencia() {
    const el = document.getElementById("financeiro-competencia-atual");
    if (!el) return;

    const mesNome = obterNomeMes(financeiroCompetencia.mes);
    el.textContent = `${mesNome} / ${financeiroCompetencia.ano}`;
}

function montarQueryFinanceiro() {
    const params = new URLSearchParams();
    params.set("empresa_id", String(FINANCEIRO_EMPRESA_ID));
    params.set("mes", String(financeiroCompetencia.mes));
    params.set("ano", String(financeiroCompetencia.ano));
    return params.toString();
}

function obterCompetenciaAtual() {
    const hoje = new Date();
    return {
        mes: hoje.getMonth() + 1,
        ano: hoje.getFullYear()
    };
}

function obterNomeMes(mes) {
    const meses = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ];

    return meses[Number(mes) - 1] || "Mês";
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

    const data = new Date(`${valor}T00:00:00`);
    if (Number.isNaN(data.getTime())) return valor;

    return data.toLocaleDateString("pt-BR");
}

function formatarDataCurta(valor) {
    if (!valor) return "-";

    const data = new Date(`${valor}T00:00:00`);
    if (Number.isNaN(data.getTime())) return valor;

    return data.toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "2-digit"
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

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = value;
    }
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

window.abrirFormularioConta = abrirFormularioConta;
window.fecharFormularioConta = fecharFormularioConta;
window.salvarConta = salvarConta;
window.baixarConta = baixarConta;