(function () {
  if (window.__vectorpetOperacaoTextos) return;
  window.__vectorpetOperacaoTextos = true;

  function limparTexto(texto) {
    if (!texto) return texto;

    return String(texto)
      .replace(/Confirmar etapa(?:\s+etapa)+/gi, "Confirmar etapa")
      .replace(/Finalizar atendimento(?:\s+atendimento)+/gi, "Finalizar atendimento")
      .replace(/Iniciar atendimento(?:\s+atendimento)+/gi, "Iniciar atendimento")
      .replace(/Salvar atendimento(?:\s+atendimento)+/gi, "Salvar atendimento")
      .replace(/Registro da etapa(?:\s+da etapa)+/gi, "Registro da etapa")
      .replace(/REGISTRO DA ETAPA(?:\s+DA ETAPA)+/gi, "REGISTRO DA ETAPA")
      .replace(/Status alterado para Em atendimento\./gi, "Atendimento iniciado com sucesso.");
  }

  function corrigirOperacao() {
    const btnProducao = document.getElementById("confirmar-acao-producao");
    if (btnProducao) {
      btnProducao.textContent = "Confirmar etapa";
    }

    const btnFinalizarAgenda = document.getElementById("btn-finalizar-agendamento");
    if (btnFinalizarAgenda) {
      btnFinalizarAgenda.textContent = "Finalizar atendimento";
    }

    const btnIniciarAgenda = document.getElementById("btn-iniciar-agendamento");
    if (btnIniciarAgenda) {
      btnIniciarAgenda.textContent = "Iniciar atendimento";
    }

    document.querySelectorAll("button, span, strong, small, p, label, .section-badge, .success-btn, .btn-primary").forEach(function (el) {
      const texto = el.textContent || "";

      if (
        texto.includes("etapa etapa") ||
        texto.includes("atendimento atendimento") ||
        texto.includes("da etapa da etapa") ||
        texto.includes("DA ETAPA DA ETAPA") ||
        texto.includes("Status alterado para Em atendimento")
      ) {
        el.textContent = limparTexto(texto);
      }
    });
  }

  function corrigirEmRajada() {
    [0, 40, 90, 160, 260, 420, 700].forEach(function (tempo) {
      setTimeout(corrigirOperacao, tempo);
    });
  }

  document.addEventListener("DOMContentLoaded", corrigirEmRajada);
  window.addEventListener("load", corrigirEmRajada);

  document.addEventListener("click", function () {
    corrigirEmRajada();
  }, true);

  document.addEventListener("change", function () {
    corrigirEmRajada();
  }, true);
})();