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

async function carregarDashboardFinanceiro() {
  try {
    const empresaId = obterEmpresaId();

    const response = await fetch(`/api/financeiro/dashboard/?empresa_id=${empresaId}`);

    if (!response.ok) {
      throw new Error("Erro ao carregar dashboard financeiro");
    }

    const data = await response.json();
    const resumo = data.resumo || {};

    const cardFaturamentoHoje = document.getElementById("card-faturamento-hoje");
    const finCaixaStatus = document.getElementById("fin-caixa-status");
    const finEntradasHoje = document.getElementById("fin-entradas-hoje");
    const finSaidasHoje = document.getElementById("fin-saidas-hoje");
    const finLucroHoje = document.getElementById("fin-lucro-hoje");
    const finReceberAberto = document.getElementById("fin-receber-aberto");
    const finPagarAberto = document.getElementById("fin-pagar-aberto");

    if (cardFaturamentoHoje) {
      cardFaturamentoHoje.textContent = formatarMoeda(resumo.entradas_hoje);
    }

    aplicarStatusCaixa(finCaixaStatus, resumo.caixa_status);

    if (finEntradasHoje) {
      finEntradasHoje.textContent = formatarMoeda(resumo.entradas_hoje);
    }

    if (finSaidasHoje) {
      finSaidasHoje.textContent = formatarMoeda(resumo.saidas_hoje);
    }

    if (finLucroHoje) {
      finLucroHoje.textContent = formatarMoeda(resumo.lucro_hoje);
      aplicarClasseLucro(finLucroHoje, resumo.lucro_hoje);
    }

    if (finReceberAberto) {
      finReceberAberto.textContent = formatarMoeda(resumo.receber_aberto);
    }

    if (finPagarAberto) {
      finPagarAberto.textContent = formatarMoeda(resumo.pagar_aberto);
    }
  } catch (error) {
    console.error("Erro ao carregar resumo financeiro:", error);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  carregarDashboardFinanceiro();
});