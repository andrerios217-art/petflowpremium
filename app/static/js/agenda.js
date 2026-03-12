let semanaAtual = new Date();

let clienteSelecionado = null;
let petSelecionado = null;
let petSelecionadoObj = null;

let servicosSelecionados = [];
let servicosCache = [];
let funcionariosCache = [];
let clientesCache = [];
let petsCache = [];

let agendamentoDetalheAtual = null;
let modoEdicao = false;
let agendamentoEditandoId = null;

let confirmAction = null;
let agendaAutoRefresh = null;

/* =========================================================
   UTIL
========================================================= */

function formatDateISO(date) {
  return date.toISOString().split("T")[0];
}

function startOfWeek(date) {
  const d = new Date(date);
  const day = d.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  d.setDate(d.getDate() + diff);
  d.setHours(0, 0, 0, 0);
  return d;
}

function addDays(date, days) {
  const d = new Date(date);
  d.setDate(d.getDate() + days);
  return d;
}

function normalizarTexto(valor) {
  return String(valor || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function somenteNumeros(valor) {
  return String(valor || "").replace(/\D/g, "");
}

function tokensTexto(valor) {
  return normalizarTexto(valor)
    .split(/\s+/)
    .filter(Boolean);
}

function mostrarMensagemAgenda(texto) {
  const msg = document.getElementById("agenda-message");
  if (msg) msg.innerText = texto;
}

function mostrarMensagemDetalhe(texto) {
  const msg = document.getElementById("detalhe-message");
  if (msg) msg.innerText = texto;
}

function formatarDataBR(data) {
  if (!data) return "-";
  const dt = new Date(`${data}T00:00:00`);
  if (Number.isNaN(dt.getTime())) return data;
  return dt.toLocaleDateString("pt-BR");
}

function formatarHora(valor) {
  return String(valor || "").slice(0, 5);
}

function escapeHtml(valor) {
  return String(valor ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function obterTextoServicos(servicos) {
  if (!Array.isArray(servicos)) return "";

  return servicos
    .map((servico) => {
      if (typeof servico === "string") return servico;
      return servico?.nome || servico?.servico_nome || "";
    })
    .filter(Boolean)
    .join(", ");
}

/* =========================================================
   MODAL CONFIRMAÇÃO PREMIUM
========================================================= */

function abrirConfirmModal({ title, text, confirmText = "Confirmar", onConfirm }) {
  const modal = document.getElementById("confirm-modal");
  const titleEl = document.getElementById("confirm-title");
  const textEl = document.getElementById("confirm-text");
  const okBtn = document.getElementById("confirm-ok");

  if (!modal || !titleEl || !textEl || !okBtn) return;

  titleEl.innerText = title || "Confirmar ação";
  textEl.innerText = text || "Deseja continuar?";
  okBtn.innerText = confirmText;

  confirmAction = onConfirm || null;
  modal.classList.remove("hidden");
}

function fecharConfirmModal() {
  const modal = document.getElementById("confirm-modal");
  if (modal) modal.classList.add("hidden");
  confirmAction = null;
}

async function confirmarAcaoModal() {
  if (typeof confirmAction === "function") {
    const action = confirmAction;
    fecharConfirmModal();
    await action();
    return;
  }
  fecharConfirmModal();
}

/* =========================================================
   STATUS / PRIORIDADE
========================================================= */

function corStatus(item) {
  if (item && item.tem_intercorrencia === true) return "status-intercorrencia";

  const valor = String(item?.status || "").toUpperCase();

  if (valor === "AGUARDANDO") return "status-aguardando";
  if (valor === "EM_ATENDIMENTO") return "status-andamento";
  if (valor === "FINALIZADO") return "status-finalizado";
  if (valor === "FALTA") return "status-falta";
  if (valor === "CANCELADO") return "status-cancelado";
  return "status-aguardando";
}

function textoStatus(status) {
  const valor = String(status || "").toUpperCase();

  if (valor === "AGUARDANDO") return "Aguardando";
  if (valor === "EM_ATENDIMENTO") return "Em atendimento";
  if (valor === "FINALIZADO") return "Finalizado";
  if (valor === "FALTA") return "Falta";
  if (valor === "CANCELADO") return "Cancelado";
  return status || "-";
}

function prioridadeDot(prioridade) {
  const valor = String(prioridade || "").toUpperCase();

  if (valor === "PRIORITARIO" || valor === "PRIORIDADE") return "dot-prioridade";
  if (valor === "SEM_PRIORIDADE") return "dot-sem-prioridade";
  return "dot-normal";
}

/* =========================================================
   AGENDA
========================================================= */

function limparColunas() {
  document.querySelectorAll(".agenda-column-body").forEach((col) => {
    col.innerHTML = "";
  });
}

function montarCabecalhosSemana(inicio) {
  for (let i = 0; i < 6; i++) {
    const dia = addDays(inicio, i);
    const span = document.getElementById(`dia-${i}`);
    if (span) {
      span.innerText = dia.toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "2-digit"
      });
    }
  }
}

function ativarCliqueNasColunas(inicio) {
  const colunas = document.querySelectorAll(".agenda-column");

  colunas.forEach((coluna, index) => {
    coluna.style.cursor = "pointer";

    coluna.onclick = () => {
      if (modoEdicao) return;
      const dia = addDays(inicio, index);
      abrirModal(formatDateISO(dia));
    };
  });
}

function criarCardAgendamento(item) {
  const card = document.createElement("div");
  card.className = `agenda-card ${corStatus(item)}`;
  card.dataset.id = item.id;
  card.style.cursor = "pointer";

  card.addEventListener("click", (e) => {
    e.stopPropagation();
    abrirModalDetalhe(item.id);
  });

  const hora = formatarHora(item.hora);
  const servicos = obterTextoServicos(item.servicos);

  const alertaIntercorrencia = item.tem_intercorrencia
    ? `<div class="agenda-card-alerta">⚠ Intercorrência registrada</div>`
    : "";

  card.innerHTML = `
    <div class="agenda-card-top">
      <span class="agenda-time">${escapeHtml(hora)}</span>
      <span class="agenda-dot ${prioridadeDot(item.prioridade)}"></span>
    </div>

    <div class="agenda-card-title">${escapeHtml(item.pet_nome || "Pet")}</div>

    <div class="agenda-card-subtitle">
      Tutor: ${escapeHtml(item.cliente_nome || "-")}
    </div>

    <div class="agenda-card-servicos">
      ${escapeHtml(servicos)}
    </div>

    <div class="agenda-card-func">
      ${item.funcionario_nome ? "Funcionário: " + escapeHtml(item.funcionario_nome) : ""}
    </div>

    <div class="agenda-card-status">${escapeHtml(textoStatus(item.status))}</div>
    ${alertaIntercorrencia}
  `;

  return card;
}

function atualizarCardNoDOM(item) {
  const cardAntigo = document.querySelector(`.agenda-card[data-id="${item.id}"]`);
  if (!cardAntigo) return;

  const novoCard = criarCardAgendamento(item);
  cardAntigo.replaceWith(novoCard);
}

function removerCardNoDOM(id) {
  const card = document.querySelector(`.agenda-card[data-id="${id}"]`);
  if (card) card.remove();
}

async function carregarAgenda() {
  limparColunas();

  const inicio = startOfWeek(semanaAtual);
  const fim = addDays(inicio, 5);

  const dataBaseInput = document.getElementById("data-base");
  if (dataBaseInput) dataBaseInput.value = formatDateISO(inicio);

  montarCabecalhosSemana(inicio);
  ativarCliqueNasColunas(inicio);

  try {
    const response = await fetch(
      `/api/agenda/semana?empresa_id=1&data_inicio=${formatDateISO(inicio)}&data_fim=${formatDateISO(fim)}`,
      { cache: "no-store" }
    );

    if (!response.ok) {
      console.error("Erro ao carregar agenda");
      return;
    }

    const agendamentos = await response.json();

    agendamentos.forEach((item) => {
      const dataItem = new Date(item.data + "T00:00:00");
      const index = Math.round((dataItem - inicio) / (1000 * 60 * 60 * 24));

      if (index < 0 || index > 5) return;

      const card = criarCardAgendamento(item);
      const coluna = document.getElementById(`col-${index}`);
      if (coluna) coluna.appendChild(card);
    });
  } catch (error) {
    console.error("Erro ao carregar agenda:", error);
  }
}

function iniciarAutoRefreshAgenda() {
  if (agendaAutoRefresh) clearInterval(agendaAutoRefresh);

  agendaAutoRefresh = setInterval(async () => {
    await carregarAgenda();

    if (agendamentoDetalheAtual?.id) {
      try {
        const response = await fetch(`/api/agenda/${agendamentoDetalheAtual.id}`, { cache: "no-store" });
        if (response.ok) {
          const data = await response.json();
          agendamentoDetalheAtual = data;
          renderDetalhe(data);
        }
      } catch (error) {
        console.error("Erro ao atualizar detalhe automaticamente:", error);
      }
    }
  }, 5000);
}

/* =========================================================
   CARGA DE BASE
========================================================= */

async function carregarClientesPetsBase() {
  const [clientesResp, petsResp] = await Promise.all([
    fetch("/api/clientes/"),
    fetch("/api/pets/")
  ]);

  clientesCache = await clientesResp.json();
  petsCache = await petsResp.json();
}

function atualizarSelectServicosPorPet() {
  const select = document.getElementById("servico-select");
  if (!select) return;

  const portePet = String(petSelecionadoObj?.pet_porte || "").toUpperCase();

  select.innerHTML = `<option value="">Selecione um serviço</option>`;

  let servicosFiltrados = servicosCache.filter((servico) => servico.ativo);

  if (portePet) {
    servicosFiltrados = servicosFiltrados.filter((servico) => {
      const porteServico = String(servico.porte_referencia || "").toUpperCase();
      return porteServico === portePet;
    });
  }

  servicosFiltrados.forEach((servico) => {
    const opt = document.createElement("option");
    opt.value = String(servico.id);
    opt.textContent = `${servico.nome} • ${servico.porte_referencia} • ${servico.tempo_minutos} min`;
    select.appendChild(opt);
  });
}

async function carregarServicos() {
  const response = await fetch("/api/servicos/");
  servicosCache = await response.json();
  atualizarSelectServicosPorPet();
}

async function carregarFuncionarios() {
  const response = await fetch("/api/funcionarios/");
  funcionariosCache = await response.json();

  const select = document.getElementById("ag_funcionario");
  if (!select) return;

  select.innerHTML = `<option value="">Selecione</option>`;

  funcionariosCache.forEach((func) => {
    if (func.ativo) {
      const opt = document.createElement("option");
      opt.value = String(func.id);
      opt.textContent = `${func.nome} • ${func.funcao}`;
      select.appendChild(opt);
    }
  });
}

/* =========================================================
   BUSCA INTELIGENTE
========================================================= */

function buscarClientesPets(termo) {
  const resultado = document.getElementById("resultado-busca");
  if (!resultado) return;

  if (modoEdicao) {
    resultado.classList.add("hidden");
    resultado.innerHTML = "";
    return;
  }

  if (!termo || termo.trim().length < 2) {
    resultado.classList.add("hidden");
    resultado.innerHTML = "";
    return;
  }

  const partesTexto = tokensTexto(termo);
  const termoNumero = somenteNumeros(termo);

  const resultados = petsCache
    .map((pet) => {
      const cliente = clientesCache.find((c) => c.id === pet.cliente_id);

      return {
        pet_id: pet.id,
        pet_nome: pet.nome || "",
        pet_raca: pet.raca || "",
        pet_porte: pet.porte || "",
        cliente_id: pet.cliente_id,
        cliente_nome: cliente?.nome || `Cliente #${pet.cliente_id}`,
        cliente_cpf: cliente?.cpf || "",
        cliente_telefone: cliente?.telefone || "",
        cliente_email: cliente?.email || "",
      };
    })
    .filter((item) => {
      const textoAgrupado = normalizarTexto([
        item.pet_nome,
        item.pet_raca,
        item.pet_porte,
        item.cliente_nome,
        item.cliente_email
      ].join(" "));

      const numerosAgrupados = [
        item.cliente_cpf,
        item.cliente_telefone,
        item.pet_id,
        item.cliente_id
      ].map(somenteNumeros).join(" ");

      const matchTexto = partesTexto.every((token) => textoAgrupado.includes(token));
      const matchNumero = termoNumero ? numerosAgrupados.includes(termoNumero) : false;

      return matchTexto || matchNumero;
    });

  if (!resultados.length) {
    resultado.innerHTML = `<div class="search-item">Nenhum pet encontrado para essa busca.</div>`;
    resultado.classList.remove("hidden");
    return;
  }

  resultado.innerHTML = resultados.map((item, index) => `
    <button type="button" class="search-item" data-index="${index}">
      <strong>${escapeHtml(item.pet_nome)}</strong>
      • Tutor: ${escapeHtml(item.cliente_nome)}
      ${item.pet_porte ? `• ${escapeHtml(item.pet_porte)}` : ""}
    </button>
  `).join("");

  resultado.classList.remove("hidden");

  resultado.querySelectorAll(".search-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      const item = resultados[Number(btn.dataset.index)];

      clienteSelecionado = item.cliente_id;
      petSelecionado = item.pet_id;
      petSelecionadoObj = item;

      document.getElementById("cliente_nome").value = item.cliente_nome;
      document.getElementById("pet_nome").value = item.pet_nome;

      atualizarSelectServicosPorPet();

      resultado.classList.add("hidden");
      resultado.innerHTML = "";
    });
  });
}

