const COLUNAS = [
  "PRE_BANHO",
  "PRE_TOSA",
  "BANHO",
  "FINALIZACAO_BANHO",
  "TOSA",
  "SECAGEM",
];

let funcionariosProducaoCache = [];
let cardAcaoAtual = null;
let producaoAutoRefresh = null;
let carregandoProducao = false;
let ultimoSnapshotProducao = "";
let timerSecagemIniciado = false;
let ultimoRefreshManual = 0;

function corPrioridade(prioridade) {
  const valor = String(prioridade || "").toUpperCase();

  if (valor === "PRIORITARIO" || valor === "PRIORIDADE") return "prioridade-vermelha";
  if (valor === "NORMAL") return "prioridade-verde";
  return "prioridade-preta";
}

function corStatusCard(etapaStatus) {
  const valor = String(etapaStatus || "").toUpperCase();

  if (valor === "EM_EXECUCAO") return "status-execucao-producao";
  return "status-aguardando-producao";
}

function badgePrioridade(prioridade) {
  const valor = String(prioridade || "").toUpperCase();

  if (valor === "PRIORITARIO" || valor === "PRIORIDADE") {
    return '<span class="badge-prioridade badge-prioritario">PRIORITÁRIO</span>';
  }

  if (valor === "NORMAL") {
    return '<span class="badge-prioridade badge-normal">NORMAL</span>';
  }

  return '<span class="badge-prioridade badge-sem-prioridade">SEM PRIORIDADE</span>';
}

function obterEmpresaId() {
  const pagina = document.querySelector(".pagina-producao");
  return pagina?.dataset?.empresaId || "1";
}

function textoStatusEtapa(status) {
  const valor = String(status || "").toUpperCase();

  if (valor === "AGUARDANDO") return "Aguardando";
  if (valor === "EM_EXECUCAO") return "Em execução";
  if (valor === "CONCLUIDO") return "Concluído";

  return valor || "-";
}

function nomeColuna(coluna) {
  const mapa = {
    PRE_BANHO: "Pré-banho",
    PRE_TOSA: "Pré-tosa",
    BANHO: "Banho",
    FINALIZACAO_BANHO: "Finalização do banho",
    TOSA: "Tosa",
    SECAGEM: "Secagem",
    FINALIZAR: "Finalizar atendimento",
  };

  return mapa[coluna] || coluna;
}

function cardEstaEmUltimaEtapa(card) {
  return String(card.proximo_destino_automatico || "").toUpperCase() === "FINALIZAR";
}

function deveExibirBotaoIniciar(card) {
  const coluna = String(card.coluna || "").toUpperCase();
  const status = String(card.etapa_status || "").toUpperCase();

  if (coluna === "SECAGEM") return false;
  return status === "AGUARDANDO";
}

function deveExibirBotaoAvancar(card) {
  const status = String(card.etapa_status || "").toUpperCase();
  const coluna = String(card.coluna || "").toUpperCase();

  return status === "EM_EXECUCAO" || coluna === "SECAGEM";
}

function normalizarListaFuncionarios(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.itens)) return payload.itens;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.results)) return payload.results;
  return [];
}

function funcionarioEstaAtivo(funcionario) {
  if (typeof funcionario?.ativo === "boolean") {
    return funcionario.ativo;
  }
  return true;
}

function nomeFuncaoFuncionario(funcionario) {
  return funcionario?.funcao || funcionario?.cargo || funcionario?.tipo || "Sem função";
}

function modalAcaoAberto() {
  const modal = document.getElementById("acao-producao-modal");
  return !!modal && !modal.classList.contains("hidden");
}

function podeExecutarAutoRefresh() {
  if (document.hidden) return false;
  if (modalAcaoAberto()) return false;
  if (carregandoProducao) return false;
  return true;
}

function gerarSnapshotProducao(cards) {
  const base = (Array.isArray(cards) ? cards : []).map((card) => ({
    id: card.id,
    coluna: card.coluna,
    etapa_status: card.etapa_status,
    prioridade: card.prioridade,
    funcionario_id: card.funcionario_id,
    funcionario_nome: card.funcionario_nome,
    secagem_tempo: card.secagem_tempo,
    secagem_inicio: card.secagem_inicio,
    finalizado: card.finalizado,
    observacoes: card.observacoes,
    intercorrencias: card.intercorrencias,
    proximo_destino_automatico: card.proximo_destino_automatico,
    status_agendamento: card.status_agendamento,
    pet_nome: card.pet_nome,
    tutor_nome: card.tutor_nome,
    servicos: card.servicos || [],
  }));

  return JSON.stringify(base);
}

