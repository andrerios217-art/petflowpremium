const COLUNAS = [
  "ORDEM",
  "PRE_BANHO",
  "PRE_TOSA",
  "BANHO",
  "FINALIZACAO_BANHO",
  "TOSA",
  "SECAGEM",
];

function corPrioridade(prioridade) {
  if (prioridade === "PRIORITARIO") return "prioridade-vermelha";
  if (prioridade === "NORMAL") return "prioridade-verde";
  return "prioridade-preta";
}

function nomeColuna(coluna) {
  const mapa = {
    ORDEM: "Ordem",
    PRE_BANHO: "Pré-banho",
    PRE_TOSA: "Pré-tosa",
    BANHO: "Banho",
    FINALIZACAO_BANHO: "Finalização do banho",
    TOSA: "Tosa",
    SECAGEM: "Secagem",
  };
  return mapa[coluna] || coluna;
}

async function carregarProducao() {
  const empresaId = document.body.dataset.empresaId || 1;
  const resp = await fetch(`/producao/?empresa_id=${empresaId}`);
  const data = await resp.json();

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

function renderCard(card) {
  const div = document.createElement("div");
  div.className = `card-producao ${corPrioridade(card.prioridade)}`;
  div.dataset.id = card.id;

  const servicos = (card.servicos || []).map(s => `<li>${s}</li>`).join("");

  let secagemHtml = "";
  if (card.coluna === "SECAGEM" && card.secagem_inicio && card.secagem_tempo) {
    secagemHtml = `<p class="secagem-info" data-inicio="${card.secagem_inicio}" data-minutos="${card.secagem_tempo}">
      Secagem: ${card.secagem_tempo} min
    </p>`;
  }

  div.innerHTML = `
    <div class="card-header">
      <strong>#${card.agendamento_id}</strong>
      <span>${card.prioridade}</span>
    </div>

    <div class="card-body">
      <h4>${card.pet_nome || "Pet"}</h4>
      <p><strong>Tutor:</strong> ${card.tutor_nome || "-"}</p>
      <p><strong>Responsável:</strong> ${card.funcionario_nome || "-"}</p>
      <p><strong>Status:</strong> ${card.etapa_status}</p>
      ${secagemHtml}
      <ul>${servicos}</ul>
    </div>

    <div class="card-actions">
      <button onclick="iniciarEtapa(${card.id})">Iniciar</button>
      <button onclick="abrirMover(${card.id}, '${card.coluna}')">Avançar</button>
    </div>
  `;

  return div;
}

async function iniciarEtapa(id) {
  const funcionarioId = prompt("Informe o ID do funcionário:");
  if (!funcionarioId) return;

  const resp = await fetch(`/producao/${id}/iniciar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ funcionario_id: Number(funcionarioId) }),
  });

  if (!resp.ok) {
    const erro = await resp.json();
    alert(erro.detail || "Erro ao iniciar etapa.");
    return;
  }

  carregarProducao();
}

function proximoDestino(colunaAtual) {
  const mapa = {
    ORDEM: ["PRE_BANHO"],
    PRE_BANHO: ["BANHO", "PRE_TOSA"],
    PRE_TOSA: ["BANHO"],
    BANHO: ["FINALIZACAO_BANHO", "SECAGEM"],
    SECAGEM: ["FINALIZACAO_BANHO"],
    FINALIZACAO_BANHO: ["TOSA", "FINALIZAR"],
    TOSA: ["FINALIZAR"],
  };
  return mapa[colunaAtual] || [];
}

async function abrirMover(id, colunaAtual) {
  const destinos = proximoDestino(colunaAtual);
  const destino = prompt(`Destino possível: ${destinos.join(", ")}`);
  if (!destino) return;

  const payload = { coluna_destino: destino };

  if (colunaAtual === "PRE_BANHO") {
    const pulga = confirm("Tem pulga?");
    const carrapato = confirm("Tem carrapato?");
    const outros = confirm("Tem outros problemas?");
    const intercorrencias = [];
    let descricao = null;

    if (pulga) intercorrencias.push("PULGA");
    if (carrapato) intercorrencias.push("CARRAPATO");
    if (outros) {
      intercorrencias.push("OUTROS");
      descricao = prompt("Descreva:");
    }

    payload.intercorrencias = intercorrencias;
    payload.descricao_intercorrencia = descricao;
  }

  if (destino === "SECAGEM") {
    const tempo = prompt("Tempo de secagem em minutos:");
    payload.secagem_tempo = Number(tempo);
  }

  const resp = await fetch(`/producao/${id}/mover`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!resp.ok) {
    const erro = await resp.json();
    alert(erro.detail || "Erro ao mover card.");
    return;
  }

  carregarProducao();
}

function iniciarTimerSecagem() {
  setInterval(() => {
    document.querySelectorAll(".secagem-info").forEach((el) => {
      const inicio = new Date(el.dataset.inicio);
      const minutos = Number(el.dataset.minutos);
      const limite = new Date(inicio.getTime() + minutos * 60000);
      const agora = new Date();

      if (agora >= limite) {
        const card = el.closest(".card-producao");
        if (card) card.classList.add("alerta-secagem");
      }
    });
  }, 5000);
}

document.addEventListener("DOMContentLoaded", () => {
  carregarProducao();
  iniciarTimerSecagem();
  setInterval(carregarProducao, 15000);
});