/* =========================================================
   MODAL NOVO / EDIÇÃO
========================================================= */

function atualizarTituloModal() {
  const titulo = document.querySelector("#agendamento-modal .modal-header h2");
  const subtitulo = document.querySelector("#agendamento-modal .modal-header p");
  const submitBtn = document.querySelector('#agendamento-form button[type="submit"]');

  if (modoEdicao) {
    if (titulo) titulo.innerText = "Editar Agendamento";
    if (subtitulo) subtitulo.innerText = "Atualize data, horário, funcionário, serviços e observações.";
    if (submitBtn) submitBtn.innerText = "Salvar Alterações";
  } else {
    if (titulo) titulo.innerText = "Novo Agendamento";
    if (subtitulo) subtitulo.innerText = "Selecione cliente, pet, serviços e horário.";
    if (submitBtn) submitBtn.innerText = "Salvar Agendamento";
  }
}

function abrirModal(dataPreenchida = null) {
  modoEdicao = false;
  agendamentoEditandoId = null;
  atualizarTituloModal();

  const modal = document.getElementById("agendamento-modal");
  if (!modal) return;

  modal.classList.remove("hidden");

  const busca = document.getElementById("busca-cliente-pet");
  if (busca) {
    busca.disabled = false;
    busca.value = "";
  }

  if (dataPreenchida) {
    const dataInput = document.getElementById("ag_data");
    if (dataInput) dataInput.value = dataPreenchida;
  }

  atualizarSelectServicosPorPet();
}