async function carregarFuncionariosProducao() {
  const empresaId = obterEmpresaId();

  try {
    const urlsTentativa = [
      `/api/funcionarios/?empresa_id=${empresaId}`,
      `/api/funcionarios?empresa_id=${empresaId}`,
      "/api/funcionarios/",
      "/api/funcionarios",
    ];

    let data = [];
    let carregado = false;

    for (const url of urlsTentativa) {
      try {
        const resp = await fetch(url, { cache: "no-store" });

        if (!resp.ok) {
          continue;
        }

        const json = await resp.json();
        data = normalizarListaFuncionarios(json);
        carregado = true;
        break;
      } catch (erroInterno) {
        console.error(`Erro ao tentar carregar funcionários em ${url}:`, erroInterno);
      }
    }

    if (!carregado) {
      funcionariosProducaoCache = [];
      console.error("Não foi possível carregar os funcionários da produção.");
      return;
    }

    funcionariosProducaoCache = data.filter(funcionarioEstaAtivo);
  } catch (error) {
    funcionariosProducaoCache = [];
    console.error("Erro ao carregar funcionários:", error);
  }
}

function preencherSelectFuncionarios(valorSelecionado = "") {
  const select = document.getElementById("acao-funcionario");
  if (!select) return;

  select.innerHTML = `<option value="">Selecione</option>`;

  funcionariosProducaoCache.forEach((func) => {
    const opt = document.createElement("option");
    opt.value = String(func.id);
    opt.textContent = `${func.nome} • ${nomeFuncaoFuncionario(func)}`;

    if (String(valorSelecionado) === String(func.id)) {
      opt.selected = true;
    }

    select.appendChild(opt);
  });
}

function limparMensagemAcao() {
  const el = document.getElementById("acao-producao-message");
  if (el) el.innerText = "";
}

function mostrarMensagemAcao(texto) {
  const el = document.getElementById("acao-producao-message");
  if (el) el.innerText = texto;
}

function garantirToggleSecagem() {
  const grupoAcaoBanho = document.getElementById("grupo-acao-banho");
  if (!grupoAcaoBanho) return;

  let wrapper = document.getElementById("acao-banho-toggle-wrapper");
  if (!wrapper) {
    wrapper = document.createElement("div");
    wrapper.id = "acao-banho-toggle-wrapper";
    wrapper.className = "form-group";
    wrapper.innerHTML = `
      <label style="display:flex; align-items:center; justify-content:space-between; gap:16px; width:100%;">
        <span>Enviar para secagem</span>
        <span style="display:flex; align-items:center; gap:10px;">
          <span id="acao-banho-toggle-texto" style="font-weight:600; color:var(--muted);">Não</span>
          <span class="switch">
            <input type="checkbox" id="acao-banho-toggle-secagem">
            <span class="slider"></span>
          </span>
        </span>
      </label>
    `;
    grupoAcaoBanho.appendChild(wrapper);
  }

  const selectOriginal = document.getElementById("acao-banho-opcao");
  if (selectOriginal) {
    const blocoOriginal = selectOriginal.closest(".form-group") || selectOriginal.parentElement;
    if (blocoOriginal) {
      blocoOriginal.classList.add("hidden");
    } else {
      selectOriginal.classList.add("hidden");
    }
  }

  const toggle = document.getElementById("acao-banho-toggle-secagem");
  const texto = document.getElementById("acao-banho-toggle-texto");
  const grupoSecagem = document.getElementById("grupo-secagem");

  if (!toggle || !texto || !grupoSecagem) return;

  const atualizarUI = () => {
    if (toggle.checked) {
      texto.innerText = "Sim";
      grupoSecagem.classList.remove("hidden");
    } else {
      texto.innerText = "Não";
      grupoSecagem.classList.add("hidden");
      const inputTempo = document.getElementById("acao-secagem-tempo");
      if (inputTempo) inputTempo.value = "";
    }
  };

  toggle.onchange = atualizarUI;
  atualizarUI();
}

