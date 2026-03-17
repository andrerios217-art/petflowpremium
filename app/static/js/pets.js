console.log("Pets module carregado");

document.addEventListener("DOMContentLoaded", () => {
    const historicoModal = document.getElementById("pet-historico-modal");
    const historicoBody = document.getElementById("pet-historico-body");
    const historicoTitulo = document.getElementById("pet-historico-titulo");
    const historicoSubtitulo = document.getElementById("pet-historico-subtitulo");
    const historicoClose = document.getElementById("pet-historico-close");
    const historicoBackdrop = document.getElementById("pet-historico-backdrop");

    const buscaPets = document.getElementById("busca-pets");
    const petsTbody = document.getElementById("pets-tbody");

    const confirmModal = document.getElementById("pet-confirm-modal");
    const confirmBackdrop = document.getElementById("pet-confirm-backdrop");
    const confirmClose = document.getElementById("pet-confirm-close");
    const confirmCancel = document.getElementById("pet-confirm-cancel");
    const confirmSubmit = document.getElementById("pet-confirm-submit");
    const confirmTitle = document.getElementById("pet-confirm-title");
    const confirmSubtitle = document.getElementById("pet-confirm-subtitle");
    const confirmMessage = document.getElementById("pet-confirm-message");

    let confirmCallback = null;

    function escapeHtml(value) {
        if (value === null || value === undefined) return "-";

        return String(value)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#39;");
    }

    function formatarData(data) {
        if (!data) return "-";

        try {
            return new Date(`${data}T00:00:00`).toLocaleDateString("pt-BR");
        } catch (error) {
            return data;
        }
    }

    function formatarHora(hora) {
        if (!hora) return "-";
        return String(hora).slice(0, 5);
    }

    function formatarDataHora(dataHora) {
        if (!dataHora) return "-";

        try {
            return new Date(dataHora).toLocaleString("pt-BR");
        } catch (error) {
            return dataHora;
        }
    }

    function formatarLista(lista) {
        if (!lista || !lista.length) return "-";
        return lista.map((item) => escapeHtml(item)).join(", ");
    }

    function formatarBooleano(valor) {
        return valor ? "Sim" : "Não";
    }

    function abrirHistoricoModal() {
        if (!historicoModal) return;
        historicoModal.classList.remove("hidden");
        document.body.style.overflow = "hidden";
    }

    function fecharHistoricoModal() {
        if (!historicoModal) return;

        historicoModal.classList.add("hidden");
        document.body.style.overflow = "";

        if (historicoBody) {
            historicoBody.innerHTML = `
                <div class="empty-state">
                    <h4>Carregando histórico...</h4>
                    <p>Aguarde enquanto buscamos os dados do pet.</p>
                </div>
            `;
        }
    }

    function abrirConfirmModal({
        title = "Confirmar ação",
        subtitle = "Revise a ação antes de continuar.",
        message = "Deseja continuar?",
        confirmText = "Confirmar",
        onConfirm = null,
    }) {
        if (!confirmModal) return;

        confirmCallback = onConfirm;

        if (confirmTitle) confirmTitle.textContent = title;
        if (confirmSubtitle) confirmSubtitle.textContent = subtitle;
        if (confirmMessage) confirmMessage.innerHTML = message;
        if (confirmSubmit) confirmSubmit.textContent = confirmText;

        confirmModal.classList.remove("hidden");
        document.body.style.overflow = "hidden";
    }

    function fecharConfirmModal() {
        if (!confirmModal) return;

        confirmModal.classList.add("hidden");
        confirmCallback = null;

        if (!historicoModal || historicoModal.classList.contains("hidden")) {
            document.body.style.overflow = "";
        }
    }

    async function confirmarAcaoModal() {
        if (typeof confirmCallback === "function") {
            await confirmCallback();
        }

        fecharConfirmModal();
    }

    function renderizarResumoPet(pet) {
        return `
            <section class="historico-section">
                <div style="display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-bottom:14px;">
                    <h3 style="margin:0;">Resumo do Pet</h3>
                    <button
                        type="button"
                        class="btn btn-secondary"
                        id="btn-ir-historico-veterinario"
                    >
                        Histórico Veterinário
                    </button>
                </div>

                <div class="detail-grid">
                    <div class="detail-box">
                        <span class="detail-label">Nome</span>
                        <strong>${escapeHtml(pet.nome)}</strong>
                    </div>

                    <div class="detail-box">
                        <span class="detail-label">Tutor</span>
                        <strong>${escapeHtml(pet.tutor)}</strong>
                    </div>

                    <div class="detail-box">
                        <span class="detail-label">Raça</span>
                        <strong>${escapeHtml(pet.raca)}</strong>
                    </div>

                    <div class="detail-box">
                        <span class="detail-label">Porte</span>
                        <strong>${escapeHtml(pet.porte)}</strong>
                    </div>

                    <div class="detail-box">
                        <span class="detail-label">Peso</span>
                        <strong>${pet.peso ?? "-"}</strong>
                    </div>

                    <div class="detail-box">
                        <span class="detail-label">Sexo</span>
                        <strong>${escapeHtml(pet.sexo)}</strong>
                    </div>

                    <div class="detail-box">
                        <span class="detail-label">Temperamento</span>
                        <strong>${escapeHtml(pet.temperamento)}</strong>
                    </div>

                    <div class="detail-box">
                        <span class="detail-label">Nascimento</span>
                        <strong>${formatarData(pet.nascimento)}</strong>
                    </div>

                    <div class="detail-box">
                        <span class="detail-label">Pode perfume</span>
                        <strong>${formatarBooleano(pet.pode_perfume)}</strong>
                    </div>

                    <div class="detail-box">
                        <span class="detail-label">Pode acessório</span>
                        <strong>${formatarBooleano(pet.pode_acessorio)}</strong>
                    </div>

                    <div class="detail-box">
                        <span class="detail-label">Castrado</span>
                        <strong>${formatarBooleano(pet.castrado)}</strong>
                    </div>

                    <div class="detail-box">
                        <span class="detail-label">Status do cadastro</span>
                        <strong>${pet.ativo ? "Ativo" : "Inativo"}</strong>
                    </div>

                    <div class="detail-box" style="grid-column: 1 / -1;">
                        <span class="detail-label">Observações cadastrais</span>
                        <strong>${escapeHtml(pet.observacoes_cadastrais)}</strong>
                    </div>
                </div>
            </section>
        `;
    }

    function renderizarTimeline(timeline) {
        if (!timeline || !timeline.length) {
            return `
                <div class="historico-item">
                    <p>Nenhum histórico operacional encontrado para este atendimento.</p>
                </div>
            `;
        }

        return `
            <div class="historico-section">
                <h4>Timeline Operacional</h4>
                ${timeline
                    .map(
                        (item) => `
                            <div class="historico-item">
                                <p><strong>Etapa:</strong> ${escapeHtml(item.etapa)}</p>
                                <p><strong>Status:</strong> ${escapeHtml(item.status)}</p>
                                <p><strong>Iniciado em:</strong> ${formatarDataHora(item.iniciado_em)}</p>
                                <p><strong>Finalizado em:</strong> ${formatarDataHora(item.finalizado_em)}</p>
                                <p><strong>Funcionário:</strong> ${escapeHtml(item.funcionario)}</p>
                                <p><strong>Tempo gasto:</strong> ${item.tempo_gasto_minutos ?? "-"} min</p>
                                <p><strong>Intercorrência:</strong> ${escapeHtml(item.intercorrencia)}</p>
                                <p><strong>Observações:</strong> ${escapeHtml(item.observacoes)}</p>
                            </div>
                        `
                    )
                    .join("")}
            </div>
        `;
    }

    function renderizarHistoricoVeterinario(consultasVeterinarias) {
        if (!consultasVeterinarias || !consultasVeterinarias.length) {
            return `
                <section class="historico-section" id="historico-veterinario-section">
                    <h3>Histórico Veterinário</h3>
                    <div class="empty-state">
                        <h4>Sem consultas veterinárias</h4>
                        <p>Este pet ainda não possui histórico veterinário registrado.</p>
                    </div>
                </section>
            `;
        }

        return `
            <section class="historico-section" id="historico-veterinario-section">
                <h3>Histórico Veterinário</h3>

                ${consultasVeterinarias
                    .map(
                        (item) => `
                            <div class="historico-item" style="margin-bottom: 16px;">
                                <p><strong>Início:</strong> ${formatarDataHora(item.data_inicio)}</p>
                                <p><strong>Fim:</strong> ${formatarDataHora(item.data_fim)}</p>
                                <p><strong>Status:</strong> ${escapeHtml(item.status)}</p>
                                <p><strong>Veterinário:</strong> ${escapeHtml(item.veterinario)}</p>
                                <p><strong>Serviços executados:</strong> ${formatarLista(item.servicos_executados)}</p>
                                <p><strong>Observações da recepção:</strong> ${escapeHtml(item.observacoes_recepcao)}</p>
                                <p><strong>Observações clínicas:</strong> ${escapeHtml(item.observacoes_clinicas)}</p>

                                <hr>

                                <p><strong>Anamnese</strong></p>
                                <p><strong>Queixa principal:</strong> ${escapeHtml(item.anamnese?.queixa_principal)}</p>
                                <p><strong>Histórico atual:</strong> ${escapeHtml(item.anamnese?.historico_atual)}</p>
                                <p><strong>Alimentação:</strong> ${escapeHtml(item.anamnese?.alimentacao)}</p>
                                <p><strong>Alergias:</strong> ${escapeHtml(item.anamnese?.alergias)}</p>
                                <p><strong>Uso de medicação atual:</strong> ${escapeHtml(item.anamnese?.uso_medicacao_atual)}</p>
                                <p><strong>Observações da anamnese:</strong> ${escapeHtml(item.anamnese?.observacoes)}</p>

                                <hr>

                                <p><strong>Prontuário</strong></p>
                                <p><strong>Exame físico:</strong> ${escapeHtml(item.prontuario?.exame_fisico)}</p>
                                <p><strong>Diagnóstico:</strong> ${escapeHtml(item.prontuario?.diagnostico)}</p>
                                <p><strong>Conduta:</strong> ${escapeHtml(item.prontuario?.conduta)}</p>
                                <p><strong>Observações do prontuário:</strong> ${escapeHtml(item.prontuario?.observacoes)}</p>
                                <p><strong>Observações gerais:</strong> ${escapeHtml(item.prontuario?.observacoes_gerais)}</p>
                                <p><strong>Medicações:</strong> ${escapeHtml(item.prontuario?.medicacoes)}</p>
                                <p><strong>Exames:</strong> ${escapeHtml(item.prontuario?.exames)}</p>
                                <p><strong>Receita:</strong> ${escapeHtml(item.prontuario?.receita)}</p>
                            </div>
                        `
                    )
                    .join("")}
            </section>
        `;
    }

    function renderizarAtendimentos(atendimentos) {
        if (!atendimentos || !atendimentos.length) {
            return `
                <section class="historico-section">
                    <h3>Histórico de Atendimentos</h3>
                    <div class="empty-state">
                        <h4>Sem atendimentos</h4>
                        <p>Este pet ainda não possui atendimentos registrados.</p>
                    </div>
                </section>
            `;
        }

        return `
            <section class="historico-section">
                <h3>Histórico de Atendimentos</h3>

                ${atendimentos
                    .map(
                        (item) => `
                            <div class="historico-item" style="margin-bottom: 16px;">
                                <p><strong>Data:</strong> ${formatarData(item.data)} às ${formatarHora(item.hora)}</p>
                                <p><strong>Funcionário responsável:</strong> ${escapeHtml(item.funcionario_responsavel)}</p>
                                <p><strong>Status final:</strong> ${escapeHtml(item.status_final)}</p>
                                <p><strong>Serviços executados:</strong> ${formatarLista(item.servicos_executados)}</p>
                                <p><strong>Intercorrências:</strong> ${formatarLista(item.intercorrencias)}</p>
                                <p><strong>Tempo total:</strong> ${item.tempo_total_atendimento_minutos ?? "-"} min</p>
                                <p><strong>Observações gerais:</strong> ${escapeHtml(item.observacoes_gerais)}</p>
                                <p><strong>Observações da produção:</strong> ${escapeHtml(item.observacoes_producao)}</p>

                                ${renderizarTimeline(item.timeline)}
                            </div>
                        `
                    )
                    .join("")}
            </section>
        `;
    }

    function ativarBotaoHistoricoVeterinario() {
        const botao = document.getElementById("btn-ir-historico-veterinario");
        const secao = document.getElementById("historico-veterinario-section");

        if (!botao || !secao) return;

        botao.addEventListener("click", () => {
            secao.scrollIntoView({
                behavior: "smooth",
                block: "start",
            });
        });
    }

    async function abrirHistoricoPet(petId, petNome) {
        abrirHistoricoModal();

        if (historicoTitulo) {
            historicoTitulo.textContent = "Histórico do Pet";
        }

        if (historicoSubtitulo) {
            historicoSubtitulo.textContent = petNome
                ? `Visualização completa do pet ${petNome}.`
                : "Visualização completa de atendimentos e produção.";
        }

        if (historicoBody) {
            historicoBody.innerHTML = `
                <div class="empty-state">
                    <h4>Carregando histórico...</h4>
                    <p>Aguarde enquanto buscamos os dados do pet.</p>
                </div>
            `;
        }

        try {
            const response = await fetch(`/api/pets/${petId}/historico`);

            if (!response.ok) {
                let mensagem = "Não foi possível carregar o histórico do pet.";

                try {
                    const erro = await response.json();
                    if (erro?.detail) {
                        mensagem = erro.detail;
                    }
                } catch (jsonError) {
                    console.warn("Erro ao interpretar resposta de erro:", jsonError);
                }

                throw new Error(mensagem);
            }

            const data = await response.json();

            if (historicoBody) {
                historicoBody.innerHTML = `
                    ${renderizarResumoPet(data.pet)}
                    ${renderizarHistoricoVeterinario(data.consultas_veterinarias)}
                    ${renderizarAtendimentos(data.atendimentos)}
                `;

                ativarBotaoHistoricoVeterinario();
            }
        } catch (error) {
            if (historicoBody) {
                historicoBody.innerHTML = `
                    <div class="empty-state error-state">
                        <h4>Erro ao carregar histórico</h4>
                        <p>${escapeHtml(error.message || "Erro ao carregar histórico do pet.")}</p>
                    </div>
                `;
            }
        }
    }

    async function executarTogglePet(petId, buscaAtual) {
        const response = await fetch(`/api/pets/${petId}/toggle`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
        });

        if (!response.ok) {
            let mensagem = "Não foi possível alterar o status do pet.";

            try {
                const erro = await response.json();
                if (erro?.detail) {
                    mensagem = erro.detail;
                }
            } catch (jsonError) {
                console.warn("Erro ao interpretar resposta de erro:", jsonError);
            }

            throw new Error(mensagem);
        }

        await carregarPets(buscaAtual);
    }

    function alternarStatusPet(petId, nomePet, ativoAtual) {
        const acao = ativoAtual ? "inativar" : "ativar";
        const confirmText = ativoAtual ? "Inativar" : "Ativar";
        const buscaAtual = buscaPets ? buscaPets.value : "";

        abrirConfirmModal({
            title: ativoAtual ? "Inativar pet" : "Ativar pet",
            subtitle: "Confirme a alteração de status do cadastro.",
            message: `Deseja realmente ${acao} o pet "${escapeHtml(nomePet)}"?`,
            confirmText,
            onConfirm: async () => {
                try {
                    await executarTogglePet(petId, buscaAtual);
                } catch (error) {
                    fecharConfirmModal();
                    window.alert(error.message || "Erro ao alterar status do pet.");
                }
            },
        });
    }

    async function carregarPets(q = "") {
        try {
            const response = await fetch(`/api/pets?q=${encodeURIComponent(q)}`);
            const data = await response.json();

            if (!petsTbody) return;

            if (!data.length) {
                petsTbody.innerHTML = `
                    <tr>
                        <td colspan="7">Nenhum pet encontrado.</td>
                    </tr>
                `;
                return;
            }

            petsTbody.innerHTML = data
                .map(
                    (pet) => `
                        <tr>
                            <td>${escapeHtml(pet.nome ?? "-")}</td>
                            <td>${escapeHtml(pet.cliente_id ?? "-")}</td>
                            <td>${escapeHtml(pet.raca ?? "-")}</td>
                            <td>${escapeHtml(pet.sexo ?? "-")}</td>
                            <td>${escapeHtml(pet.porte ?? "-")}</td>
                            <td>${pet.ativo ? "Ativo" : "Inativo"}</td>
                            <td>
                                <button
                                    type="button"
                                    class="btn btn-secondary pet-action-btn historico"
                                    data-pet-id="${pet.id}"
                                    data-pet-nome="${escapeHtml(pet.nome ?? "")}"
                                >
                                    Histórico
                                </button>

                                <button
                                    type="button"
                                    class="btn ${pet.ativo ? "btn-light" : "btn-primary"}"
                                    data-toggle-pet-id="${pet.id}"
                                    data-toggle-pet-nome="${escapeHtml(pet.nome ?? "")}"
                                    data-toggle-pet-ativo="${pet.ativo ? "true" : "false"}"
                                >
                                    ${pet.ativo ? "Inativar" : "Ativar"}
                                </button>
                            </td>
                        </tr>
                    `
                )
                .join("");

            petsTbody.querySelectorAll(".pet-action-btn.historico").forEach((botao) => {
                botao.addEventListener("click", () => {
                    const petId = botao.getAttribute("data-pet-id");
                    const petNome = botao.getAttribute("data-pet-nome");
                    abrirHistoricoPet(petId, petNome);
                });
            });

            petsTbody.querySelectorAll("[data-toggle-pet-id]").forEach((botao) => {
                botao.addEventListener("click", () => {
                    const petId = botao.getAttribute("data-toggle-pet-id");
                    const petNome = botao.getAttribute("data-toggle-pet-nome");
                    const ativoAtual = botao.getAttribute("data-toggle-pet-ativo") === "true";
                    alternarStatusPet(petId, petNome, ativoAtual);
                });
            });
        } catch (error) {
            if (!petsTbody) return;

            petsTbody.innerHTML = `
                <tr>
                    <td colspan="7">Erro ao carregar pets.</td>
                </tr>
            `;
        }
    }

    if (buscaPets) {
        buscaPets.addEventListener("input", function () {
            carregarPets(this.value);
        });
    }

    if (historicoClose) {
        historicoClose.addEventListener("click", fecharHistoricoModal);
    }

    if (historicoBackdrop) {
        historicoBackdrop.addEventListener("click", fecharHistoricoModal);
    }

    if (confirmClose) {
        confirmClose.addEventListener("click", fecharConfirmModal);
    }

    if (confirmCancel) {
        confirmCancel.addEventListener("click", fecharConfirmModal);
    }

    if (confirmBackdrop) {
        confirmBackdrop.addEventListener("click", fecharConfirmModal);
    }

    if (confirmSubmit) {
        confirmSubmit.addEventListener("click", confirmarAcaoModal);
    }

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            if (confirmModal && !confirmModal.classList.contains("hidden")) {
                fecharConfirmModal();
                return;
            }

            if (historicoModal && !historicoModal.classList.contains("hidden")) {
                fecharHistoricoModal();
            }
        }
    });

    window.abrirHistoricoPet = abrirHistoricoPet;
    window.fecharHistoricoModal = fecharHistoricoModal;

    carregarPets();
});