function fecharModal() {
  const modal = document.getElementById("agendamento-modal");
  if (modal) modal.classList.add("hidden");

  const form = document.getElementById("agendamento-form");
  if (form) form.reset();

  const resultadoBusca = document.getElementById("resultado-busca");
  if (resultadoBusca) {
    resultadoBusca.innerHTML = "";
    resultadoBusca.classList.add("hidden");
  }

  const servicosWrap = document.getElementById("servicos-escolhidos");
  if (servicosWrap) servicosWrap.innerHTML = "";

  mostrarMensagemAgenda("");

  const clienteInput = document.getElementById("cliente_nome");
  const petInput = document.getElementById("pet_nome");
  const busca = document.getElementById("busca-cliente-pet");

  if (clienteInput) clienteInput.value = "";
  if (petInput) petInput.value = "";
  if (busca) {
    busca.value = "";
    busca.disabled = false;
  }

  clienteSelecionado = null;
  petSelecionado = null;
  petSelecionadoObj = null;
  servicosSelecionados = [];
  modoEdicao = false;
  agendamentoEditandoId = null;
  atualizarTituloModal();
  atualizarSelectServicosPorPet();
}

function preencherModalEdicao(ag) {
  modoEdicao = true;
  agendamentoEditandoId = ag.id;
  atualizarTituloModal();

  const modal = document.getElementById("agendamento-modal");
  if (modal) modal.classList.remove("hidden");

  const pet = petsCache.find((p) => p.id === ag.pet_id) || null;

  clienteSelecionado = ag.cliente_id;
  petSelecionado = ag.pet_id;
  petSelecionadoObj = {
    pet_id: ag.pet_id,
    pet_nome: ag.pet_nome,
    pet_porte: pet?.porte || "",
    cliente_id: ag.cliente_id,
    cliente_nome: ag.cliente_nome,
  };

  const busca = document.getElementById("busca-cliente-pet");
  if (busca) {
    busca.value = `${ag.cliente_nome} • ${ag.pet_nome}`;
    busca.disabled = true;
  }

  document.getElementById("cliente_nome").value = ag.cliente_nome || "";
  document.getElementById("pet_nome").value = ag.pet_nome || "";
  document.getElementById("ag_data").value = ag.data || "";
  document.getElementById("ag_hora").value = formatarHora(ag.hora || "");
  document.getElementById("ag_funcionario").value = ag.funcionario_id ? String(ag.funcionario_id) : "";
  document.getElementById("ag_prioridade").value = ag.prioridade || "NORMAL";
  document.getElementById("ag_observacoes").value = ag.observacoes || "";

  atualizarSelectServicosPorPet();

  servicosSelecionados = (ag.servicos || []).map((item) => {
    const cache = servicosCache.find((s) => s.id === item.servico_id);

    return {
      id: item.servico_id,
      nome: item.nome || cache?.nome || "Serviço",
      porte_referencia: cache?.porte_referencia || "",
      venda: cache?.venda ?? item.preco ?? 0,
      tempo_minutos: cache?.tempo_minutos ?? item.tempo_previsto ?? 0,
      ativo: true,
    };
  });

  renderServicosEscolhidos();
  mostrarMensagemAgenda("");
}

