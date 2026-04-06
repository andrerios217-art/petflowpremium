function formatarMoeda(valor) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL"
  }).format(Number(valor || 0));
}

function obterEmpresaId() {
  return localStorage.getItem("empresa_id") || 1;
}

function aplicarClasseLucro(elemento, valor) {
  if (!elemento) return;

  elemento.classList.remove("valor-positivo", "valor-negativo");

  if (Number(valor || 0) >= 0) {
    elemento.classList.add("valor-positivo");
  } else {
    elemento.classList.add("valor-negativo");
  }
}

function aplicarStatusCaixa(elemento, status) {
  if (!elemento) return;

  const statusNormalizado = (status || "fechado").toLowerCase();

  elemento.textContent = statusNormalizado;
  elemento.classList.add("badge-status");
  elemento.classList.remove("badge-aberto", "badge-fechado");

  if (statusNormalizado === "aberto") {
    elemento.classList.add("badge-aberto");
  } else {
    elemento.classList.add("badge-fechado");
  }
}

function formatarDataIso(data) {
  const ano = data.getFullYear();
  const mes = String(data.getMonth() + 1).padStart(2, "0");
  const dia = String(data.getDate()).padStart(2, "0");
  return `${ano}-${mes}-${dia}`;
}

async function carregarDashboardFinanceiro() {
  try {
    const empresaId = obterEmpresaId();

    const response = await fetch(`/api/financeiro/dashboard/?empresa_id=${empresaId}`);

    if (!response.ok) {
      throw new Error("Erro ao carregar dashboard financeiro");
    }

    const data = await response.json();

    const cardFaturamentoHoje = document.getElementById("card-faturamento-hoje");
    const finCaixaStatus = document.getElementById("fin-caixa-status");
    const finEntradasHoje = document.getElementById("fin-entradas-hoje");
    const finSaidasHoje = document.getElementById("fin-saidas-hoje");
    const finLucroHoje = document.getElementById("fin-lucro-hoje");
    const finReceberAberto = document.getElementById("fin-receber-aberto");
    const finPagarAberto = document.getElementById("fin-pagar-aberto");

    if (cardFaturamentoHoje) {
      cardFaturamentoHoje.textContent = formatarMoeda(data.entradas_hoje);
    }

    aplicarStatusCaixa(finCaixaStatus, data.caixa_status || "fechado");

    if (finEntradasHoje) {
      finEntradasHoje.textContent = formatarMoeda(data.entradas_hoje);
    }

    if (finSaidasHoje) {
      finSaidasHoje.textContent = formatarMoeda(data.saidas_hoje);
    }

    if (finLucroHoje) {
      finLucroHoje.textContent = formatarMoeda(data.lucro_hoje);
      aplicarClasseLucro(finLucroHoje, data.lucro_hoje);
    }

    if (finReceberAberto) {
      finReceberAberto.textContent = formatarMoeda(data.receber_aberto);
    }

    if (finPagarAberto) {
      finPagarAberto.textContent = formatarMoeda(data.pagar_aberto);
    }
  } catch (error) {
    console.error("Erro ao carregar resumo financeiro:", error);
  }
}

