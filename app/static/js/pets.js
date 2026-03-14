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
      .replaceAll("'", "&#039;");
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
      historicoBody.innerHTML = `<div class="pet-historico-loading">Carregando histórico...</div>`;
    }
  }

  function abrirConfirmModal({
    title = "Confirmar ação",
    subtitle = "Revise a ação antes de continuar.",
    message = "Deseja continuar?",
    confirmText = "Confirmar",
    onConfirm = null
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
      <div class="pet-resumo-grid">
        <div class="pet-resumo-card">
          <span class="pet-resumo-label">Nome</span>
          <div class="pet-resumo-valor">${escapeHtml(pet.nome)}</div>
        </div>

        <div class="pet-resumo-card">
          <span class="pet-resumo-label">Tutor</span>
          <div class="pet-resumo-valor">${escapeHtml(pet.tutor)}</div>
        </div>

        <div class="pet-resumo-card">
          <span class="pet-resumo-label">Raça</span>
          <div class="pet-resumo-valor">${escapeHtml(pet.raca)}</div>
        </div>

        <div class="pet-resumo-card">
          <span class="pet-resumo-label">Porte</span>
          <div class="pet-resumo-valor">${escapeHtml(pet.porte)}</div>
        </div>

        <div class="pet-resumo-card">
          <span class="pet-resumo-label">Peso</span>
          <div class="pet-resumo-valor">${pet.peso ?? "-"}</div>
        </div>

        <div class="pet-resumo-card">
          <span class="pet-resumo-label">Sexo</span>
          <div class="pet-resumo-valor">${escapeHtml(pet.sexo)}</div>
        </div>

        <div class="pet-resumo-card">
          <span class="pet-resumo-label">Temperamento</span>
          <div class="pet-resumo-valor">${escapeHtml(pet.temperamento)}</div>
        </div>

        <div class="pet-resumo-card">
          <span class="pet-resumo-label">Nascimento</span>
          <div class="pet-resumo-valor">${formatarData(pet.nascimento)}</div>
        </div>

        <div class="pet-resumo-card">
          <span class="pet-resumo-label">Pode perfume</span>
          <div class="pet-resumo-valor">${formatarBooleano(pet.pode_perfume)}</div>
        </div>

        <div class="pet-resumo-card">
          <span class="pet-resumo-label">Pode acessório</span>
          <div class="pet-resumo-valor">${formatarBooleano(pet.pode_acessorio)}</div>
        </div>

        <div class="pet-resumo-card">
          <span class="pet-resumo-label">Castrado</span>
          <div class="pet-resumo-valor">${formatarBooleano(pet.castrado)}</div>
        </div>

        <div class="pet-resumo-card">
          <span class="pet-resumo-label">Status do cadastro</span>
          <div class="pet-resumo-valor">${pet.ativo ? "Ativo" : "Inativo"}</div>
        </div>

        <div class="pet-resumo-card full">
          <span class="pet-resumo-label">Observações cadastrais</span>
          <div class="pet-resumo-valor">${escapeHtml(pet.observacoes_cadastrais)}</div>
        </div>
      </div>
    `;
  }

  function renderizarTimeline(timeline) {
    if (!timeline || !timeline.length) {
      return `<div class="pet-historico-empty">Nenhum histórico operacional encontrado para este atendimento.</div>`;
    }

    return `
      <div class="pet-timeline">
        ${timeline.map((item) => `
          <div class="pet-timeline-item">
            <div class="pet-timeline-marker-wrap">
              <div class="pet-timeline-marker"></div>
            </div>

            <div class="pet-timeline-content">
              <div class="pet-timeline-titulo">
                <strong>${escapeHtml(item.etapa)}</strong>
                <span class="pet-timeline-status">${escapeHtml(item.status)}</span>
              </div>

              <div class="pet-timeline-detalhes">
                <div>
                  <span>Iniciado em</span>
                  ${formatarDataHora(item.iniciado_em)}
                </div>

                <div>
                  <span>Finalizado em</span>
                  ${formatarDataHora(item.finalizado_em)}
                </div>

                <div>
                  <span>Funcionário</span>
                  ${escapeHtml(item.funcionario)}
                </div>

                <div>
                  <span>Tempo gasto</span>
                  ${item.tempo_gasto_minutos ?? "-"} min
                </div>

                <div>
                  <span>Intercorrência</span>
                  ${escapeHtml(item.intercorrencia)}
                </div>

                <div>
                  <span>Observações</span>
                  ${escapeHtml(item.observacoes)}
                </div>
              </div>
            </div>
          </div>
        `).join("")}
      </div>
    `;
  }

  function renderizarAtendimentos(atendimentos) {
    if (!atendimentos || !atendimentos.length) {
      return `<div class="pet-historico-empty">Este pet ainda não possui atendimentos registrados.</div>`;
    }

    return `
      <h3 class="pet-section-title">Histórico de Atendimentos</h3>

      <div class="pet-atendimentos-lista">
        ${atendimentos.map((item) => `
          <div class="pet-atendimento-card">
            <div class="pet-atendimento-topo">
              <div>
                <h4>${formatarData(item.data)} às ${formatarHora(item.hora)}</h4>

                <div class="pet-atendimento-meta">
                  <span class="pet-chip">${escapeHtml(item.status_final)}</span>
                  <span class="pet-chip ok">${escapeHtml(item.funcionario_responsavel)}</span>
                  <span class="pet-chip roxo">${formatarLista(item.servicos_executados)}</span>
                  ${
                    item.teve_intercorrencia
                      ? `<span class="pet-chip warn">Com intercorrência</span>`
                      : `<span class="pet-chip ok">Sem intercorrência</span>`
                  }
                </div>
              </div>

              <div class="pet-chip">
                Tempo total: ${item.tempo_total_atendimento_minutos ?? "-"} min
              </div>
            </div>

            <div class="pet-atendimento-conteudo">
              <div class="pet-info-grid">
                <div class="pet-info-box">
                  <span class="label">Serviços executados</span>
                  <div class="value">${formatarLista(item.servicos_executados)}</div>
                </div>

                <div class="pet-info-box">
                  <span class="label">Funcionário responsável</span>
                  <div class="value">${escapeHtml(item.funcionario_responsavel)}</div>
                </div>

                <div class="pet-info-box">
                  <span class="label">Status final</span>
                  <div class="value">${escapeHtml(item.status_final)}</div>
                </div>

                <div class="pet-info-box">
                  <span class="label">Intercorrências</span>
                  <div class="value">${formatarLista(item.intercorrencias)}</div>
                </div>

                <div class="pet-info-box">
                  <span class="label">Observações gerais</span>
                  <div class="value">${escapeHtml(item.observacoes_gerais)}</div>
                </div>

                <div class="pet-info-box">
                  <span class="label">Observações da produção</span>
                  <div class="value">${escapeHtml(item.observacoes_producao)}</div>
                </div>
              </div>

              ${renderizarTimeline(item.timeline)}
            </div>
          </div>
        `).join("")}
      </div>
    `;
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
      historicoBody.innerHTML = `<div class="pet-historico-loading">Carregando histórico...</div>`;
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
          ${renderizarAtendimentos(data.atendimentos)}
        `;
      }
    } catch (error) {
      if (historicoBody) {
        historicoBody.innerHTML = `
          <div class="pet-historico-error">
            ${escapeHtml(error.message || "Erro ao carregar histórico do pet.")}
          </div>
        `;
      }
    }
  }

  async function executarTogglePet(petId, buscaAtual) {
    const response = await fetch(`/api/pets/${petId}/toggle`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json"
      }
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
      message: `
        Deseja realmente <strong>${acao}</strong> o pet
        <strong>"${escapeHtml(nomePet)}"</strong>?
      `,
      confirmText,
      onConfirm: async () => {
        try {
          await executarTogglePet(petId, buscaAtual);
        } catch (error) {
          fecharConfirmModal();
          window.alert(error.message || "Erro ao alterar status do pet.");
        }
      }
    });
  }

  async function carregarPets(q = "") {
    try {
      const response = await fetch(`/api/pets?q=${encodeURIComponent(q)}`);
      const data = await response.json();

      if (!petsTbody) return;

      if (!data.length) {
        petsTbody.innerHTML = `<tr><td colspan="7">Nenhum pet encontrado.</td></tr>`;
        return;
      }

      petsTbody.innerHTML = data.map((pet) => `
        <tr>
          <td>${escapeHtml(pet.nome ?? "-")}</td>
          <td>${escapeHtml(pet.cliente_id ?? "-")}</td>
          <td>${escapeHtml(pet.raca ?? "-")}</td>
          <td>${escapeHtml(pet.sexo ?? "-")}</td>
          <td>${escapeHtml(pet.porte ?? "-")}</td>
          <td>${pet.ativo ? "Ativo" : "Inativo"}</td>
          <td>
            <div class="pet-actions">
              <button
                type="button"
                class="pet-action-btn historico"
                data-pet-id="${pet.id}"
                data-pet-nome="${escapeHtml(pet.nome ?? "")}"
              >
                Histórico
              </button>

              <button
                type="button"
                class="pet-action-btn ${pet.ativo ? "toggle-inativo" : "toggle-ativo"}"
                data-toggle-pet-id="${pet.id}"
                data-toggle-pet-nome="${escapeHtml(pet.nome ?? "")}"
                data-toggle-pet-ativo="${pet.ativo ? "true" : "false"}"
              >
                ${pet.ativo ? "Inativar" : "Ativar"}
              </button>
            </div>
          </td>
        </tr>
      `).join("");

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