/* =========================================================
   MODAL DETALHE
========================================================= */

function abrirModalDetalheBase() {
  const modal = document.getElementById("detalhe-agendamento-modal");
  if (modal) modal.classList.remove("hidden");
}

function fecharModalDetalhe() {
  const modal = document.getElementById("detalhe-agendamento-modal");
  if (modal) modal.classList.add("hidden");

  mostrarMensagemDetalhe("");
  agendamentoDetalheAtual = null;
}

function setDetalheLoading(loading) {
  const el = document.getElementById("detalhe-loading");
  if (!el) return;
  el.classList.toggle("hidden", !loading);
}

function limparBotoesDetalhe() {
  [
    "btn-editar-agendamento",
    "btn-excluir-agendamento",
    "btn-falta-agendamento",
    "btn-cancelar-agendamento",
    "btn-iniciar-agendamento",
    "btn-finalizar-agendamento"
  ].forEach((id) => {
    document.getElementById(id)?.classList.add("hidden");
  });
}

function renderAcoesDetalhe(status) {
  limparBotoesDetalhe();

  const valor = String(status || "").toUpperCase();
  const btnEditar = document.getElementById("btn-editar-agendamento");

  if (valor === "AGUARDANDO") {
    btnEditar?.classList.remove("hidden");
    document.getElementById("btn-iniciar-agendamento")?.classList.remove("hidden");
    document.getElementById("btn-falta-agendamento")?.classList.remove("hidden");
    document.getElementById("btn-cancelar-agendamento")?.classList.remove("hidden");
    document.getElementById("btn-excluir-agendamento")?.classList.remove("hidden");
  }

  if (valor === "EM_ATENDIMENTO") {
    btnEditar?.classList.remove("hidden");
    document.getElementById("btn-finalizar-agendamento")?.classList.remove("hidden");
  }
}

