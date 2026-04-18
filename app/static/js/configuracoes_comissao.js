(function () {
  let faixas = [];

  document.addEventListener("DOMContentLoaded", init);

  async function init() {
    bindEvents();
    await carregarConfiguracao();
  }

  function bindEvents() {
    document.getElementById("btn-add-faixa")?.addEventListener("click", adicionarFaixaVazia);
    document.getElementById("btn-reset")?.addEventListener("click", async () => {
      await carregarConfiguracao();
    });
    document.getElementById("btn-salvar")?.addEventListener("click", salvarConfiguracao);

    document.getElementById("faixas-container")?.addEventListener("input", (event) => {
      const inputValor = event.target.closest(".faixa-valor");
      if (inputValor) {
        aplicarMascaraMoeda(inputValor);
      }
      sincronizarFaixasDoDOM();
    });

    document.getElementById("faixas-container")?.addEventListener("change", (event) => {
      const checkboxAberta = event.target.closest(".faixa-max-aberta");
      if (checkboxAberta) {
        const row = checkboxAberta.closest(".commission-range-row");
        const inputMax = row?.querySelector(".faixa-max");
        if (inputMax) {
          if (checkboxAberta.checked) {
            inputMax.value = "";
            inputMax.disabled = true;
            inputMax.placeholder = "∞";
          } else {
            inputMax.disabled = false;
            inputMax.placeholder = "Até";
          }
        }
      }
      sincronizarFaixasDoDOM();
      renderFaixas();
    });

    document.getElementById("faixas-container")?.addEventListener("click", (event) => {
      const botaoRemover = event.target.closest("[data-action='remover-faixa']");
      if (!botaoRemover) return;

      const index = Number(botaoRemover.dataset.index);
      removerFaixa(index);
    });

    [
      "pontos_banho",
      "pontos_tosa",
      "pontos_tosa_higienica",
      "pontos_finalizacao",
      "dias_trabalhados_mes",
      "responsavel_aprovacao",
    ].forEach((id) => {
      document.getElementById(id)?.addEventListener("input", () => {
        atualizarPreview();
      });
    });
  }

  function resolveEmpresaId() {
    const candidatos = [
      window.APP_EMPRESA_ID,
      window.empresaId,
      localStorage.getItem("empresa_id"),
      localStorage.getItem("petflow_empresa_id"),
      sessionStorage.getItem("empresa_id"),
      sessionStorage.getItem("petflow_empresa_id"),
      1,
    ];

    for (const valor of candidatos) {
      const numero = Number(valor);
      if (Number.isInteger(numero) && numero > 0) {
        return numero;
      }
    }

    return 1;
  }

  async function fetchJsonSafe(url, options = {}, defaultError = "Erro na requisição.") {
    const response = await fetch(url, options);
    const raw = await response.text();

    let data = null;

    try {
      data = raw ? JSON.parse(raw) : null;
    } catch (error) {
      if (!response.ok) {
        throw new Error(raw || defaultError);
      }
      throw new Error(raw || defaultError);
    }

    if (!response.ok) {
      throw new Error(data?.detail || data?.message || raw || defaultError);
    }

    return data;
  }

  async function carregarConfiguracao() {
    try {
      const empresaId = resolveEmpresaId();

      const data = await fetchJsonSafe(
        `/api/comissao/configuracao?empresa_id=${empresaId}`,
        {},
        "Erro ao carregar configuração de comissão."
      );

      document.getElementById("pontos_banho").value = Number(data.pontos_banho || 0);
      document.getElementById("pontos_tosa").value = Number(data.pontos_tosa || 0);
      document.getElementById("pontos_tosa_higienica").value = Number(data.pontos_tosa_higienica || 0);
      document.getElementById("pontos_finalizacao").value = Number(data.pontos_finalizacao || 0);
      document.getElementById("dias_trabalhados_mes").value = Number(data.dias_trabalhados_mes || 26);
      document.getElementById("responsavel_aprovacao").value = data.responsavel_aprovacao || "";

      faixas = Array.isArray(data.faixas) && data.faixas.length
        ? data.faixas.map((faixa) => ({
            pontos_min: Number(faixa.pontos_min ?? 0),
            pontos_max: faixa.pontos_max === null || faixa.pontos_max === undefined || faixa.pontos_max === ""
              ? null
              : Number(faixa.pontos_max),
            valor_reais: Number(faixa.valor_reais ?? 0),
          }))
        : [
            {
              pontos_min: 0,
              pontos_max: 9,
              valor_reais: 0,
            },
          ];

      renderFaixas();
      atualizarPreview();
      esconderAviso();
    } catch (error) {
      console.error(error);
      showToast(error.message || "Erro ao carregar configuração.", "error");
    }
  }

  function criarFaixa(pontosMin = 0, pontosMax = 0, valorReais = 0) {
    return {
      pontos_min: Number(pontosMin || 0),
      pontos_max:
        pontosMax === null || pontosMax === undefined || pontosMax === ""
          ? null
          : Number(pontosMax),
      valor_reais: Number(valorReais || 0),
    };
  }

  function adicionarFaixaVazia() {
    sincronizarFaixasDoDOM();

    const ultima = faixas.length ? faixas[faixas.length - 1] : null;
    let novoMin = 0;

    if (ultima) {
      if (ultima.pontos_max === null) {
        showToast("A última faixa já está aberta. Feche-a antes de adicionar outra.", "error");
        return;
      }
      novoMin = Number(ultima.pontos_max) + 1;
    }

    faixas.push(criarFaixa(novoMin, novoMin, 0));
    renderFaixas();
    atualizarPreview();
  }

  function removerFaixa(index) {
    if (faixas.length <= 1) {
      showToast("É necessário manter ao menos uma faixa.", "error");
      return;
    }

    faixas.splice(index, 1);
    renderFaixas();
    atualizarPreview();
  }

  function renderFaixas() {
    const container = document.getElementById("faixas-container");
    if (!container) return;

    container.innerHTML = faixas
      .map((faixa, index) => {
        const aberta = faixa.pontos_max === null;

        return `
          <div class="commission-range-row" data-index="${index}">
            <input
              type="number"
              class="commission-input faixa-min"
              min="0"
              step="1"
              value="${Number(faixa.pontos_min || 0)}"
              data-index="${index}"
            />

            <input
              type="number"
              class="commission-input faixa-max"
              min="0"
              step="1"
              value="${aberta ? "" : Number(faixa.pontos_max || 0)}"
              data-index="${index}"
              ${aberta ? "disabled" : ""}
              placeholder="${aberta ? "∞" : "Até"}"
            />

            <label class="commission-checkbox-wrap">
              <input
                type="checkbox"
                class="faixa-max-aberta"
                data-index="${index}"
                ${aberta ? "checked" : ""}
              />
              <span>Até infinito</span>
            </label>

            <input
              type="text"
              inputmode="decimal"
              class="commission-input faixa-valor"
              value="${formatCurrencyInput(faixa.valor_reais)}"
              data-index="${index}"
              placeholder="R$ 0,00"
            />

            <button
              type="button"
              class="commission-remove-btn"
              data-action="remover-faixa"
              data-index="${index}"
              title="Remover faixa"
            >
              ✕
            </button>
          </div>
        `;
      })
      .join("");
  }

  function sincronizarFaixasDoDOM() {
    const rows = Array.from(document.querySelectorAll(".commission-range-row"));

    faixas = rows.map((row) => {
      const inputMin = row.querySelector(".faixa-min");
      const inputMax = row.querySelector(".faixa-max");
      const inputValor = row.querySelector(".faixa-valor");
      const aberta = row.querySelector(".faixa-max-aberta")?.checked;

      return {
        pontos_min: Number(inputMin?.value || 0),
        pontos_max: aberta ? null : Number(inputMax?.value || 0),
        valor_reais: parseCurrencyInput(inputValor?.value || ""),
      };
    });

    atualizarPreview();
    validarFaixasVisual();
  }

  function ordenarFaixas() {
    faixas.sort((a, b) => Number(a.pontos_min || 0) - Number(b.pontos_min || 0));
  }

  function validarFaixas() {
    ordenarFaixas();

    if (!faixas.length) {
      throw new Error("Adicione ao menos uma faixa de comissão.");
    }

    if (Number(faixas[0].pontos_min) !== 0) {
      throw new Error("A primeira faixa deve começar em 0 pontos.");
    }

    let encontrouFaixaAberta = false;

    for (let i = 0; i < faixas.length; i++) {
      const faixa = faixas[i];
      const min = Number(faixa.pontos_min);
      const max = faixa.pontos_max === null ? null : Number(faixa.pontos_max);
      const valor = Number(faixa.valor_reais);

      if (!Number.isFinite(min) || min < 0) {
        throw new Error(`A faixa ${i + 1} possui início inválido.`);
      }

      if (max !== null) {
        if (!Number.isFinite(max) || max < min) {
          throw new Error(`A faixa ${i + 1} possui limite final inválido.`);
        }
      }

      if (!Number.isFinite(valor) || valor < 0) {
        throw new Error(`A faixa ${i + 1} possui valor em R$ inválido.`);
      }

      if (max === null) {
        if (encontrouFaixaAberta) {
          throw new Error("Só pode existir uma faixa aberta.");
        }
        encontrouFaixaAberta = true;

        if (i !== faixas.length - 1) {
          throw new Error("A faixa aberta deve ser a última.");
        }
      }

      if (i > 0) {
        const faixaAnterior = faixas[i - 1];
        const maxAnterior = faixaAnterior.pontos_max === null ? null : Number(faixaAnterior.pontos_max);

        if (maxAnterior === null) {
          throw new Error("Não é permitido adicionar faixa após uma faixa aberta.");
        }

        if (min !== maxAnterior + 1) {
          throw new Error(
            `As faixas devem ser contínuas. A faixa ${i + 1} deve começar em ${maxAnterior + 1}.`
          );
        }
      }
    }
  }

  function validarFaixasVisual() {
    try {
      validarFaixas();
      esconderAviso();
      return true;
    } catch (error) {
      mostrarAviso(error.message || "Erro de validação nas faixas.");
      return false;
    }
  }

  function atualizarPreview() {
    const preview = document.getElementById("commission-preview");
    if (!preview) return;

    const pontosBanho = Number(document.getElementById("pontos_banho")?.value || 0);
    const pontosTosa = Number(document.getElementById("pontos_tosa")?.value || 0);
    const pontosTosaHigienica = Number(document.getElementById("pontos_tosa_higienica")?.value || 0);
    const pontosFinalizacao = Number(document.getElementById("pontos_finalizacao")?.value || 0);

    const resumoEtapas = `
      <span class="commission-preview-line">
        <strong>Banho:</strong> ${pontosBanho} ponto(s) •
        <strong>Tosa:</strong> ${pontosTosa} ponto(s) •
        <strong>Tosa higiênica:</strong> ${pontosTosaHigienica} ponto(s) •
        <strong>Finalização:</strong> ${pontosFinalizacao} ponto(s)
      </span>
    `;

    const linhasFaixas = [...faixas]
      .sort((a, b) => Number(a.pontos_min || 0) - Number(b.pontos_min || 0))
      .map((faixa) => {
        const maxLabel = faixa.pontos_max === null ? "∞" : faixa.pontos_max;
        return `
          <span class="commission-preview-line">
            <strong>${faixa.pontos_min} a ${maxLabel} pontos</strong> = ${formatCurrency(faixa.valor_reais)}
          </span>
        `;
      });

    preview.innerHTML = [resumoEtapas, ...linhasFaixas].join("");
  }

  function mostrarAviso(message) {
    const warning = document.getElementById("faixa-warning");
    if (!warning) return;

    warning.textContent = message;
    warning.classList.remove("hidden");
  }

  function esconderAviso() {
    const warning = document.getElementById("faixa-warning");
    if (!warning) return;

    warning.textContent = "";
    warning.classList.add("hidden");
  }

  function montarPayload() {
    sincronizarFaixasDoDOM();
    validarFaixas();

    return {
      empresa_id: resolveEmpresaId(),
      pontos_banho: Number(document.getElementById("pontos_banho")?.value || 0),
      pontos_tosa: Number(document.getElementById("pontos_tosa")?.value || 0),
      pontos_tosa_higienica: Number(document.getElementById("pontos_tosa_higienica")?.value || 0),
      pontos_finalizacao: Number(document.getElementById("pontos_finalizacao")?.value || 0),
      dias_trabalhados_mes: Number(document.getElementById("dias_trabalhados_mes")?.value || 26),
      responsavel_aprovacao: document.getElementById("responsavel_aprovacao")?.value?.trim() || null,
      faixas: [...faixas]
        .sort((a, b) => Number(a.pontos_min || 0) - Number(b.pontos_min || 0))
        .map((faixa, index) => ({
          ordem: index + 1,
          pontos_min: Number(faixa.pontos_min),
          pontos_max: faixa.pontos_max === null ? null : Number(faixa.pontos_max),
          valor_reais: Number(faixa.valor_reais),
        })),
    };
  }

  async function salvarConfiguracao() {
    try {
      const payload = montarPayload();

      await fetchJsonSafe(
        "/api/comissao/configuracao",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        },
        "Erro ao salvar configuração de comissão."
      );

      showToast("Configuração de comissão salva com sucesso.");
      await carregarConfiguracao();
    } catch (error) {
      console.error(error);
      showToast(error.message || "Erro ao salvar configuração.", "error");
    }
  }

  function formatCurrency(value) {
    return Number(value || 0).toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
    });
  }

  function parseCurrencyInput(value) {
    const digits = String(value || "").replace(/\D/g, "");
    return Number(digits || 0) / 100;
  }

  function formatCurrencyInput(value) {
    return formatCurrency(Number(value || 0));
  }

  function aplicarMascaraMoeda(input) {
    if (!input) return;
    const valor = parseCurrencyInput(input.value);
    input.value = formatCurrencyInput(valor);
  }

  function showToast(message, type = "success") {
    if (window.showToast && typeof window.showToast === "function") {
      window.showToast(message, type);
      return;
    }

    console.log(message);
  }
})();