function limparCamposModalAcao() {
  document.getElementById("acao-producao-id").value = "";
  document.getElementById("acao-producao-coluna-atual").value = "";
  document.getElementById("acao-producao-tipo").value = "";
  document.getElementById("acao-producao-finaliza").value = "";

  const campoAcaoBanho = document.getElementById("acao-banho-opcao");
  if (campoAcaoBanho) {
    campoAcaoBanho.value = "";
  }

  const toggleSecagem = document.getElementById("acao-banho-toggle-secagem");
  if (toggleSecagem) {
    toggleSecagem.checked = false;
  }

  const textoToggle = document.getElementById("acao-banho-toggle-texto");
  if (textoToggle) {
    textoToggle.innerText = "Não";
  }

  document.getElementById("acao-secagem-tempo").value = "";
  document.getElementById("acao-descricao-intercorrencia").value = "";
  document.getElementById("acao-observacoes-gerais").value = "";

  document.getElementById("intercorrencia-pulga").checked = false;
  document.getElementById("intercorrencia-carrapato").checked = false;
  document.getElementById("intercorrencia-ferida").checked = false;
  document.getElementById("intercorrencia-irritacao").checked = false;
  document.getElementById("intercorrencia-outros").checked = false;

  document.getElementById("grupo-acao-banho").classList.add("hidden");
  document.getElementById("grupo-secagem").classList.add("hidden");
  document.getElementById("grupo-intercorrencias").classList.add("hidden");
  document.getElementById("grupo-intercorrencia-outros").classList.add("hidden");
  document.getElementById("grupo-observacoes-gerais").classList.add("hidden");

  limparMensagemAcao();
}

async function abrirModalAcao({ tipo, card }) {
  cardAcaoAtual = card;
  limparCamposModalAcao();

  if (!funcionariosProducaoCache.length) {
    await carregarFuncionariosProducao();
  }

  document.getElementById("acao-producao-id").value = card.id;
  document.getElementById("acao-producao-coluna-atual").value = card.coluna;
  document.getElementById("acao-producao-tipo").value = tipo;
  document.getElementById("acao-producao-finaliza").value = cardEstaEmUltimaEtapa(card) ? "1" : "0";

  preencherSelectFuncionarios(card.funcionario_id || "");

  const titulo = document.getElementById("acao-modal-titulo");
  const subtitulo = document.getElementById("acao-modal-subtitulo");

  if (tipo === "INICIAR") {
    titulo.innerText = "Iniciar etapa";
    subtitulo.innerText = `Defina o responsável por ${nomeColuna(card.coluna)}.`;
  }

  if (tipo === "AVANCAR") {
    titulo.innerText = "Avançar etapa";

    if (card.coluna === "PRE_BANHO") {
      subtitulo.innerText = "A próxima etapa será definida automaticamente pelo agendamento.";
      document.getElementById("grupo-intercorrencias").classList.remove("hidden");
    } else if (card.coluna === "BANHO") {
      subtitulo.innerText = "Ative o botão abaixo se o pet for para secagem.";
      document.getElementById("grupo-acao-banho").classList.remove("hidden");
      garantirToggleSecagem();
    } else if (card.coluna === "SECAGEM") {
      subtitulo.innerText = "Finalize a secagem para seguir automaticamente para a próxima etapa.";
    } else {
      subtitulo.innerText = "A próxima etapa será definida automaticamente.";
    }

    if (cardEstaEmUltimaEtapa(card)) {
      document.getElementById("grupo-observacoes-gerais").classList.remove("hidden");
      document.getElementById("grupo-intercorrencias").classList.remove("hidden");
      subtitulo.innerText = "Antes de finalizar, registre observações gerais e o que foi encontrado.";
    }
  }

  document.getElementById("acao-producao-modal").classList.remove("hidden");
}

function fecharModalAcao() {
  document.getElementById("acao-producao-modal").classList.add("hidden");
  cardAcaoAtual = null;
  limparCamposModalAcao();
}

function coletarIntercorrencias() {
  const itens = [];

  if (document.getElementById("intercorrencia-pulga").checked) itens.push("PULGA");
  if (document.getElementById("intercorrencia-carrapato").checked) itens.push("CARRAPATO");
  if (document.getElementById("intercorrencia-ferida").checked) itens.push("FERIDA");
  if (document.getElementById("intercorrencia-irritacao").checked) itens.push("IRRITACAO");
  if (document.getElementById("intercorrencia-outros").checked) itens.push("OUTROS");

  return itens;
}

function renderizarKanban(data) {
  COLUNAS.forEach((coluna) => {
    const container = document.getElementById(`coluna-${coluna}`);
    if (container) container.innerHTML = "";
  });

  data.forEach((card) => {
    const container = document.getElementById(`coluna-${card.coluna}`);
    if (!container) return;
    container.appendChild(renderCard(card));
  });
}

