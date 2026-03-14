(function () {
    const state = {
        dataRef: getTodayISO(),
        agenda: [],
        dias: [],
        clientes: [],
        pets: [],
        funcionarios: [],
        servicos: [],
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
        agVetServicosChecklist: document.getElementById("agVetServicosChecklist"),
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
                iniciarAtendimento(agendamentoId);
                return;
            }

            const btnVerHistorico = event.target.closest("[data-action='historico-rapido']");
            if (btnVerHistorico) {
                const petId = Number(btnVerHistorico.dataset.petId);
                abrirHistoricoPetPorId(petId);
                return;
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
            throw new Error(
                data?.detail ||
                data?.message ||
                raw ||
                defaultErrorMessage
            );
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

        const html = state.dias.map((dia) => {
            const cardsDia = state.agenda
                .filter((item) => item.data_agendamento && item.data_agendamento.startsWith(dia.data))
                .filter((item) => filtraAgenda(item, termo))
                .sort((a, b) => new Date(a.data_agendamento) - new Date(b.data_agendamento))
                .map(renderCardAgendamento)
                .join("");

            return `
                <div class="agenda-dia-coluna premium-glass">
                    <div class="agenda-dia-header">
                        <strong>${dia.dia_semana}</strong>
                        <span>${dia.label}</span>
                    </div>

                    ${cardsDia || `
                        <div class="empty-state small">
                            <h4>Sem atendimentos</h4>
                            <p>Nenhum agendamento veterinário para este dia.</p>
                        </div>
                    `}
                </div>
            `;
        }).join("");

        el.agendaVetGrid.innerHTML = html || `
            <div class="premium-glass empty-state">
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
        ].join(" ").toLowerCase();

        return base.includes(termo);
    }

    function renderCardAgendamento(item) {
        const dataHora = item.data_agendamento ? formatDateTime(item.data_agendamento) : "-";
        const servicos = Array.isArray(item.servicos) ? item.servicos : [];

        return `
            <div class="agenda-card-vet" data-agendamento-id="${item.id}">
                <div class="agenda-card-top">
                    <div>
                        <h4>${escapeHtml(item.pet?.nome || "Pet não informado")}</h4>
                        <p class="agenda-card-subtitle">${escapeHtml(item.cliente?.nome || "Tutor não informado")}</p>
                    </div>
                    <span class="status-badge">${escapeHtml(item.status || "AGUARDANDO")}</span>
                </div>

                <div class="agenda-card-meta">
                    <div><strong>Horário:</strong> ${dataHora}</div>
                    <div><strong>Veterinário:</strong> ${escapeHtml(item.funcionario?.nome || "Não definido")}</div>
                    <div><strong>Prioridade:</strong> <span class="priority-badge">${escapeHtml(item.prioridade || "NORMAL")}</span></div>
                </div>

                <div class="badge-list">
                    ${servicos.map((servico) => `<span class="service-badge">${escapeHtml(servico.nome || "")}</span>`).join("")}
                </div>

                ${item.observacoes ? `
                    <div class="agenda-card-meta">
                        <div><strong>Observações:</strong> ${escapeHtml(item.observacoes)}</div>
                    </div>
                ` : ""}

                <div class="agenda-card-actions">
                    <button class="btn btn-primary" type="button" data-action="iniciar-atendimento" data-agendamento-id="${item.id}">
                        Iniciar Atendimento
                    </button>
                    <button class="btn btn-outline" type="button" data-action="historico-rapido" data-pet-id="${item.pet?.id || ""}">
                        Histórico do Pet
                    </button>
                </div>
            </div>
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
            ${state.clientes.map((cliente) => `
                <option value="${cliente.id}">${escapeHtml(cliente.nome || "")}</option>
            `).join("")}
        `;
    }

    async function carregarPets(clienteId = null) {
        try {
            let url = "/api/agenda-veterinaria/pets";
            if (clienteId) {
                url += `?cliente_id=${clienteId}`;
            }

            const data = await fetchJsonSafe(
                url,
                {},
                "Erro ao carregar pets."
            );

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
            ${state.pets.map((pet) => `
                <option value="${pet.id}">
                    ${escapeHtml(pet.nome || "")} ${pet.especie ? `- ${escapeHtml(pet.especie)}` : ""}
                </option>
            `).join("")}
        `;
    }

    async function carregarFuncionarios() {
        try {
            const data = await fetchJsonSafe(
                "/api/agenda-veterinaria/funcionarios",
                {},
                "Erro ao carregar veterinários."
            );

            state.funcionarios = Array.isArray(data) ? data : [];
            preencherSelectFuncionarios();
        } catch (error) {
            console.error(error);
        }
    }

    function preencherSelectFuncionarios() {
        if (!el.agVetFuncionario) return;

        if (!state.funcionarios.length) {
            el.agVetFuncionario.innerHTML = `<option value="">Nenhum veterinário disponível</option>`;
            return;
        }

        el.agVetFuncionario.innerHTML = `
            <option value="">Selecione o veterinário</option>
            ${state.funcionarios.map((funcionario) => `
                <option value="${funcionario.id}">
                    ${escapeHtml(funcionario.nome || "")}${funcionario.funcao ? ` - ${escapeHtml(funcionario.funcao)}` : ""}
                </option>
            `).join("")}
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
            preencherChecklistServicos();
        } catch (error) {
            console.error(error);
        }
    }

    function preencherChecklistServicos() {
        if (!el.agVetServicosChecklist) return;

        if (!state.servicos.length) {
            el.agVetServicosChecklist.innerHTML = `
                <div class="empty-state small">
                    <h4>Sem serviços veterinários</h4>
                    <p>Cadastre ou ajuste serviços com tipo VETERINARIO.</p>
                </div>
            `;
            return;
        }

        el.agVetServicosChecklist.innerHTML = state.servicos.map((servico) => `
            <label class="servico-check-item">
                <input type="checkbox" name="agVetServico" value="${servico.id}">
                <div class="servico-check-info">
                    <strong>${escapeHtml(servico.nome || "")}</strong>
                    <span>${escapeHtml(servico.porte_referencia || "-")} | ${formatCurrency(servico.valor || 0)}</span>
                </div>
            </label>
        `).join("");
    }

    function obterServicosSelecionados() {
        if (!el.agVetServicosChecklist) return [];

        return Array.from(
            el.agVetServicosChecklist.querySelectorAll("input[name='agVetServico']:checked")
        ).map((input) => Number(input.value));
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

        if (el.agVetServicosChecklist) {
            el.agVetServicosChecklist
                .querySelectorAll("input[name='agVetServico']")
                .forEach((input) => {
                    input.checked = false;
                });
        }
    }

    async function salvarAgendamentoVet() {
        try {
            const servicoIds = obterServicosSelecionados();

            const payload = {
                cliente_id: Number(el.agVetCliente.value || 0),
                pet_id: Number(el.agVetPet.value || 0),
                funcionario_id: el.agVetFuncionario.value ? Number(el.agVetFuncionario.value) : null,
                data_agendamento: el.agVetDataHora.value,
                prioridade: el.agVetPrioridade.value,
                status: el.agVetStatus.value,
                observacoes: el.agVetObservacoes.value || "",
                servico_ids: servicoIds,
            };

            if (!payload.cliente_id) throw new Error("Selecione o tutor.");
            if (!payload.pet_id) throw new Error("Selecione o pet.");
            if (!payload.funcionario_id) throw new Error("Selecione o veterinário.");
            if (!payload.data_agendamento) throw new Error("Informe a data/hora.");
            if (!payload.servico_ids.length) throw new Error("Selecione ao menos um serviço veterinário.");

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
            alert(error.message || "Erro ao salvar agendamento.");
        } finally {
            if (el.btnSalvarAgendamentoVet) {
                el.btnSalvarAgendamentoVet.disabled = false;
            }
        }
    }

    async function iniciarAtendimento(agendamentoId) {
        try {
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
            alert(error.message || "Erro ao iniciar atendimento.");
        }
    }

    async function iniciarAtendimentoClinicoBackend(agendamentoId) {
        const empresaId = resolveEmpresaId();

        if (!empresaId) {
            restaurarRascunhoClinicoLocal(agendamentoId);
            showToast("Atendimento aberto em modo local. Empresa não identificada para persistência clínica.");
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
            showToast("Atendimento clínico iniciado.");
        } catch (error) {
            console.error(error);
            state.atendimentoClinicoId = null;
            state.atendimentoClinicoModo = "local";
            restaurarRascunhoClinicoLocal(agendamentoId);
            showToast("Atendimento aberto em modo local. A persistência clínica ainda não foi iniciada no backend.");
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

        if (el.clinicoQueixaPrincipal) {
            el.clinicoQueixaPrincipal.value = anamnese.queixa_principal || "";
        }

        if (el.clinicoHistoricoAtual) {
            el.clinicoHistoricoAtual.value = anamnese.historico_atual || "";
        }

        if (el.clinicoObservacoesGerais) {
            el.clinicoObservacoesGerais.value =
                anamnese.observacoes ||
                prontuario.observacoes ||
                "";
        }

        if (el.clinicoServicosExecutados) {
            el.clinicoServicosExecutados.value = prontuario.conduta || "";
        }

        if (el.clinicoMedicacoes) {
            el.clinicoMedicacoes.value = "";
        }

        if (el.clinicoExames) {
            el.clinicoExames.value = prontuario.diagnostico || "";
        }

        if (el.clinicoReceita) {
            el.clinicoReceita.value = "";
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
            ].filter(Boolean).join(" • ");
            el.clinicoPetResumo.textContent = resumo || "-";
        }

        if (el.clinicoServicosPrevistos) {
            el.clinicoServicosPrevistos.innerHTML = (agendamento?.servicos || []).map((servico) => {
                return `<span class="service-badge">${escapeHtml(servico.nome || "")}</span>`;
            }).join("") || `<span class="muted">Nenhum serviço previsto</span>`;
        }
    }

    async function abrirHistoricoPet() {
        if (!state.agendamentoAtual?.pet?.id) {
            alert("Nenhum pet selecionado no atendimento.");
            return;
        }

        await abrirHistoricoPetPorId(state.agendamentoAtual.pet.id);
    }

    async function abrirHistoricoPetPorId(petId) {
        try {
            renderHistoricoVazio("Carregando histórico...", "Buscando atendimentos, intercorrências e timeline do pet.");

            const data = await fetchJsonSafe(
                `/api/pets/${petId}/historico`,
                {},
                "Erro ao carregar histórico do pet."
            );

            state.historicoAberto = true;
            renderHistoricoPet(data);
        } catch (error) {
            console.error(error);
            renderHistoricoVazio("Erro ao carregar histórico", error.message || "Não foi possível buscar o histórico do pet.");
        }
    }

    function renderHistoricoPet(data) {
        if (!el.clinicoHistoricoConteudo) return;

        const pet = data?.pet || {};
        const atendimentos = Array.isArray(data?.atendimentos) ? data.atendimentos : [];
        const intercorrencias = Array.isArray(data?.intercorrencias) ? data.intercorrencias : [];
        const timeline = Array.isArray(data?.timeline_producao) ? data.timeline_producao : [];

        el.clinicoHistoricoConteudo.innerHTML = `
            <div class="historico-card">
                <h4>Resumo do Pet</h4>
                <div><strong>Nome:</strong> ${escapeHtml(pet.nome || "-")}</div>
                <div><strong>Espécie:</strong> ${escapeHtml(pet.especie || "-")}</div>
                <div><strong>Raça:</strong> ${escapeHtml(pet.raca || "-")}</div>
                <div><strong>Porte:</strong> ${escapeHtml(pet.porte || "-")}</div>
                <div><strong>Sexo:</strong> ${escapeHtml(pet.sexo || "-")}</div>
            </div>

            <div class="historico-card">
                <h4>Atendimentos anteriores</h4>
                <div class="historico-list">
                    ${atendimentos.length ? atendimentos.map((item) => `
                        <div class="historico-timeline-item">
                            <div><strong>Data:</strong> ${escapeHtml(item.data || item.data_agendamento || "-")}</div>
                            <div><strong>Status:</strong> ${escapeHtml(item.status || "-")}</div>
                            <div><strong>Serviços:</strong> ${escapeHtml((item.servicos || []).join(", ") || "-")}</div>
                            <div><strong>Observações:</strong> ${escapeHtml(item.observacoes || "-")}</div>
                        </div>
                    `).join("") : `
                        <div class="muted">Nenhum atendimento encontrado no histórico.</div>
                    `}
                </div>
            </div>

            <div class="historico-card">
                <h4>Intercorrências</h4>
                <div class="historico-list">
                    ${intercorrencias.length ? intercorrencias.map((item) => `
                        <div class="historico-timeline-item">
                            <div><strong>Data:</strong> ${escapeHtml(item.data || "-")}</div>
                            <div><strong>Descrição:</strong> ${escapeHtml(item.descricao || "-")}</div>
                        </div>
                    `).join("") : `
                        <div class="muted">Nenhuma intercorrência registrada.</div>
                    `}
                </div>
            </div>

            <div class="historico-card">
                <h4>Timeline operacional</h4>
                <div class="historico-list">
                    ${timeline.length ? timeline.map((item) => `
                        <div class="historico-timeline-item">
                            <div><strong>Etapa:</strong> ${escapeHtml(item.etapa || "-")}</div>
                            <div><strong>Data/Hora:</strong> ${escapeHtml(item.data_hora || "-")}</div>
                            <div><strong>Observação:</strong> ${escapeHtml(item.observacao || "-")}</div>
                        </div>
                    `).join("") : `
                        <div class="muted">Nenhum histórico operacional encontrado.</div>
                    `}
                </div>
            </div>
        `;
    }

    function renderHistoricoVazio(titulo, descricao) {
        if (!el.clinicoHistoricoConteudo) return;

        el.clinicoHistoricoConteudo.innerHTML = `
            <div class="empty-state small">
                <h4>${escapeHtml(titulo || "Sem histórico")}</h4>
                <p>${escapeHtml(descricao || "Nenhuma informação disponível.")}</p>
            </div>
        `;
    }

    async function salvarAtendimentoClinico() {
        try {
            salvarRascunhoClinicoLocal();

            if (!state.atendimentoClinicoId) {
                showToast("Rascunho clínico salvo localmente.");
                return;
            }

            const payloadAnamnese = {
                queixa_principal: el.clinicoQueixaPrincipal?.value || "",
                historico_atual: el.clinicoHistoricoAtual?.value || "",
                observacoes: el.clinicoObservacoesGerais?.value || "",
            };

            const payloadProntuario = {
                conduta: el.clinicoServicosExecutados?.value || "",
                diagnostico: el.clinicoExames?.value || "",
                observacoes: el.clinicoObservacoesGerais?.value || "",
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

            showToast("Atendimento clínico salvo no sistema.");
        } catch (error) {
            console.error(error);
            alert(error.message || "Erro ao salvar atendimento clínico.");
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
            <div class="premium-glass empty-state">
                <h3>Erro ao carregar agenda veterinária</h3>
                <p>${escapeHtml(message || "Falha inesperada.")}</p>
            </div>
        `;
    }

    function formatDateTime(value) {
        if (!value) return "-";
        const date = new Date(value);
        if (isNaN(date.getTime())) return value;

        return date.toLocaleString("pt-BR", {
            day: "2-digit",
            month: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
        });
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
            .replaceAll("'", "&#039;");
    }

    function showToast(message) {
        if (window.showToast && typeof window.showToast === "function") {
            window.showToast(message);
            return;
        }

        console.log(message);
        alert(message);
    }
})();