function renderServicosDetalhe(servicos) {
  const wrap = document.getElementById("detalhe-servicos");
  if (!wrap) return;

  wrap.innerHTML = "";

  if (!Array.isArray(servicos) || !servicos.length) {
    wrap.innerHTML = `<div class="selected-service-item"><span>Nenhum serviço</span></div>`;
    return;
  }

  servicos.forEach((servico) => {
    const nome = typeof servico === "string"
      ? servico
      : (servico.nome || servico.servico_nome || "Serviço");

    const item = document.createElement("div");
    item.className = "selected-service-item";
    item.innerHTML = `<span>${escapeHtml(nome)}</span>`;
    wrap.appendChild(item);
  });
}

function renderDetalhe(data) {
  document.getElementById("detalhe-cliente").innerText = data.cliente_nome || "-";
  document.getElementById("detalhe-pet").innerText = data.pet_nome || "-";
  document.getElementById("detalhe-funcionario").innerText = data.funcionario_nome || "Sem funcionário";
  document.getElementById("detalhe-data").innerText = formatarDataBR(data.data);
  document.getElementById("detalhe-hora").innerText = formatarHora(data.hora);
  document.getElementById("detalhe-status").innerText = textoStatus(data.status);
  document.getElementById("detalhe-observacoes").innerText = data.observacoes || "Sem observações.";

  renderServicosDetalhe(data.servicos || []);
  renderAcoesDetalhe(data.status);
}

