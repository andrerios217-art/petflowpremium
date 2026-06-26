(function () {
  if (window.__vpNormalizarTextosOperacaoV4) return;
  window.__vpNormalizarTextosOperacaoV4 = true;

  function limparTexto(texto) {
    if (!texto) return texto;

    return String(texto)
      .replace(/Confirmar etapa(?:\s+etapa)+/gi, "Confirmar etapa")
      .replace(/Finalizar atendimento(?:\s+atendimento)+/gi, "Finalizar atendimento")
      .replace(/Iniciar atendimento(?:\s+atendimento)+/gi, "Iniciar atendimento")
      .replace(/Salvar atendimento(?:\s+atendimento)+/gi, "Salvar atendimento")
      .replace(/Editar atendimento(?:\s+atendimento)+/gi, "Editar atendimento")
      .replace(/Registro da etapa(?:\s+da etapa)+/gi, "Registro da etapa")
      .replace(/REGISTRO DA ETAPA(?:\s+DA ETAPA)+/gi, "REGISTRO DA ETAPA")
      .replace(/Status alterado para Em atendimento\./gi, "Atendimento iniciado com sucesso.")
      .replace(/Status alterado para Concluído\./gi, "Atendimento finalizado com sucesso.");
  }

  function corrigirElemento(el) {
    if (!el) return;

    const texto = (el.textContent || "").trim();

    if (!texto) return;

    if (el.id === "confirmar-acao-producao") {
      el.textContent = "Confirmar etapa";
      return;
    }

    if (el.id === "btn-finalizar-agendamento") {
      el.textContent = "Finalizar atendimento";
      return;
    }

    if (el.id === "btn-iniciar-agendamento") {
      el.textContent = "Iniciar atendimento";
      return;
    }

    if (
      texto.includes("etapa etapa") ||
      texto.includes("atendimento atendimento") ||
      texto.includes("da etapa da etapa") ||
      texto.includes("DA ETAPA DA ETAPA") ||
      texto.includes("Status alterado para Em atendimento") ||
      texto.includes("Status alterado para Concluído")
    ) {
      el.textContent = limparTexto(texto);
    }
  }

  function corrigirTela() {
    const path = window.location.pathname || "";

    if (!path.includes("/producao") && !path.includes("/agenda")) {
      return;
    }

    [
      document.getElementById("confirmar-acao-producao"),
      document.getElementById("btn-finalizar-agendamento"),
      document.getElementById("btn-iniciar-agendamento")
    ].forEach(corrigirElemento);

    document
      .querySelectorAll("button, span, strong, small, p, label, .section-badge, .success-btn, .btn-primary")
      .forEach(corrigirElemento);
  }

  function corrigirEmRajada() {
    let contador = 0;

    const timer = setInterval(function () {
      contador += 1;
      corrigirTela();

      if (contador >= 25) {
        clearInterval(timer);
      }
    }, 80);
  }

  document.addEventListener("DOMContentLoaded", corrigirEmRajada);
  window.addEventListener("load", corrigirEmRajada);

  document.addEventListener("click", function () {
    setTimeout(corrigirEmRajada, 20);
  }, true);

  document.addEventListener("change", function () {
    setTimeout(corrigirEmRajada, 20);
  }, true);
})();