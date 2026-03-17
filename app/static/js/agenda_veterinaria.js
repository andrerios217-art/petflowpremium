(function () {
    const state = {
        dataRef: getTodayISO(),
        agenda: [],
        dias: [],
        clientes: [],
        pets: [],
        funcionarios: [],
        servicos: [],
        servicosSelecionados: [],
        agendamentoAtual: null,
        historicoAberto: false,
        atendimentoClinicoId: null,
        atendimentoClinicoModo: "local",
    };

    const el = {
        agendaVetGrid: document.getElementById("agendaVetGrid"),
        periodoSemanaLabel: document.getElementById("periodoSemanaLabel"),
        filtroBuscaAgenda: document.getElementById("filtroBuscaAgenda"),
        btnSemanaAnterior: document.getElementById("btnSemanaAnterior"),
        btnHoje: document.getElementById("btnHoje"),
        btnProximaSemana: document.getElementById("btnProximaSemana"),
        btnNovoAgendamento: document.getElementById("btnNovoAgendamento"),

        modalAgendamentoVetOverlay: document.getElementById("modalAgendamentoVetOverlay"),
        btnFecharModalAgendamentoVet: document.getElementById("btnFecharModalAgendamentoVet"),
        btnCancelarAgendamentoVet: document.getElementById("btnCancelarAgendamentoVet"),
        btnSalvarAgendamentoVet: document.getElementById("btnSalvarAgendamentoVet"),

        agVetCliente: document.getElementById("agVetCliente"),
        agVetPet: document.getElementById("agVetPet"),
        agVetFuncionario: document.getElementById("agVetFuncionario"),
        agVetDataHora: document.getElementById("agVetDataHora"),
        agVetPrioridade: document.getElementById("agVetPrioridade"),
        agVetStatus: document.getElementById("agVetStatus"),
        agVetServicoSelect: document.getElementById("agVetServicoSelect"),
        btnAdicionarServicoVet: document.getElementById("btnAdicionarServicoVet"),
        agVetServicosSelecionados: document.getElementById("agVetServicosSelecionados"),
        agVetObservacoes: document.getElementById("agVetObservacoes"),

        modalAtendimentoClinicoOverlay: document.getElementById("modalAtendimentoClinicoOverlay"),
        btnFecharModalAtendimentoClinico: document.getElementById("btnFecharModalAtendimentoClinico"),
        btnFecharAtendimentoClinicoRodape: document.getElementById("btnFecharAtendimentoClinicoRodape"),
        btnSalvarRascunhoClinico: document.getElementById("btnSalvarRascunhoClinico"),
        btnAbrirHistoricoPet: document.getElementById("btnAbrirHistoricoPet"),
        btnFecharHistoricoDrawer: document.getElementById("btnFecharHistoricoDrawer"),

        clinicoTutorNome: document.getElementById("clinicoTutorNome"),
        clinicoTutorContato: document.getElementById("clinicoTutorContato"),
        clinicoPetNome: document.getElementById("clinicoPetNome"),
        clinicoPetResumo: document.getElementById("clinicoPetResumo"),
        clinicoServicosPrevistos: document.getElementById("clinicoServicosPrevistos"),
        clinicoHistoricoConteudo: document.getElementById("clinicoHistoricoConteudo"),

        clinicoQueixaPrincipal: document.getElementById("clinicoQueixaPrincipal"),
        clinicoHistoricoAtual: document.getElementById("clinicoHistoricoAtual"),
        clinicoObservacoesGerais: document.getElementById("clinicoObservacoesGerais"),
        clinicoServicosExecutados: document.getElementById("clinicoServicosExecutados"),
        clinicoMedicacoes: document.getElementById("clinicoMedicacoes"),
        clinicoExames: document.getElementById("clinicoExames"),
        clinicoReceita: document.getElementById("clinicoReceita"),
    };

    document.addEventListener("DOMContentLoaded", init);

    async function init() {
        bindEvents();

        await Promise.all([
            carregarClientes(),
            carregarFuncionarios(),
            carregarServicosVeterinarios(),
        ]);

        await carregarAgendaSemana();
    }

    function bindEvents() {
        if (el.btnSemanaAnterior) {
            el.btnSemanaAnterior.addEventListener("click", async () => {
                state.dataRef = addDays(state.dataRef, -7);
                await carregarAgendaSemana();
            });
        }

        if (el.btnHoje) {
            el.btnHoje.addEventListener("click", async () => {
                state.dataRef = getTodayISO();
                await carregarAgendaSemana();
            });
        }

        if (el.btnProximaSemana) {
            el.btnProximaSemana.addEventListener("click", async () => {
                state.dataRef = addDays(state.dataRef, 7);
                await carregarAgendaSemana();
            });
        }

        if (el.btnNovoAgendamento) {
            el.btnNovoAgendamento.addEventListener("click", abrirModalAgendamentoVet);
        }

        if (el.btnFecharModalAgendamentoVet) {
            el.btnFecharModalAgendamentoVet.addEventListener("click", fecharModalAgendamentoVet);
        }

        if (el.btnCancelarAgendamentoVet) {
            el.btnCancelarAgendamentoVet.addEventListener("click", (event) => {
                event.preventDefault();
                event.stopPropagation();
                fecharModalAgendamentoVet();
            });
        }

        if (el.btnSalvarAgendamentoVet) {
            el.btnSalvarAgendamentoVet.addEventListener("click", async (event) => {
                event.preventDefault();
                event.stopPropagation();
                await salvarAgendamentoVet();
            });
        }

        if (el.btnAdicionarServicoVet) {
            el.btnAdicionarServicoVet.addEventListener("click", adicionarServicoVetSelecionado);
        }

        if (el.agVetCliente) {
            el.agVetCliente.addEventListener("change", async (event) => {
                const clienteId = event.target.value;
                await carregarPets(clienteId || null);
            });
        }

        if (el.btnFecharModalAtendimentoClinico) {
            el.btnFecharModalAtendimentoClinico.addEventListener("click", fecharModalAtendimentoClinico);
        }

        if (el.btnFecharAtendimentoClinicoRodape) {
            el.btnFecharAtendimentoClinicoRodape.addEventListener("click", fecharModalAtendimentoClinico);
        }

        if (el.btnAbrirHistoricoPet) {
            el.btnAbrirHistoricoPet.addEventListener("click", async () => {
                await abrirHistoricoPet();
            });
        }

        if (el.btnFecharHistoricoDrawer) {
            el.btnFecharHistoricoDrawer.addEventListener("click", () => {
                state.historicoAberto = false;
                renderHistoricoVazio(
                    "Histórico recolhido.",
                    "Clique novamente em Histórico do Pet para consultar os atendimentos anteriores."
                );
            });
        }

        if (el.btnSalvarRascunhoClinico) {
            el.btnSalvarRascunhoClinico.addEventListener("click", salvarAtendimentoClinico);
        }

        if (el.filtroBuscaAgenda) {
            el.filtroBuscaAgenda.addEventListener("input", renderAgenda);
        }

        document.addEventListener("click", (event) => {
            const btnIniciar = event.target.closest("[data-action='iniciar-atendimento']");
            if (btnIniciar) {
                const agendamentoId = Number(btnIniciar.dataset.agendamentoId);
                const status = String(btnIniciar.dataset.status || "").trim();

                if (agendamentoEstaFinalizado(status)) {
                    showToast("Este atendimento veterinário já foi salvo e finalizado.", "error");
                    return;
                }

                iniciarAtendimento(agendamentoId);
                return;
            }

            const btnVerHistorico = event.target.closest("[data-action='historico-rapido']");
            if (btnVerHistorico) {
                const petId = Number(btnVerHistorico.dataset.petId);
                abrirHistoricoPetPorId(petId);
                return;
            }

            const btnRemoverServico = event.target.closest("[data-action='remover-servico-vet']");
            if (btnRemoverServico) {
                const servicoId = Number(btnRemoverServico.dataset.servicoId);
                removerServicoVetSelecionado(servicoId);
            }
        });

        [el.modalAgendamentoVetOverlay, el.modalAtendimentoClinicoOverlay].forEach((overlay) => {
            if (!overlay) return;

            overlay.addEventListener("click", (event) => {
                if (event.target === overlay) {
                    overlay.classList.remove("active");
                }
            });
        });
    }

    async function fetchJsonSafe(url, options = {}, defaultErrorMessage = "Erro na requisição.") {
        const response = await fetch(url, options);
        const raw = await response.text();

        let data = null;

        try {
            data = raw ? JSON.parse(raw) : null;
        } catch (error) {
            if (!response.ok) {
                throw new Error(raw || defaultErrorMessage);
            }
            throw new Error(raw || defaultErrorMessage);
        }

        if (!response.ok) {
            throw new Error(data?.detail || data?.message || raw || defaultErrorMessage);
        }

        return data;
    }

    async function carregarAgendaSemana() {
        try {
            const data = await fetchJsonSafe(
                `/api/agenda-veterinaria/semana?data_ref=${state.dataRef}`,
                {},
                "Erro ao carregar agenda veterinária."
            );

            state.agenda = Array.isArray(data.agendamentos) ? data.agendamentos : [];
            state.dias = Array.isArray(data.dias) ? data.dias : [];

            if (el.periodoSemanaLabel) {
                el.periodoSemanaLabel.textContent = `${data.periodo.inicio_label} até ${data.periodo.fim_label}`;
            }

            renderAgenda();
        } catch (error) {
            console.error(error);
            renderErroAgenda(error.message || "Erro ao carregar agenda.");
        }
    }

    function renderAgenda() {
        if (!el.agendaVetGrid) return;

        const termo = (el.filtroBuscaAgenda?.value || "").trim().toLowerCase();

        const html = state.dias
            .map((dia) => {
                const cardsDia = state.agenda
                    .filter((item) => item.data_agendamento && item.data_agendamento.startsWith(dia.data))
                    .filter((item) => filtraAgenda(item, termo))
                    .sort((a, b) => new Date(a.data_agendamento) - new Date(b.data_agendamento))
                    .map(renderCardAgendamento)
                    .join("");

                return `
                    <section class="agenda-vet-day">
                        <header class="agenda-vet-day-header">
                            <h3>${escapeHtml(dia.dia_semana || "")} ${escapeHtml(dia.label || "")}</h3>
                        </header>

                        <div class="agenda-vet-day-body">
                            ${
                                cardsDia ||
                                `
                                <div class="empty-state">
                                    <h4>Sem atendimentos</h4>
                                    <p>Nenhum agendamento veterinário para este dia.</p>
                                </div>
                            `
                            }
                        </div>
                    </section>
                `;
            })
            .join("");

        el.agendaVetGrid.innerHTML =
            html ||
            `
            <div class="empty-state">
                <h3>Nenhum dado encontrado</h3>
                <p>Não foi possível montar a agenda veterinária.</p>
            </div>
        `;
    }

    function filtraAgenda(item, termo) {
        if (!termo) return true;

        const base = [
            item?.cliente?.nome || "",
            item?.pet?.nome || "",
            item?.funcionario?.nome || "",
            ...(item?.servicos || []).map((s) => s.nome || ""),
            item?.status || "",
            item?.prioridade || "",
        ]
            .join(" ")
            .toLowerCase();

        return base.includes(termo);
    }

    function renderCardAgendamento(item) {
        const dataHora = item.data_agendamento ? formatDateTime(item.data_agendamento) : "-";
        const servicos = Array.isArray(item.servicos) ? item.servicos : [];
        const status = String(item.status || "AGUARDANDO");
        const finalizado = agendamentoEstaFinalizado(status);

        const cardStyle = finalizado
            ? 'style="background: linear-gradient(135deg, #14532d 0%, #166534 100%); color: #ffffff; border: 1px solid #14532d; box-shadow: 0 12px 26px rgba(20, 83, 45, 0.28);"'
            : "";

        const textStyle = finalizado ? 'style="color: #ffffff;"' : "";
        const strongStyle = finalizado ? 'style="color: #ffffff;"' : "";
        const badgeStyle = finalizado
            ? 'style="background: rgba(255,255,255,0.18); color: #ffffff; border: 1px solid rgba(255,255,255,0.18);"'
            : "";

        return `
            <article class="agenda-vet-card ${finalizado ? "status-finalizado" : ""}" ${cardStyle}>
                <div class="agenda-vet-card-top">
                    <h4 ${textStyle}>${escapeHtml(item.pet?.nome || "Pet não informado")}</h4>
                    <span class="status-badge" ${badgeStyle}>${escapeHtml(status)}</span>
                </div>

                <p ${textStyle}><strong ${strongStyle}>Tutor:</strong> ${escapeHtml(item.cliente?.nome || "Tutor não informado")}</p>
                <p ${textStyle}><strong ${strongStyle}>Horário:</strong> ${escapeHtml(dataHora)}</p>
                <p ${textStyle}><strong ${strongStyle}>Responsável:</strong> ${escapeHtml(item.funcionario?.nome || "Não definido")}</p>
                <p ${textStyle}><strong ${strongStyle}>Prioridade:</strong> ${escapeHtml(item.prioridade || "NORMAL")}</p>

                <div class="agenda-vet-servicos">
                    <strong ${strongStyle}>Serviços:</strong>
                    <div class="tag-list">
                        ${
                            servicos.length
                                ? servicos
                                      .map((servico) => {
                                          if (finalizado) {
                                              return `<span class="tag" style="background: rgba(255,255,255,0.16); border: 1px solid rgba(255,255,255,0.18); color: #ffffff;">${escapeHtml(servico.nome || "")}</span>`;
                                          }
                                          return `<span class="tag">${escapeHtml(servico.nome || "")}</span>`;
                                      })
                                      .join("")
                                : finalizado
                                    ? `<span class="tag" style="background: rgba(255,255,255,0.16); border: 1px solid rgba(255,255,255,0.18); color: #ffffff;">Sem serviços</span>`
                                    : `<span class="tag">Sem serviços</span>`
                        }
                    </div>
                </div>

                ${
                    item.observacoes
                        ? `
                    <p ${textStyle}><strong ${strongStyle}>Observações:</strong> ${escapeHtml(item.observacoes)}</p>
                `
                        : ""
                }

                <div class="agenda-vet-card-actions">
                    ${
                        finalizado
                            ? `
                        <button
                            type="button"
                            class="btn btn-secondary"
                            disabled
                            style="opacity: 1; background: rgba(255,255,255,0.16); color: #ffffff; border: 1px solid rgba(255,255,255,0.18); cursor: not-allowed;"
                        >
                            Atendimento Salvo
                        </button>
                    `
                            : `
                        <button
                            type="button"
                            class="btn btn-primary"
                            data-action="iniciar-atendimento"
                            data-agendamento-id="${Number(item.id || 0)}"
                            data-status="${escapeHtml(status)}"
                        >
                            Iniciar Atendimento
                        </button>
                    `
                    }

                    <button
                        type="button"
                        class="btn ${finalizado ? "btn-secondary" : "btn-secondary"}"
                        data-action="historico-rapido"
                        data-pet-id="${Number(item?.pet?.id || 0)}"
                        ${finalizado ? 'style="background: rgba(255,255,255,0.16); color: #ffffff; border: 1px solid rgba(255,255,255,0.18);"' : ""}
                    >
                        Histórico do Pet
                    </button>
                </div>
            </article>
        `;
    }

    async function carregarClientes() {
        try {
            const data = await fetchJsonSafe(
                "/api/agenda-veterinaria/clientes",
                {},
                "Erro ao carregar clientes."
            );

            state.clientes = Array.isArray(data) ? data : [];
            preencherSelectClientes();
        } catch (error) {
            console.error(error);
        }
    }

    function preencherSelectClientes() {
        if (!el.agVetCliente) return;

        el.agVetCliente.innerHTML = `
            <option value="">Selecione o tutor</option>
            ${state.clientes
                .map(
                    (cliente) => `
                        <option value="${Number(cliente.id || 0)}">
                            ${escapeHtml(cliente.nome || "")}
                        </option>
                    `
                )
                .join("")}
        `;
    }

    async function carregarPets(clienteId = null) {
        try {
            let url = "/api/agenda-veterinaria/pets";
            if (clienteId) {
                url += `?cliente_id=${clienteId}`;
            }

            const data = await fetchJsonSafe(url, {}, "Erro ao carregar pets.");

            state.pets = Array.isArray(data) ? data : [];
            preencherSelectPets();
        } catch (error) {
            console.error(error);
        }
    }

    function preencherSelectPets() {
        if (!el.agVetPet) return;

        el.agVetPet.innerHTML = `
            <option value="">Selecione o pet</option>
            ${state.pets
                .map(
                    (pet) => `
                        <option value="${Number(pet.id || 0)}">
                            ${escapeHtml(pet.nome || "")}
                            ${pet.especie ? ` - ${escapeHtml(pet.especie)}` : ""}
                        </option>
                    `
                )
                .join("")}
        `;
    }

    async function carregarFuncionarios() {
        try {
            const data = await fetchJsonSafe(
                "/api/agenda-veterinaria/funcionarios",
                {},
                "Erro ao carregar funcionários."
            );

            state.funcionarios = Array.isArray(data) ? data : [];
            preencherSelectFuncionarios();
        } catch (error) {
            console.error(error);
        }
    }

    function preencherSelectFuncionarios() {
        if (!el.agVetFuncionario) return;

        el.agVetFuncionario.innerHTML = `
            <option value="">Selecione o responsável</option>
            ${state.funcionarios
                .map(
                    (funcionario) => `
                        <option value="${Number(funcionario.id || 0)}">
                            ${escapeHtml(funcionario.nome || "")}
                            ${funcionario.funcao ? ` • ${escapeHtml(funcionario.funcao)}` : ""}
                        </option>
                    `
                )
                .join("")}
        `;
    }

    async function carregarServicosVeterinarios() {
        try {
            const data = await fetchJsonSafe(
                "/api/agenda-veterinaria/servicos",
                {},
                "Erro ao carregar serviços veterinários."
            );

            state.servicos = Array.isArray(data) ? data : [];
            preencherSelectServicosVet();
        } catch (error) {
            console.error(error);
        }
    }

    function preencherSelectServicosVet() {
        if (!el.agVetServicoSelect) return;

        el.agVetServicoSelect.innerHTML = `
            <option value="">Selecione um serviço veterinário</option>
            ${state.servicos
                .map(
                    (servico) => `
                        <option value="${Number(servico.id || 0)}">
                            ${escapeHtml(servico.nome || "")}
                            ${servico.porte_referencia ? ` • ${escapeHtml(servico.porte_referencia)}` : ""}
                            • ${formatCurrency(servico.valor || 0)}
                        </option>
                    `
                )
                .join("")}
        `;
    }

    function renderServicosSelecionadosVet() {
        if (!el.agVetServicosSelecionados) return;

        if (!state.servicosSelecionados.length) {
            el.agVetServicosSelecionados.innerHTML = `
                <div class="empty-state">
                    <h4>Nenhum serviço selecionado</h4>
                    <p>Adicione ao menos um serviço veterinário para o agendamento.</p>
                </div>
            `;
            return;
        }

        el.agVetServicosSelecionados.innerHTML = state.servicosSelecionados
            .map(
                (servico) => `
                    <div class="selected-service-item">
                        <span>
                            ${escapeHtml(servico.nome || "")}
                            ${servico.porte_referencia ? ` • ${escapeHtml(servico.porte_referencia)}` : ""}
                            • ${formatCurrency(servico.valor || 0)}
                        </span>
                        <button
                            type="button"
                            class="remove-service-btn"
                            data-action="remover-servico-vet"
                            data-servico-id="${Number(servico.id || 0)}"
                        >
                            ✕
                        </button>
                    </div>
                `
            )
            .join("");
    }

    function adicionarServicoVetSelecionado() {
        const servicoId = Number(el.agVetServicoSelect?.value || 0);

        if (!servicoId) {
            showToast("Selecione um serviço veterinário.", "error");
            return;
        }

        const servico = state.servicos.find((item) => Number(item.id) === servicoId);
        if (!servico) {
            showToast("Serviço veterinário não encontrado.", "error");
            return;
        }

        const jaExiste = state.servicosSelecionados.some((item) => Number(item.id) === servicoId);
        if (jaExiste) {
            showToast("Esse serviço já foi adicionado.", "error");
            if (el.agVetServicoSelect) el.agVetServicoSelect.value = "";
            return;
        }

        state.servicosSelecionados.push(servico);
        renderServicosSelecionadosVet();

        if (el.agVetServicoSelect) {
            el.agVetServicoSelect.value = "";
        }
    }

    function removerServicoVetSelecionado(servicoId) {
        state.servicosSelecionados = state.servicosSelecionados.filter(
            (item) => Number(item.id) !== Number(servicoId)
        );
        renderServicosSelecionadosVet();
    }

    function obterServicosSelecionados() {
        return state.servicosSelecionados.map((item) => Number(item.id)).filter(Boolean);
    }

    function abrirModalAgendamentoVet() {
        limparFormularioAgendamentoVet();

        if (el.modalAgendamentoVetOverlay) {
            el.modalAgendamentoVetOverlay.classList.add("active");
        }
    }

    function fecharModalAgendamentoVet() {
        if (!el.modalAgendamentoVetOverlay) return;

        el.modalAgendamentoVetOverlay.classList.remove("active");

        const form = el.modalAgendamentoVetOverlay.querySelector("form");
        if (form) {
            form.reset();
        }
    }

    function limparFormularioAgendamentoVet() {
        if (el.agVetCliente) el.agVetCliente.value = "";
        if (el.agVetPet) el.agVetPet.innerHTML = `<option value="">Selecione o pet</option>`;
        if (el.agVetFuncionario) el.agVetFuncionario.value = "";
        if (el.agVetDataHora) el.agVetDataHora.value = "";
        if (el.agVetPrioridade) el.agVetPrioridade.value = "NORMAL";
        if (el.agVetStatus) el.agVetStatus.value = "AGUARDANDO";
        if (el.agVetObservacoes) el.agVetObservacoes.value = "";
        if (el.agVetServicoSelect) el.agVetServicoSelect.value = "";

        state.servicosSelecionados = [];
        renderServicosSelecionadosVet();
    }

    async function salvarAgendamentoVet() {
        try {
            const servicoIds = obterServicosSelecionados();

            const payload = {
                cliente_id: Number(el.agVetCliente?.value || 0),
                pet_id: Number(el.agVetPet?.value || 0),
                funcionario_id: el.agVetFuncionario?.value ? Number(el.agVetFuncionario.value) : null,
                data_agendamento: el.agVetDataHora?.value || "",
                prioridade: el.agVetPrioridade?.value || "NORMAL",
                status: el.agVetStatus?.value || "AGUARDANDO",
                observacoes: el.agVetObservacoes?.value || "",
                servico_ids: servicoIds,
            };

            if (!payload.cliente_id) throw new Error("Selecione o tutor.");
            if (!payload.pet_id) throw new Error("Selecione o pet.");
            if (!payload.funcionario_id) throw new Error("Selecione o responsável veterinário.");
            if (!payload.data_agendamento) throw new Error("Informe a data/hora.");
            if (!payload.servico_ids.length) {
                throw new Error("Selecione ao menos um serviço veterinário.");
            }

            if (el.btnSalvarAgendamentoVet) {
                el.btnSalvarAgendamentoVet.disabled = true;
            }

            const data = await fetchJsonSafe(
                "/api/agenda-veterinaria/agendamentos",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(payload),
                },
                "Erro ao salvar agendamento."
            );

            fecharModalAgendamentoVet();
            limparFormularioAgendamentoVet();
            await carregarAgendaSemana();
            showToast(data?.message || "Agendamento veterinário salvo com sucesso.");
        } catch (error) {
            console.error(error);
            showToast(error.message || "Erro ao salvar agendamento.", "error");
        } finally {
            if (el.btnSalvarAgendamentoVet) {
                el.btnSalvarAgendamentoVet.disabled = false;
            }
        }
    }

    async function iniciarAtendimento(agendamentoId) {
        try {
            const itemAgenda = state.agenda.find((item) => Number(item.id) === Number(agendamentoId));
            if (itemAgenda && agendamentoEstaFinalizado(itemAgenda.status)) {
                showToast("Este atendimento veterinário já foi salvo e finalizado.", "error");
                return;
            }

            const data = await fetchJsonSafe(
                `/api/agenda-veterinaria/agendamentos/${agendamentoId}/iniciar-atendimento`,
                {
                    method: "POST",
                },
                "Erro ao iniciar atendimento."
            );

            state.agendamentoAtual = data.agendamento || null;
            state.atendimentoClinicoId = null;
            state.atendimentoClinicoModo = "local";

            limparFormularioClinico();
            preencherAtendimentoClinico(state.agendamentoAtual);
            abrirModalAtendimentoClinico();

            renderHistoricoVazio(
                "Histórico pronto para consulta.",
                "Clique em Histórico do Pet para abrir o painel lateral sem perder a anamnese."
            );

            await iniciarAtendimentoClinicoBackend(agendamentoId);
            await carregarHistoricoInicialClinico(agendamentoId);
        } catch (error) {
            console.error(error);
            showToast(error.message || "Erro ao iniciar atendimento.", "error");
        }
    }

    async function iniciarAtendimentoClinicoBackend(agendamentoId) {
        const empresaId = resolveEmpresaId();

        if (!empresaId) {
            restaurarRascunhoClinicoLocal(agendamentoId);
            state.atendimentoClinicoId = null;
            state.atendimentoClinicoModo = "local";
            return;
        }

        try {
            const data = await fetchJsonSafe(
                `/api/clinico/iniciar-por-agendamento/${agendamentoId}?empresa_id=${empresaId}`,
                {
                    method: "POST",
                },
                "Não foi possível iniciar o atendimento clínico no backend."
            );

            state.atendimentoClinicoId = data.id;
            state.atendimentoClinicoModo = "backend";

            await carregarDetalheAtendimentoClinico(data.id);
        } catch (error) {
            console.error(error);

            state.atendimentoClinicoId = null;
            state.atendimentoClinicoModo = "local";

            restaurarRascunhoClinicoLocal(agendamentoId);
        }
    }

    async function carregarDetalheAtendimentoClinico(atendimentoId) {
        try {
            const data = await fetchJsonSafe(
                `/api/clinico/${atendimentoId}`,
                {},
                "Erro ao buscar detalhe do atendimento clínico."
            );

            preencherFormularioClinicoComBackend(data);
        } catch (error) {
            console.error(error);
            restaurarRascunhoClinicoLocal(state.agendamentoAtual?.id);
        }
    }

    async function carregarHistoricoInicialClinico(agendamentoId) {
        if (state.atendimentoClinicoModo === "backend") {
            return;
        }

        restaurarRascunhoClinicoLocal(agendamentoId);
    }

    function preencherFormularioClinicoComBackend(data) {
        const anamnese = data?.anamnese || {};
        const prontuario = data?.prontuario || {};
        const observacoesClinicas = extrairObservacoesClinicas(prontuario.observacoes || "");

        if (el.clinicoQueixaPrincipal) {
            el.clinicoQueixaPrincipal.value = anamnese.queixa_principal || "";
        }

        if (el.clinicoHistoricoAtual) {
            el.clinicoHistoricoAtual.value = anamnese.historico_atual || "";
        }

        if (el.clinicoObservacoesGerais) {
            el.clinicoObservacoesGerais.value =
                observacoesClinicas.observacoes_gerais ||
                anamnese.observacoes ||
                "";
        }

        if (el.clinicoServicosExecutados) {
            el.clinicoServicosExecutados.value = prontuario.conduta || "";
        }

        if (el.clinicoMedicacoes) {
            el.clinicoMedicacoes.value = observacoesClinicas.medicacoes || "";
        }

        if (el.clinicoExames) {
            el.clinicoExames.value =
                observacoesClinicas.exames ||
                prontuario.diagnostico ||
                "";
        }

        if (el.clinicoReceita) {
            el.clinicoReceita.value = observacoesClinicas.receita || "";
        }
    }

    function abrirModalAtendimentoClinico() {
        if (el.modalAtendimentoClinicoOverlay) {
            el.modalAtendimentoClinicoOverlay.classList.add("active");
        }
    }

    function fecharModalAtendimentoClinico() {
        if (el.modalAtendimentoClinicoOverlay) {
            el.modalAtendimentoClinicoOverlay.classList.remove("active");
        }
    }

    function preencherAtendimentoClinico(agendamento) {
        if (!agendamento) return;

        if (el.clinicoTutorNome) {
            el.clinicoTutorNome.textContent = agendamento?.cliente?.nome || "-";
        }

        if (el.clinicoTutorContato) {
            const telefone = agendamento?.cliente?.telefone || "";
            const email = agendamento?.cliente?.email || "";
            el.clinicoTutorContato.textContent = [telefone, email].filter(Boolean).join(" | ") || "-";
        }

        if (el.clinicoPetNome) {
            el.clinicoPetNome.textContent = agendamento?.pet?.nome || "-";
        }

        if (el.clinicoPetResumo) {
            const resumo = [
                agendamento?.pet?.especie || "",
                agendamento?.pet?.raca || "",
                agendamento?.pet?.porte || "",
            ]
                .filter(Boolean)
                .join(" • ");

            el.clinicoPetResumo.textContent = resumo || "-";
        }

        if (el.clinicoServicosPrevistos) {
            el.clinicoServicosPrevistos.innerHTML =
                (agendamento?.servicos || [])
                    .map((servico) => `<span class="tag">${escapeHtml(servico.nome || "")}</span>`)
                    .join("") || `<span class="tag">Nenhum serviço previsto</span>`;
        }
    }

    async function abrirHistoricoPet() {
        if (!state.agendamentoAtual?.pet?.id) {
            showToast("Nenhum pet selecionado no atendimento.", "error");
            return;
        }

        await abrirHistoricoPetPorId(state.agendamentoAtual.pet.id);
    }

    async function abrirHistoricoPetPorId(petId) {
        try {
            renderHistoricoVazio(
                "Carregando histórico...",
                "Buscando consultas anteriores, anamnese, intercorrências e timeline do pet."
            );

            const data = await fetchJsonSafe(
                `/api/pets/${petId}/historico`,
                {},
                "Erro ao carregar histórico do pet."
            );

            state.historicoAberto = true;
            renderHistoricoPet(data);
        } catch (error) {
            console.error(error);
            renderHistoricoVazio(
                "Erro ao carregar histórico",
                error.message || "Não foi possível buscar o histórico do pet."
            );
        }
    }

    function renderHistoricoPet(data) {
        if (!el.clinicoHistoricoConteudo) return;

        const pet = data?.pet || {};
        const consultasVeterinarias = Array.isArray(data?.consultas_veterinarias)
            ? data.consultas_veterinarias
            : [];
        const atendimentosGrooming = Array.isArray(data?.atendimentos_grooming)
            ? data.atendimentos_grooming
            : Array.isArray(data?.atendimentos)
                ? data.atendimentos
                : [];
        const intercorrencias = Array.isArray(data?.intercorrencias_grooming)
            ? data.intercorrencias_grooming
            : Array.isArray(data?.intercorrencias)
                ? data.intercorrencias
                : [];
        const timeline = Array.isArray(data?.timeline_producao) ? data.timeline_producao : [];

        el.clinicoHistoricoConteudo.innerHTML = `
            <section class="historico-section">
                <h4>Resumo do Pet</h4>
                <p><strong>Nome:</strong> ${escapeHtml(pet.nome || "-")}</p>
                <p><strong>Tutor:</strong> ${escapeHtml(pet.tutor || "-")}</p>
                <p><strong>Espécie:</strong> ${escapeHtml(pet.especie || "-")}</p>
                <p><strong>Raça:</strong> ${escapeHtml(pet.raca || "-")}</p>
                <p><strong>Porte:</strong> ${escapeHtml(pet.porte || "-")}</p>
                <p><strong>Sexo:</strong> ${escapeHtml(pet.sexo || "-")}</p>
                <p><strong>Peso:</strong> ${escapeHtml(formatPeso(pet.peso))}</p>
                <p><strong>Temperamento:</strong> ${escapeHtml(pet.temperamento || "-")}</p>
                <p><strong>Observações cadastrais:</strong> ${escapeHtml(pet.observacoes_cadastrais || "-")}</p>
            </section>

            <section class="historico-section">
                <h4>Consultas veterinárias anteriores</h4>
                ${
                    consultasVeterinarias.length
                        ? consultasVeterinarias
                              .map(
                                  (item) => `
                                    <div class="historico-item">
                                        <p><strong>Início:</strong> ${escapeHtml(formatDateTime(item.data_inicio))}</p>
                                        <p><strong>Fim:</strong> ${escapeHtml(formatDateTime(item.data_fim))}</p>
                                        <p><strong>Status:</strong> ${escapeHtml(item.status || "-")}</p>
                                        <p><strong>Veterinário:</strong> ${escapeHtml(item.veterinario || "-")}</p>
                                        <p><strong>Serviços executados:</strong> ${escapeHtml(joinList(item.servicos_executados))}</p>
                                        <p><strong>Observações da recepção:</strong> ${escapeHtml(item.observacoes_recepcao || "-")}</p>
                                        <p><strong>Observações clínicas:</strong> ${escapeHtml(item.observacoes_clinicas || "-")}</p>

                                        <hr>

                                        <p><strong>Anamnese</strong></p>
                                        <p><strong>Queixa principal:</strong> ${escapeHtml(item.anamnese?.queixa_principal || "-")}</p>
                                        <p><strong>Histórico atual:</strong> ${escapeHtml(item.anamnese?.historico_atual || "-")}</p>
                                        <p><strong>Alimentação:</strong> ${escapeHtml(item.anamnese?.alimentacao || "-")}</p>
                                        <p><strong>Alergias:</strong> ${escapeHtml(item.anamnese?.alergias || "-")}</p>
                                        <p><strong>Uso de medicação atual:</strong> ${escapeHtml(item.anamnese?.uso_medicacao_atual || "-")}</p>
                                        <p><strong>Observações da anamnese:</strong> ${escapeHtml(item.anamnese?.observacoes || "-")}</p>

                                        <hr>

                                        <p><strong>Prontuário</strong></p>
                                        <p><strong>Exame físico:</strong> ${escapeHtml(item.prontuario?.exame_fisico || "-")}</p>
                                        <p><strong>Diagnóstico:</strong> ${escapeHtml(item.prontuario?.diagnostico || "-")}</p>
                                        <p><strong>Conduta:</strong> ${escapeHtml(item.prontuario?.conduta || "-")}</p>
                                        <p><strong>Observações do prontuário:</strong> ${escapeHtml(item.prontuario?.observacoes || "-")}</p>
                                        <p><strong>Observações gerais:</strong> ${escapeHtml(item.prontuario?.observacoes_gerais || "-")}</p>
                                        <p><strong>Medicações:</strong> ${escapeHtml(item.prontuario?.medicacoes || "-")}</p>
                                        <p><strong>Exames:</strong> ${escapeHtml(item.prontuario?.exames || "-")}</p>
                                        <p><strong>Receita:</strong> ${escapeHtml(item.prontuario?.receita || "-")}</p>
                                    </div>
                                `
                              )
                              .join("")
                        : `<p>Nenhuma consulta veterinária encontrada no histórico.</p>`
                }
            </section>

            <section class="historico-section">
                <h4>Atendimentos anteriores de banho e tosa</h4>
                ${
                    atendimentosGrooming.length
                        ? atendimentosGrooming
                              .map(
                                  (item) => `
                                    <div class="historico-item">
                                        <p><strong>Data:</strong> ${escapeHtml(formatDateLabel(item.data, item.hora))}</p>
                                        <p><strong>Status:</strong> ${escapeHtml(item.status_final || item.status || "-")}</p>
                                        <p><strong>Funcionário responsável:</strong> ${escapeHtml(item.funcionario_responsavel || "-")}</p>
                                        <p><strong>Serviços:</strong> ${escapeHtml(joinList(item.servicos_executados || item.servicos))}</p>
                                        <p><strong>Intercorrências:</strong> ${escapeHtml(joinList(item.intercorrencias))}</p>
                                        <p><strong>Observações gerais:</strong> ${escapeHtml(item.observacoes_gerais || item.observacoes || "-")}</p>
                                        <p><strong>Observações da produção:</strong> ${escapeHtml(item.observacoes_producao || "-")}</p>
                                        <p><strong>Tempo total:</strong> ${escapeHtml(formatMinutes(item.tempo_total_atendimento_minutos))}</p>
                                    </div>
                                `
                              )
                              .join("")
                        : `<p>Nenhum atendimento de banho e tosa encontrado no histórico.</p>`
                }
            </section>

            <section class="historico-section">
                <h4>Intercorrências de banho e tosa</h4>
                ${
                    intercorrencias.length
                        ? intercorrencias
                              .map(
                                  (item) => `
                                    <div class="historico-item">
                                        <p><strong>Data:</strong> ${escapeHtml(formatDateLabel(item.data, item.hora))}</p>
                                        <p><strong>Funcionário:</strong> ${escapeHtml(item.funcionario || "-")}</p>
                                        <p><strong>Descrição:</strong> ${escapeHtml(item.descricao || item.intercorrencia || "-")}</p>
                                    </div>
                                `
                              )
                              .join("")
                        : `<p>Nenhuma intercorrência registrada.</p>`
                }
            </section>

            <section class="historico-section">
                <h4>Timeline operacional</h4>
                ${
                    timeline.length
                        ? timeline
                              .map(
                                  (item) => `
                                    <div class="historico-item">
                                        <p><strong>Data:</strong> ${escapeHtml(formatDateLabel(item.data, item.hora, item.iniciado_em || item.finalizado_em || item.data_hora))}</p>
                                        <p><strong>Etapa:</strong> ${escapeHtml(item.etapa || "-")}</p>
                                        <p><strong>Status:</strong> ${escapeHtml(item.status || "-")}</p>
                                        <p><strong>Funcionário:</strong> ${escapeHtml(item.funcionario || "-")}</p>
                                        <p><strong>Início:</strong> ${escapeHtml(formatDateTime(item.iniciado_em))}</p>
                                        <p><strong>Fim:</strong> ${escapeHtml(formatDateTime(item.finalizado_em))}</p>
                                        <p><strong>Intercorrência:</strong> ${escapeHtml(item.intercorrencia || "-")}</p>
                                        <p><strong>Observação:</strong> ${escapeHtml(item.observacoes || item.observacao || "-")}</p>
                                        <p><strong>Tempo gasto:</strong> ${escapeHtml(formatMinutes(item.tempo_gasto_minutos))}</p>
                                    </div>
                                `
                              )
                              .join("")
                        : `<p>Nenhum histórico operacional encontrado.</p>`
                }
            </section>
        `;
    }

    function renderHistoricoVazio(titulo, descricao) {
        if (!el.clinicoHistoricoConteudo) return;

        el.clinicoHistoricoConteudo.innerHTML = `
            <div class="empty-state">
                <h4>${escapeHtml(titulo || "Sem histórico")}</h4>
                <p>${escapeHtml(descricao || "Nenhuma informação disponível.")}</p>
            </div>
        `;
    }

    async function salvarAtendimentoClinico() {
        try {
            salvarRascunhoClinicoLocal();

            if (!state.agendamentoAtual?.id) {
                showToast("Nenhum agendamento clínico aberto.", "error");
                return;
            }

            if (!state.atendimentoClinicoId) {
                showToast("Rascunho clínico salvo localmente.");
                return;
            }

            const observacoesClinicasSerializadas = serializarObservacoesClinicas();

            const payloadAnamnese = {
                queixa_principal: el.clinicoQueixaPrincipal?.value || "",
                historico_atual: el.clinicoHistoricoAtual?.value || "",
                observacoes: el.clinicoObservacoesGerais?.value || "",
            };

            const payloadProntuario = {
                conduta: el.clinicoServicosExecutados?.value || "",
                diagnostico: el.clinicoExames?.value || "",
                observacoes: observacoesClinicasSerializadas,
            };

            const [dataAnamnese, dataProntuario] = await Promise.all([
                fetchJsonSafe(
                    `/api/clinico/${state.atendimentoClinicoId}/anamnese`,
                    {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payloadAnamnese),
                    },
                    "Erro ao salvar anamnese."
                ),
                fetchJsonSafe(
                    `/api/clinico/${state.atendimentoClinicoId}/prontuario`,
                    {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payloadProntuario),
                    },
                    "Erro ao salvar prontuário."
                ),
            ]);

            if (!dataAnamnese) {
                throw new Error("Erro ao salvar anamnese.");
            }

            if (!dataProntuario) {
                throw new Error("Erro ao salvar prontuário.");
            }

            await fetchJsonSafe(
                `/api/clinico/${state.atendimentoClinicoId}/finalizar`,
                { method: "POST" },
                "Erro ao finalizar atendimento clínico."
            );

            await fetchJsonSafe(
                `/api/agenda-veterinaria/agendamentos/${state.agendamentoAtual.id}/finalizar`,
                { method: "POST" },
                "Erro ao finalizar agendamento veterinário."
            );

            if (state.agendamentoAtual) {
                state.agendamentoAtual.status = "FINALIZADO";
            }

            await carregarAgendaSemana();
            await abrirHistoricoPetPorId(state.agendamentoAtual.pet.id);

            fecharModalAtendimentoClinico();
            showToast("Atendimento clínico salvo e finalizado com sucesso.");
        } catch (error) {
            console.error(error);
            showToast(error.message || "Erro ao salvar atendimento clínico.", "error");
        }
    }

    function salvarRascunhoClinicoLocal() {
        try {
            if (!state.agendamentoAtual?.id) {
                return;
            }

            const payload = coletarFormularioClinico();
            const chave = getClinicoStorageKey(state.agendamentoAtual.id);

            localStorage.setItem(chave, JSON.stringify(payload));
        } catch (error) {
            console.error(error);
        }
    }

    function restaurarRascunhoClinicoLocal(agendamentoId) {
        limparFormularioClinico();

        try {
            const chave = getClinicoStorageKey(agendamentoId);
            const bruto = localStorage.getItem(chave);

            if (!bruto) return;

            const data = JSON.parse(bruto);

            if (el.clinicoQueixaPrincipal) el.clinicoQueixaPrincipal.value = data.queixa_principal || "";
            if (el.clinicoHistoricoAtual) el.clinicoHistoricoAtual.value = data.historico_atual || "";
            if (el.clinicoObservacoesGerais) el.clinicoObservacoesGerais.value = data.observacoes_gerais || "";
            if (el.clinicoServicosExecutados) el.clinicoServicosExecutados.value = data.servicos_executados || "";
            if (el.clinicoMedicacoes) el.clinicoMedicacoes.value = data.medicacoes || "";
            if (el.clinicoExames) el.clinicoExames.value = data.exames || "";
            if (el.clinicoReceita) el.clinicoReceita.value = data.receita || "";
        } catch (error) {
            console.error(error);
        }
    }

    function limparFormularioClinico() {
        if (el.clinicoQueixaPrincipal) el.clinicoQueixaPrincipal.value = "";
        if (el.clinicoHistoricoAtual) el.clinicoHistoricoAtual.value = "";
        if (el.clinicoObservacoesGerais) el.clinicoObservacoesGerais.value = "";
        if (el.clinicoServicosExecutados) el.clinicoServicosExecutados.value = "";
        if (el.clinicoMedicacoes) el.clinicoMedicacoes.value = "";
        if (el.clinicoExames) el.clinicoExames.value = "";
        if (el.clinicoReceita) el.clinicoReceita.value = "";
    }

    function coletarFormularioClinico() {
        return {
            queixa_principal: el.clinicoQueixaPrincipal?.value || "",
            historico_atual: el.clinicoHistoricoAtual?.value || "",
            observacoes_gerais: el.clinicoObservacoesGerais?.value || "",
            servicos_executados: el.clinicoServicosExecutados?.value || "",
            medicacoes: el.clinicoMedicacoes?.value || "",
            exames: el.clinicoExames?.value || "",
            receita: el.clinicoReceita?.value || "",
        };
    }

    function serializarObservacoesClinicas() {
        const observacoesGerais = (el.clinicoObservacoesGerais?.value || "").trim();
        const medicacoes = (el.clinicoMedicacoes?.value || "").trim();
        const exames = (el.clinicoExames?.value || "").trim();
        const receita = (el.clinicoReceita?.value || "").trim();

        return [
            "[OBSERVACOES_GERAIS]",
            observacoesGerais,
            "",
            "[MEDICACOES]",
            medicacoes,
            "",
            "[EXAMES]",
            exames,
            "",
            "[RECEITA]",
            receita,
        ].join("\n");
    }

    function extrairObservacoesClinicas(texto) {
        const bruto = String(texto || "");

        if (!bruto.includes("[OBSERVACOES_GERAIS]")) {
            return {
                observacoes_gerais: bruto.trim(),
                medicacoes: "",
                exames: "",
                receita: "",
            };
        }

        return {
            observacoes_gerais: extrairBlocoObservacao(bruto, "OBSERVACOES_GERAIS"),
            medicacoes: extrairBlocoObservacao(bruto, "MEDICACOES"),
            exames: extrairBlocoObservacao(bruto, "EXAMES"),
            receita: extrairBlocoObservacao(bruto, "RECEITA"),
        };
    }

    function extrairBlocoObservacao(texto, chave) {
        const regex = new RegExp(`\\[${chave}\\]\\n?([\\s\\S]*?)(?=\\n\\[[A-Z_]+\\]|$)`, "i");
        const match = String(texto || "").match(regex);
        return match?.[1]?.trim() || "";
    }

    function resolveEmpresaId() {
        const candidates = [
            window.APP_EMPRESA_ID,
            window.empresaId,
            localStorage.getItem("empresa_id"),
            localStorage.getItem("petflow_empresa_id"),
            sessionStorage.getItem("empresa_id"),
            sessionStorage.getItem("petflow_empresa_id"),
            1,
        ];

        for (const value of candidates) {
            const numero = Number(value);
            if (Number.isInteger(numero) && numero > 0) {
                return numero;
            }
        }

        return null;
    }

    function renderErroAgenda(message) {
        if (!el.agendaVetGrid) return;

        el.agendaVetGrid.innerHTML = `
            <div class="empty-state error-state">
                <h3>Erro ao carregar agenda veterinária</h3>
                <p>${escapeHtml(message || "Falha inesperada.")}</p>
            </div>
        `;
    }

    function agendamentoEstaFinalizado(status) {
        const normalizado = String(status || "").trim().toUpperCase();
        return normalizado === "FINALIZADO" || normalizado === "SALVO";
    }

    function formatDateTime(value) {
        if (!value) return "-";

        const date = new Date(value);
        if (isNaN(date.getTime())) return String(value);

        return date.toLocaleString("pt-BR", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    }

    function formatDateLabel(dateValue, timeValue = null, fallbackDateTime = null) {
        if (dateValue) {
            const data = String(dateValue);
            const hora = timeValue ? String(timeValue).slice(0, 5) : "";

            if (data.includes("-")) {
                const [ano, mes, dia] = data.split("-");
                return hora ? `${dia}/${mes}/${ano} ${hora}` : `${dia}/${mes}/${ano}`;
            }

            return hora ? `${data} ${hora}` : data;
        }

        if (fallbackDateTime) {
            return formatDateTime(fallbackDateTime);
        }

        return "-";
    }

    function formatMinutes(value) {
        if (value === null || value === undefined || value === "") return "-";

        const total = Number(value);
        if (!Number.isFinite(total)) return String(value);

        if (total < 60) return `${total} min`;

        const horas = Math.floor(total / 60);
        const minutos = total % 60;

        return minutos ? `${horas}h ${minutos}min` : `${horas}h`;
    }

    function joinList(list) {
        if (!Array.isArray(list) || !list.length) return "-";

        const itens = list
            .map((item) => {
                if (item === null || item === undefined) return "";
                if (typeof item === "string") return item.trim();
                if (typeof item === "object" && item.nome) return String(item.nome).trim();
                return String(item).trim();
            })
            .filter(Boolean);

        return itens.length ? itens.join(", ") : "-";
    }

    function formatPeso(value) {
        if (value === null || value === undefined || value === "") return "-";
        return `${String(value)} kg`;
    }

    function formatCurrency(value) {
        return Number(value || 0).toLocaleString("pt-BR", {
            style: "currency",
            currency: "BRL",
        });
    }

    function getTodayISO() {
        const now = new Date();
        const offset = now.getTimezoneOffset();
        const localDate = new Date(now.getTime() - offset * 60000);
        return localDate.toISOString().slice(0, 10);
    }

    function addDays(isoDate, days) {
        const date = new Date(`${isoDate}T00:00:00`);
        date.setDate(date.getDate() + days);

        const offset = date.getTimezoneOffset();
        const localDate = new Date(date.getTime() - offset * 60000);

        return localDate.toISOString().slice(0, 10);
    }

    function getClinicoStorageKey(agendamentoId) {
        return `petflow_clinico_draft_${agendamentoId}`;
    }

    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#39;");
    }

    function showToast(message, type = "success") {
        if (window.showToast && typeof window.showToast === "function" && window.showToast !== showToast) {
            window.showToast(message, type);
            return;
        }

        console.log(message);
    }
})();