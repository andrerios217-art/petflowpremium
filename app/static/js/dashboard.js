function formatarMoeda(valor) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL"
  }).format(Number(valor || 0));
}

function obterEmpresaId() {
  const selectEmpresa = document.getElementById("dashboard-empresa-id");
  const valorSelect = Number(selectEmpresa?.value || 0);

  if (valorSelect > 0) {
    return valorSelect;
  }

  return Number(localStorage.getItem("empresa_id") || 1);
}

function normalizarTextoDashboard(valor) {
  return String(valor ?? "")
    .replaceAll("Aten??o", "Atenção")
    .replaceAll("pr?ximas", "próximas")
    .replaceAll("pr?ximos", "próximos")
    .replaceAll("cr?ticas", "críticas")
    .replaceAll("vencida h?", "vencida há")
    .replaceAll("Pr?x.", "Próx.");
}

function escapeHtmlDashboard(valor) {
  return String(valor ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatarDataBr(valor) {
  if (!valor) return "-";

  const texto = String(valor);

  if (/^\d{4}-\d{2}-\d{2}$/.test(texto)) {
    const [ano, mes, dia] = texto.split("-");
    return `${dia}/${mes}/${ano}`;
  }

  return texto;
}

function formatarDataIso(data) {
  const ano = data.getFullYear();
  const mes = String(data.getMonth() + 1).padStart(2, "0");
  const dia = String(data.getDate()).padStart(2, "0");
  return `${ano}-${mes}-${dia}`;
}

function formatarDiasVencimento(dias) {
  const numero = Number(dias);

  if (!Number.isFinite(numero)) {
    return "sem vencimento";
  }

  if (numero < 0) {
    return `vencida há ${Math.abs(numero)} dia(s)`;
  }

  if (numero === 0) {
    return "vence hoje";
  }

  return `vence em ${numero} dia(s)`;
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

function atualizarStatusAlertaFinanceiro(resumo) {
  const status = document.getElementById("alertas-financeiros-status");
  if (!status) return;

  status.classList.remove("is-danger", "is-warning", "is-ok");

  const totalVencidas = Number(resumo.total_vencidas || 0);
  const totalHoje = Number(resumo.total_vence_hoje || 0);
  const total7 = Number(resumo.total_proximos_7_dias || 0);

  if (totalVencidas > 0) {
    status.textContent = "Atenção";
    status.classList.add("is-danger");
    return;
  }

  if (totalHoje > 0 || total7 > 0) {
    status.textContent = "Monitorar";
    status.classList.add("is-warning");
    return;
  }

  status.textContent = "Em dia";
  status.classList.add("is-ok");
}

function montarMensagemAlertas(resumo) {
  const totalVencidas = Number(resumo.total_vencidas || 0);
  const totalHoje = Number(resumo.total_vence_hoje || 0);
  const total7 = Number(resumo.total_proximos_7_dias || 0);
  const total15 = Number(resumo.total_proximos_15_dias || 0);

  if (totalVencidas > 0) {
    return `Atenção: existem ${formatarMoeda(totalVencidas)} em contas vencidas.`;
  }

  if (totalHoje > 0) {
    return `Atenção: existem ${formatarMoeda(totalHoje)} em contas vencendo hoje.`;
  }

  if (total7 > 0) {
    return `Nos próximos 7 dias há ${formatarMoeda(total7)} em contas a pagar.`;
  }

  if (total15 > 0) {
    return `Nos próximos 15 dias há ${formatarMoeda(total15)} em contas a pagar.`;
  }

  return "Nenhuma conta crítica a vencer nos próximos dias.";
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

async function carregarAlertasFinanceiros() {
  try {
    const empresaId = obterEmpresaId();
    const response = await fetch(`/api/financeiro/dashboard/alertas?empresa_id=${empresaId}&dias=15&limite=6`);

    if (!response.ok) {
      throw new Error("Erro ao carregar alertas financeiros");
    }

    const data = await response.json();
    const resumo = data.resumo || {};
    const principais = Array.isArray(data.principais) ? data.principais : [];

    const totalVencidas = document.getElementById("alertas-total-vencidas");
    const totalHoje = document.getElementById("alertas-total-hoje");
    const total7 = document.getElementById("alertas-total-7");
    const totalCriticas = document.getElementById("alertas-total-criticas");
    const mensagem = document.getElementById("alertas-financeiros-mensagem");
    const lista = document.getElementById("alertas-financeiros-lista");

    if (totalVencidas) {
      totalVencidas.textContent = formatarMoeda(resumo.total_vencidas || 0);
    }

    if (totalHoje) {
      totalHoje.textContent = formatarMoeda(resumo.total_vence_hoje || 0);
    }

    if (total7) {
      total7.textContent = formatarMoeda(resumo.total_proximos_7_dias || 0);
    }

    if (totalCriticas) {
      totalCriticas.textContent = formatarMoeda(resumo.total_criticas || 0);
    }

    if (mensagem) {
      mensagem.textContent = normalizarTextoDashboard(montarMensagemAlertas(resumo));
    }

    atualizarStatusAlertaFinanceiro(resumo);

    if (!lista) return;

    if (!principais.length) {
      lista.innerHTML = `<li>Nenhuma conta a vencer encontrada.</li>`;
      return;
    }

    lista.innerHTML = principais.map((conta) => {
      const classificacao = [
        conta.grupo_dre,
        conta.categoria_dre,
        conta.subcategoria_dre
      ].filter(Boolean).join(" › ");

      return `
        <li>
          <div class="dashboard-alerta-conta-info">
            <strong>${escapeHtmlDashboard(conta.descricao || "Conta a pagar")}</strong>
            <span>
              ${escapeHtmlDashboard(conta.fornecedor || "Fornecedor não informado")}
              - ${escapeHtmlDashboard(formatarDiasVencimento(conta.dias_para_vencer))}
              - ${escapeHtmlDashboard(formatarDataBr(conta.vencimento))}
              ${classificacao ? " - " + escapeHtmlDashboard(classificacao) : ""}
            </span>
          </div>
          <div class="dashboard-alerta-conta-valor">
            ${formatarMoeda(conta.valor || 0)}
          </div>
        </li>
      `;
    }).join("");
  } catch (error) {
    console.error("Erro ao carregar alertas financeiros:", error);

    const status = document.getElementById("alertas-financeiros-status");
    const mensagem = document.getElementById("alertas-financeiros-mensagem");
    const lista = document.getElementById("alertas-financeiros-lista");

    if (status) {
      status.textContent = "Erro";
      status.classList.remove("is-ok", "is-warning");
      status.classList.add("is-danger");
    }

    if (mensagem) {
      mensagem.textContent = "Não foi possível carregar os alertas financeiros.";
    }

    if (lista) {
      lista.innerHTML = `<li>Verifique o endpoint de alertas financeiros.</li>`;
    }
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

function configurarLinksAlertasFinanceiros() {
  document.querySelectorAll("[data-alerta-financeiro-link]").forEach((card) => {
    card.addEventListener("click", () => {
      const tipo = card.dataset.alertaFinanceiroLink || "";
      const empresaId = obterEmpresaId();

      const params = new URLSearchParams();
      params.set("empresa_id", String(empresaId));
      params.set("modo", "pagar");

      if (tipo === "vencidas") {
        params.set("status", "VENCIDO");
      }

      if (tipo === "hoje") {
        params.set("status", "PENDENTE");
        params.set("vencimento", "hoje");
      }

      if (tipo === "proximos7") {
        params.set("status", "PENDENTE");
        params.set("vencimento", "proximos7");
      }

      if (tipo === "criticas") {
        params.set("status", "PENDENTE");
        params.set("alerta", "criticas");
      }

      window.location.href = `/financeiro?${params.toString()}`;
    });
  });
}

function recarregarDashboard() {
  carregarDashboardFinanceiro();
  carregarAlertasFinanceiros();
  carregarDashboardAgenda();
  carregarDashboardClientes();
  carregarDashboardProducao();
}

document.addEventListener("DOMContentLoaded", () => {
  const selectEmpresa = document.getElementById("dashboard-empresa-id");

  configurarLinksAlertasFinanceiros();

  if (selectEmpresa) {
    const empresaSalva = Number(localStorage.getItem("empresa_id") || 1);
    selectEmpresa.value = String(empresaSalva > 0 ? empresaSalva : 1);

    selectEmpresa.addEventListener("change", () => {
      localStorage.setItem("empresa_id", selectEmpresa.value);
      recarregarDashboard();
    });
  }

  recarregarDashboard();
});