async function carregarProducao(forcarRender = false) {
  if (carregandoProducao) return;

  const agora = Date.now();
  if (!forcarRender && agora - ultimoRefreshManual < 1200) {
    return;
  }

  const empresaId = obterEmpresaId();
  carregandoProducao = true;

  try {
    const resp = await fetch(`/api/producao/?empresa_id=${empresaId}`, { cache: "no-store" });

    if (!resp.ok) {
      console.error("Erro ao carregar produção:", resp.status);
      return;
    }

    const data = await resp.json();
    const snapshotAtual = gerarSnapshotProducao(data);

    if (!forcarRender && snapshotAtual === ultimoSnapshotProducao) {
      return;
    }

    ultimoSnapshotProducao = snapshotAtual;
    renderizarKanban(data);
  } catch (error) {
    console.error("Falha ao carregar produção:", error);
  } finally {
    carregandoProducao = false;
  }
}

function iniciarAutoRefreshProducao() {
  if (producaoAutoRefresh) {
    clearInterval(producaoAutoRefresh);
  }

  producaoAutoRefresh = setInterval(async () => {
    if (!podeExecutarAutoRefresh()) {
      return;
    }

    await carregarProducao(false);
  }, 12000);
}

function renderCard(card) {
  const div = document.createElement("div");
  div.className = `card-producao ${corPrioridade(card.prioridade)} ${corStatusCard(card.etapa_status)}`;
  div.dataset.id = card.id;

  const servicos = (card.servicos || [])
    .map((s) => `<li>${s}</li>`)
    .join("");

  let secagemHtml = "";
  if (card.coluna === "SECAGEM" && card.secagem_inicio && card.secagem_tempo) {
    secagemHtml = `
      <p class="secagem-info" data-inicio="${card.secagem_inicio}" data-minutos="${card.secagem_tempo}">
        Tempo de secagem: ${card.secagem_tempo} min
      </p>
    `;
  }

  const cardSerializado = JSON.stringify(card).replaceAll('"', "&quot;");

  const botaoIniciar = deveExibirBotaoIniciar(card)
    ? `<button type="button" onclick="abrirAcaoIniciar('${cardSerializado}')">Iniciar</button>`
    : "";

  const botaoAvancar = deveExibirBotaoAvancar(card)
    ? `<button type="button" class="btn-secundario" onclick="abrirAcaoAvancar('${cardSerializado}')">${card.coluna === "SECAGEM" ? "Finalizar secagem" : "Avançar"}</button>`
    : "";

  div.innerHTML = `
    <div class="card-header">
      <div>
        <div class="card-codigo">Agendamento #${card.agendamento_id}</div>
        <h4 class="card-titulo">${card.pet_nome || "Pet"}</h4>
      </div>
      ${badgePrioridade(card.prioridade)}
    </div>

    <div class="card-info">
      <p><strong>Tutor:</strong> ${card.tutor_nome || "-"}</p>
      <p><strong>Responsável:</strong> ${card.funcionario_nome || "-"}</p>
      <p><strong>Status:</strong> ${textoStatusEtapa(card.etapa_status)}</p>
    </div>

    <ul class="card-servicos">${servicos}</ul>

    <div class="card-status-etapa">${nomeColuna(card.coluna)}</div>
    ${secagemHtml}

    <div class="card-actions">
      ${botaoIniciar}
      ${botaoAvancar}
    </div>
  `;

  return div;
}

function abrirAcaoIniciar(cardSerializado) {
  const card = JSON.parse(cardSerializado.replaceAll("&quot;", '"'));
  abrirModalAcao({
    tipo: "INICIAR",
    card,
  });
}

function abrirAcaoAvancar(cardSerializado) {
  const card = JSON.parse(cardSerializado.replaceAll("&quot;", '"'));
  abrirModalAcao({
    tipo: "AVANCAR",
    card,
  });
}

