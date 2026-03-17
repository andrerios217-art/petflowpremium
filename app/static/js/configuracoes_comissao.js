let faixas = [];

function criarFaixa(min = "", max = "", valor = "") {
  return { min, max, valor };
}

function renderFaixas() {
  const container = document.getElementById("faixas-container");
  container.innerHTML = "";

  faixas.forEach((f, index) => {
    const row = document.createElement("div");
    row.className = "faixa-row";

    row.innerHTML = `
      <input type="number" class="faixa-min" value="${f.min}">
      <input type="number" class="faixa-max" value="${f.max}">
      <input type="number" class="faixa-valor" value="${f.valor}">
      <button class="btn-remove" data-index="${index}">✕</button>
    `;

    container.appendChild(row);
  });

  validarFaixas();
}

function validarFaixas() {
  const warning = document.getElementById("faixa-warning");
  warning.innerText = "";

  let erro = "";

  const ordenadas = [...faixas].sort((a, b) => a.min - b.min);

  if (ordenadas.length > 0 && Number(ordenadas[0].min) !== 0) {
    erro = "A primeira faixa deve começar em 0.";
  }

  for (let i = 0; i < ordenadas.length - 1; i++) {
    const atual = ordenadas[i];
    const prox = ordenadas[i + 1];

    if (Number(atual.max) >= Number(prox.min)) {
      erro = "Faixas estão sobrepostas.";
    }
  }

  warning.innerText = erro;
}

function atualizarFaixasDoDOM() {
  const rows = document.querySelectorAll(".faixa-row");

  faixas = Array.from(rows).map((row) => {
    return {
      min: Number(row.querySelector(".faixa-min").value),
      max: Number(row.querySelector(".faixa-max").value),
      valor: Number(row.querySelector(".faixa-valor").value)
    };
  });

  validarFaixas();
}

function adicionarFaixa() {
  faixas.push(criarFaixa());
  renderFaixas();
}

function removerFaixa(index) {
  faixas.splice(index, 1);
  renderFaixas();
}

function montarPayload() {
  atualizarFaixasDoDOM();

  return {
    pontos: {
      banho: Number(document.getElementById("pontos_banho").value),
      tosa: Number(document.getElementById("pontos_tosa").value),
      finalizacao: Number(document.getElementById("pontos_finalizacao").value),
    },
    regras: {
      dias_trabalhados: Number(document.getElementById("dias_trabalhados").value),
      responsavel: document.getElementById("responsavel_nome").value
    },
    faixas: faixas
  };
}

function salvarConfiguracao() {
  const payload = montarPayload();

  console.log("Payload pronto:", payload);

  // próxima etapa: POST para backend
}

document.addEventListener("DOMContentLoaded", () => {

  faixas = [
    { min: 0, max: 9, valor: 0 }
  ];

  renderFaixas();

  document.getElementById("btn-add-faixa").onclick = adicionarFaixa;

  document.getElementById("faixas-container").addEventListener("input", atualizarFaixasDoDOM);

  document.getElementById("faixas-container").addEventListener("click", (e) => {
    if (e.target.classList.contains("btn-remove")) {
      removerFaixa(Number(e.target.dataset.index));
    }
  });

  document.getElementById("btn-salvar").onclick = salvarConfiguracao;

  document.getElementById("btn-reset").onclick = () => {
    location.reload();
  };
});