async function abrirModalDetalhe(id) {
  abrirModalDetalheBase();
  setDetalheLoading(true);
  mostrarMensagemDetalhe("");

  try {
    const response = await fetch(`/api/agenda/${id}`, { cache: "no-store" });

    if (!response.ok) {
      throw new Error("Não foi possível carregar os detalhes.");
    }

    const data = await response.json();
    agendamentoDetalheAtual = data;
    renderDetalhe(data);
  } catch (error) {
    console.error(error);
    mostrarMensagemDetalhe("Erro ao carregar os detalhes do agendamento.");
  } finally {
    setDetalheLoading(false);
  }
}

async function alterarStatusAgendamento(novoStatus) {
  if (!agendamentoDetalheAtual?.id) return;

  abrirConfirmModal({
    title: "Confirmar alteração",
    text: `Deseja alterar o status para "${textoStatus(novoStatus)}"?`,
    confirmText: "Confirmar",
    onConfirm: async () => {
      mostrarMensagemDetalhe("");

      try {
        const response = await fetch(
          `/api/agenda/${agendamentoDetalheAtual.id}/status?status=${encodeURIComponent(novoStatus)}`,
          { method: "PUT" }
        );

        const resposta = await response.json().catch(() => ({}));

        if (!response.ok) {
          mostrarMensagemDetalhe(resposta.detail || resposta.message || "Erro ao alterar status.");
          return;
        }

        agendamentoDetalheAtual = resposta;
        renderDetalhe(agendamentoDetalheAtual);
        atualizarCardNoDOM(agendamentoDetalheAtual);
        await carregarAgenda();

        mostrarMensagemDetalhe(`Status alterado para ${textoStatus(agendamentoDetalheAtual.status)}.`);
      } catch (error) {
        console.error(error);
        mostrarMensagemDetalhe("Erro de comunicação com o servidor.");
      }
    }
  });
}