async function confirmarAcaoProducao() {
  const tipo = document.getElementById("acao-producao-tipo").value;
  const producaoId = document.getElementById("acao-producao-id").value;
  const funcionarioId = document.getElementById("acao-funcionario").value;
  const finaliza = document.getElementById("acao-producao-finaliza").value === "1";

  if (!producaoId) {
    mostrarMensagemAcao("Card inválido.");
    return;
  }

  if (!funcionarioId && tipo === "INICIAR") {
    mostrarMensagemAcao("Selecione o funcionário responsável.");
    return;
  }

  ultimoRefreshManual = Date.now();

  if (tipo === "INICIAR") {
    try {
      const resp = await fetch(`/api/producao/${producaoId}/iniciar`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          funcionario_id: Number(funcionarioId),
        }),
      });

      const data = await resp.json().catch(() => ({}));

      if (!resp.ok) {
        mostrarMensagemAcao(data.detail || "Erro ao iniciar etapa.");
        return;
      }

      fecharModalAcao();
      await carregarProducao(true);
      return;
    } catch (error) {
      console.error(error);
      mostrarMensagemAcao("Falha de comunicação com o servidor.");
      return;
    }
  }

  if (tipo === "AVANCAR") {
    const payload = {
      funcionario_id: funcionarioId ? Number(funcionarioId) : null,
      usar_secagem: false,
    };

    if (cardAcaoAtual?.coluna === "PRE_BANHO") {
      payload.intercorrencias = coletarIntercorrencias();

      if (payload.intercorrencias.includes("OUTROS")) {
        payload.descricao_intercorrencia = document.getElementById("acao-descricao-intercorrencia").value || null;
      }
    }

    if (cardAcaoAtual?.coluna === "BANHO") {
      const toggleSecagem = document.getElementById("acao-banho-toggle-secagem");
      const vaiParaSecagem = !!toggleSecagem?.checked;

      if (vaiParaSecagem) {
        payload.usar_secagem = true;

        const tempo = Number(document.getElementById("acao-secagem-tempo").value);
        if (!tempo || tempo <= 0) {
          mostrarMensagemAcao("Informe um tempo de secagem válido.");
          return;
        }

        payload.secagem_tempo = tempo;
      } else {
        payload.usar_secagem = false;
      }
    }

    if (finaliza) {
      payload.intercorrencias = coletarIntercorrencias();

      if (payload.intercorrencias.includes("OUTROS")) {
        payload.descricao_intercorrencia = document.getElementById("acao-descricao-intercorrencia").value || null;
      }

      payload.observacoes_gerais = document.getElementById("acao-observacoes-gerais").value || null;
    }

    try {
      const resp = await fetch(`/api/producao/${producaoId}/proximo`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await resp.json().catch(() => ({}));

      if (!resp.ok) {
        mostrarMensagemAcao(data.detail || "Erro ao avançar etapa.");
        return;
      }

      fecharModalAcao();
      await carregarProducao(true);
      return;
    } catch (error) {
      console.error(error);
      mostrarMensagemAcao("Falha de comunicação com o servidor.");
      return;
    }
  }
}

function iniciarTimerSecagem() {
  if (timerSecagemIniciado) return;
  timerSecagemIniciado = true;

  setInterval(() => {
    document.querySelectorAll(".secagem-info").forEach((el) => {
      const inicio = new Date(el.dataset.inicio);
      const minutos = Number(el.dataset.minutos);
      const limite = new Date(inicio.getTime() + minutos * 60000);
      const agora = new Date();

      const card = el.closest(".card-producao");
      if (!card) return;

      if (agora >= limite) {
        card.classList.add("alerta-secagem");
      } else {
        card.classList.remove("alerta-secagem");
      }
    });
  }, 2000);
}

function configurarEventosModal() {
  const modalOverlay = document.getElementById("acao-producao-modal");

  document.getElementById("fechar-acao-producao-modal")?.addEventListener("click", fecharModalAcao);
  document.getElementById("cancelar-acao-producao")?.addEventListener("click", fecharModalAcao);
  document.getElementById("confirmar-acao-producao")?.addEventListener("click", confirmarAcaoProducao);
  document.getElementById("btn-atualizar-producao")?.addEventListener("click", async () => {
    ultimoRefreshManual = Date.now();
    await carregarProducao(true);
  });

  modalOverlay?.addEventListener("click", (event) => {
    if (event.target === modalOverlay) {
      fecharModalAcao();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && modalAcaoAberto()) {
      fecharModalAcao();
    }
  });

  document.addEventListener("visibilitychange", async () => {
    if (!document.hidden && !modalAcaoAberto()) {
      await carregarProducao(false);
    }
  });

  document.getElementById("intercorrencia-outros")?.addEventListener("change", (e) => {
    const grupo = document.getElementById("grupo-intercorrencia-outros");
    if (e.target.checked) {
      grupo.classList.remove("hidden");
    } else {
      grupo.classList.add("hidden");
      document.getElementById("acao-descricao-intercorrencia").value = "";
    }
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  await carregarFuncionariosProducao();
  await carregarProducao(true);

  configurarEventosModal();
  iniciarTimerSecagem();
  iniciarAutoRefreshProducao();
});