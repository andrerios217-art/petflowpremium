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

async function carregarFuncionariosProducao() {
  try {
    const resp = await fetch("/api/funcionarios/");
    if (!resp.ok) return;

    const data = await resp.json();
    funcionariosProducaoCache = Array.isArray(data)
      ? data.filter((f) => f.ativo)
      : [];
  } catch (error) {
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
    opt.textContent = `${func.nome} • ${func.funcao}`;
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

function limparCamposModalAcao() {
  document.getElementById("acao-producao-id").value = "";
  document.getElementById("acao-producao-coluna-atual").value = "";
  document.getElementById("acao-producao-tipo").value = "";
  document.getElementById("acao-producao-finaliza").value = "";

  document.getElementById("acao-banho-opcao").value = "";
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

function abrirModalAcao({ tipo, card }) {
  cardAcaoAtual = card;
  limparCamposModalAcao();

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
      subtitulo.innerText = "Escolha se o pet vai para secagem ou finalização do banho.";
      document.getElementById("grupo-acao-banho").classList.remove("hidden");
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

async function carregarProducao() {
  const empresaId = obterEmpresaId();

  try {
    const resp = await fetch(`/api/producao/?empresa_id=${empresaId}`);

    if (!resp.ok) {
      console.error("Erro ao carregar produção:", resp.status);
      return;
    }

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
  } catch (error) {
    console.error("Falha ao carregar produção:", error);
  }
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

  const textoAvancar = card.coluna === "SECAGEM" ? "Finalizar secagem" : "Avançar";

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
      <button type="button" class="btn-secundario" onclick="abrirAcaoAvancar('${cardSerializado}')">${textoAvancar}</button>
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
      await carregarProducao();
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
      const opcaoBanho = document.getElementById("acao-banho-opcao").value;

      if (!opcaoBanho) {
        mostrarMensagemAcao("Selecione a ação do banho.");
        return;
      }

      if (opcaoBanho === "SECAGEM") {
        payload.usar_secagem = true;

        const tempo = Number(document.getElementById("acao-secagem-tempo").value);
        if (!tempo || tempo <= 0) {
          mostrarMensagemAcao("Informe um tempo de secagem válido.");
          return;
        }

        payload.secagem_tempo = tempo;
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
      await carregarProducao();
      return;
    } catch (error) {
      console.error(error);
      mostrarMensagemAcao("Falha de comunicação com o servidor.");
      return;
    }
  }
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
  }, 2000);
}

function configurarEventosModal() {
  document.getElementById("fechar-acao-producao-modal")?.addEventListener("click", fecharModalAcao);
  document.getElementById("cancelar-acao-producao")?.addEventListener("click", fecharModalAcao);
  document.getElementById("confirmar-acao-producao")?.addEventListener("click", confirmarAcaoProducao);
  document.getElementById("btn-atualizar-producao")?.addEventListener("click", carregarProducao);

  document.getElementById("acao-banho-opcao")?.addEventListener("change", (e) => {
    const valor = String(e.target.value || "").toUpperCase();
    const grupoSecagem = document.getElementById("grupo-secagem");

    if (valor === "SECAGEM") {
      grupoSecagem.classList.remove("hidden");
    } else {
      grupoSecagem.classList.add("hidden");
      document.getElementById("acao-secagem-tempo").value = "";
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
  await carregarProducao();

  configurarEventosModal();
  iniciarTimerSecagem();
  setInterval(carregarProducao, 15000);
});