async function excluirAgendamentoAtual() {
  if (!agendamentoDetalheAtual?.id) return;

  abrirConfirmModal({
    title: "Excluir agendamento",
    text: "Deseja realmente excluir este agendamento?",
    confirmText: "Excluir",
    onConfirm: async () => {
      try {
        const response = await fetch(`/api/agenda/${agendamentoDetalheAtual.id}`, {
          method: "DELETE"
        });

        const resposta = await response.json().catch(() => ({}));

        if (!response.ok) {
          mostrarMensagemDetalhe(resposta.detail || resposta.message || "Não foi possível excluir.");
          return;
        }

        removerCardNoDOM(agendamentoDetalheAtual.id);
        fecharModalDetalhe();
      } catch (error) {
        console.error(error);
        mostrarMensagemDetalhe("Erro de comunicação com o servidor.");
      }
    }
  });
}

function editarAgendamentoAtual() {
  if (!agendamentoDetalheAtual) return;

  const ag = { ...agendamentoDetalheAtual };
  preencherModalEdicao(ag);

  const modalDetalhe = document.getElementById("detalhe-agendamento-modal");
  if (modalDetalhe) modalDetalhe.classList.add("hidden");
}

/* =========================================================
   SERVIÇOS
========================================================= */

function renderServicosEscolhidos() {
  const wrap = document.getElementById("servicos-escolhidos");
  if (!wrap) return;

  wrap.innerHTML = "";

  servicosSelecionados.forEach((servico, index) => {
    const item = document.createElement("div");
    item.className = "selected-service-item";
    item.innerHTML = `
      <span>${escapeHtml(servico.nome)} • ${escapeHtml(servico.porte_referencia || "")}</span>
      <button type="button" class="remove-service-btn" data-index="${index}">✕</button>
    `;
    wrap.appendChild(item);
  });

  wrap.querySelectorAll(".remove-service-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      servicosSelecionados.splice(Number(btn.dataset.index), 1);
      renderServicosEscolhidos();
    });
  });
}

function adicionarServicoSelecionado() {
  const select = document.getElementById("servico-select");
  if (!select) return;

  const id = Number(select.value);
  if (!id) {
    mostrarMensagemAgenda("Selecione um serviço.");
    return;
  }

  if (!petSelecionadoObj) {
    mostrarMensagemAgenda("Selecione primeiro um pet.");
    return;
  }

  const servico = servicosCache.find((s) => s.id === id);
  if (!servico) {
    mostrarMensagemAgenda("Serviço não encontrado.");
    return;
  }

  const existe = servicosSelecionados.find((s) => s.id === servico.id);
  if (existe) {
    mostrarMensagemAgenda("Esse serviço já foi adicionado.");
    select.value = "";
    return;
  }

  const portePet = String(petSelecionadoObj.pet_porte || "").toUpperCase();
  const porteServico = String(servico.porte_referencia || "").toUpperCase();

  if (portePet && porteServico && portePet !== porteServico) {
    mostrarMensagemAgenda(`O serviço ${servico.nome} é para porte ${porteServico}, mas o pet selecionado é ${portePet}.`);
    select.value = "";
    return;
  }

  servicosSelecionados.push(servico);
  renderServicosEscolhidos();
  mostrarMensagemAgenda("");
  select.value = "";
}

/* =========================================================
   SALVAR
========================================================= */

function montarPayloadAgendamento() {
  return {
    funcionario_id: document.getElementById("ag_funcionario").value
      ? Number(document.getElementById("ag_funcionario").value)
      : null,
    data: document.getElementById("ag_data").value,
    hora: document.getElementById("ag_hora").value,
    prioridade: document.getElementById("ag_prioridade").value,
    observacoes: document.getElementById("ag_observacoes").value || null,
    servicos: servicosSelecionados.map((servico) => ({
      servico_id: servico.id,
      preco: Number(servico.venda),
      tempo_previsto: Number(servico.tempo_minutos)
    }))
  };
}