async function carregarDashboardAgenda() {
  try {
    const empresaId = obterEmpresaId();
    const hoje = formatarDataIso(new Date());

    const response = await fetch(
      `/api/agenda/semana?empresa_id=${empresaId}&data_inicio=${hoje}&data_fim=${hoje}`
    );

    if (!response.ok) {
      throw new Error("Erro ao carregar agenda da dashboard");
    }

    const agendamentos = await response.json();
    const lista = Array.isArray(agendamentos) ? agendamentos : [];

    const cardAgendaDia = document.getElementById("card-agenda-dia");
    const cardPetsAtendimento = document.getElementById("card-pets-atendimento");
    const blocoResumo = document.querySelector(".content-grid .glass-card.large-card");

    const totalAgendaDia = lista.length;
    const petsEmAtendimento = lista.filter((item) => {
      const status = String(item.status || "").toUpperCase();
      return status === "EM_ATENDIMENTO";
    }).length;

    const aguardando = lista.filter((item) => {
      const status = String(item.status || "").toUpperCase();
      return status === "AGUARDANDO";
    }).length;

    const finalizados = lista.filter((item) => {
      const status = String(item.status || "").toUpperCase();
      return status === "FINALIZADO";
    }).length;

    const comIntercorrencia = lista.filter((item) => Boolean(item.tem_intercorrencia)).length;

    if (cardAgendaDia) {
      cardAgendaDia.textContent = String(totalAgendaDia);
    }

    if (cardPetsAtendimento) {
      cardPetsAtendimento.textContent = String(petsEmAtendimento);
    }

    if (blocoResumo) {
      blocoResumo.innerHTML = `
        <h2>Resumo Operacional</h2>
        <ul class="simple-list">
          <li>Agendamentos hoje: <span>${totalAgendaDia}</span></li>
          <li>Pets em atendimento: <span>${petsEmAtendimento}</span></li>
          <li>Aguardando início: <span>${aguardando}</span></li>
          <li>Finalizados hoje: <span>${finalizados}</span></li>
          <li>Com intercorrência: <span>${comIntercorrencia}</span></li>
        </ul>
      `;
    }
  } catch (error) {
    console.error("Erro ao carregar resumo da agenda:", error);
  }
}

async function carregarDashboardClientes() {
  try {
    const response = await fetch(`/api/clientes/`);

    if (!response.ok) {
      throw new Error("Erro ao carregar clientes da dashboard");
    }

    const clientes = await response.json();
    const lista = Array.isArray(clientes) ? clientes : [];

    const cardClientesAtivos = document.getElementById("card-clientes-ativos");

    const clientesAtivos = lista.filter((cliente) => {
      return Boolean(cliente && cliente.ativo);
    }).length;

    if (cardClientesAtivos) {
      cardClientesAtivos.textContent = String(clientesAtivos);
    }
  } catch (error) {
    console.error("Erro ao carregar clientes ativos:", error);
  }
}

async function carregarDashboardProducao() {
  try {
    const empresaId = obterEmpresaId();

    const response = await fetch(`/api/producao/?empresa_id=${empresaId}`);

    if (!response.ok) {
      throw new Error("Erro ao carregar produção da dashboard");
    }

    const producao = await response.json();
    const lista = Array.isArray(producao) ? producao : [];

    const prodPreBanho = document.getElementById("prod-pre-banho");
    const prodBanho = document.getElementById("prod-banho");
    const prodSecagem = document.getElementById("prod-secagem");
    const prodTosa = document.getElementById("prod-tosa");

    const totalPreBanho = lista.filter((item) => {
      return String(item.coluna || "").toUpperCase() === "PRE_BANHO";
    }).length;

    const totalBanho = lista.filter((item) => {
      return String(item.coluna || "").toUpperCase() === "BANHO";
    }).length;

    const totalSecagem = lista.filter((item) => {
      return String(item.coluna || "").toUpperCase() === "SECAGEM";
    }).length;

    const totalTosa = lista.filter((item) => {
      return String(item.coluna || "").toUpperCase() === "TOSA";
    }).length;

    if (prodPreBanho) {
      prodPreBanho.textContent = String(totalPreBanho);
    }

    if (prodBanho) {
      prodBanho.textContent = String(totalBanho);
    }

    if (prodSecagem) {
      prodSecagem.textContent = String(totalSecagem);
    }

    if (prodTosa) {
      prodTosa.textContent = String(totalTosa);
    }
  } catch (error) {
    console.error("Erro ao carregar produção da dashboard:", error);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  carregarDashboardFinanceiro();
  carregarDashboardAgenda();
  carregarDashboardClientes();
  carregarDashboardProducao();
});