async function salvarNovoAgendamento() {
  const payload = {
    empresa_id: 1,
    cliente_id: clienteSelecionado,
    pet_id: petSelecionado,
    ...montarPayloadAgendamento()
  };

  return fetch("/api/agenda/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
}

async function salvarEdicaoAgendamento() {
  const payload = montarPayloadAgendamento();

  return fetch(`/api/agenda/${agendamentoEditandoId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
}

async function salvarAgendamento(e) {
  e.preventDefault();

  if (!clienteSelecionado || !petSelecionado) {
    mostrarMensagemAgenda("Selecione um pet na busca.");
    return;
  }

  const data = document.getElementById("ag_data").value;
  const hora = document.getElementById("ag_hora").value;

  if (!data || !hora) {
    mostrarMensagemAgenda("Preencha data e hora.");
    return;
  }

  if (!servicosSelecionados.length) {
    mostrarMensagemAgenda("Adicione ao menos um serviço.");
    return;
  }

  try {
    const response = modoEdicao
      ? await salvarEdicaoAgendamento()
      : await salvarNovoAgendamento();

    const resposta = await response.json().catch(() => ({}));

    if (!response.ok) {
      mostrarMensagemAgenda(resposta.detail || resposta.message || "Erro ao salvar agendamento.");
      console.error("Erro ao salvar agendamento:", resposta);
      return;
    }

    if (modoEdicao) {
      atualizarCardNoDOM(resposta);
      mostrarMensagemAgenda("Agendamento atualizado com sucesso.");
    } else {
      mostrarMensagemAgenda("Agendamento criado com sucesso.");
    }

    await carregarAgenda();

    setTimeout(() => {
      fecharModal();
    }, 500);
  } catch (error) {
    console.error(error);
    mostrarMensagemAgenda("Erro de comunicação com o servidor.");
  }
}

/* =========================================================
   INIT
========================================================= */

document.addEventListener("DOMContentLoaded", async () => {
  await carregarClientesPetsBase();
  await carregarServicos();
  await carregarFuncionarios();
  await carregarAgenda();

  iniciarAutoRefreshAgenda();

  document.getElementById("novo-agendamento-btn")?.addEventListener("click", () => abrirModal());
  document.getElementById("fechar-modal")?.addEventListener("click", fecharModal);
  document.getElementById("cancelar-modal")?.addEventListener("click", fecharModal);

  document.getElementById("fechar-detalhe-modal")?.addEventListener("click", fecharModalDetalhe);

  document.getElementById("confirm-close")?.addEventListener("click", fecharConfirmModal);
  document.getElementById("confirm-cancel")?.addEventListener("click", fecharConfirmModal);
  document.getElementById("confirm-ok")?.addEventListener("click", confirmarAcaoModal);

  document.getElementById("semana-anterior")?.addEventListener("click", async () => {
    semanaAtual = addDays(startOfWeek(semanaAtual), -7);
    await carregarAgenda();
  });

  document.getElementById("proxima-semana")?.addEventListener("click", async () => {
    semanaAtual = addDays(startOfWeek(semanaAtual), 7);
    await carregarAgenda();
  });

  document.getElementById("data-base")?.addEventListener("change", async (e) => {
    semanaAtual = new Date(e.target.value + "T00:00:00");
    await carregarAgenda();
  });

  document.getElementById("busca-cliente-pet")?.addEventListener("input", (e) => {
    buscarClientesPets(e.target.value);
  });

  document.getElementById("adicionar-servico-btn")?.addEventListener("click", adicionarServicoSelecionado);
  document.getElementById("agendamento-form")?.addEventListener("submit", salvarAgendamento);

  document.getElementById("btn-iniciar-agendamento")?.addEventListener("click", () => alterarStatusAgendamento("EM_ATENDIMENTO"));
  document.getElementById("btn-finalizar-agendamento")?.addEventListener("click", () => alterarStatusAgendamento("FINALIZADO"));
  document.getElementById("btn-falta-agendamento")?.addEventListener("click", () => alterarStatusAgendamento("FALTA"));
  document.getElementById("btn-cancelar-agendamento")?.addEventListener("click", () => alterarStatusAgendamento("CANCELADO"));
  document.getElementById("btn-excluir-agendamento")?.addEventListener("click", excluirAgendamentoAtual);
  document.getElementById("btn-editar-agendamento")?.addEventListener("click", editarAgendamentoAtual);
});