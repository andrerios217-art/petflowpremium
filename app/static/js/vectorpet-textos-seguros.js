(function () {
  if (window.__vectorpetTextosSegurosLoaded) return;
  window.__vectorpetTextosSegurosLoaded = true;

  function deveRodarNestaPagina() {
    const path = window.location.pathname || "";
    return path.includes("/agenda") || path.includes("/producao");
  }

  function limparTexto(texto) {
    if (!texto) return texto;

    let novo = String(texto);

    novo = novo.replace(/Confirmar etapa(?:\s+etapa)+/gi, "Confirmar etapa");
    novo = novo.replace(/REGISTRO DA ETAPA(?:\s+DA ETAPA)+/g, "REGISTRO DA ETAPA");
    novo = novo.replace(/Registro da etapa(?:\s+da etapa)+/gi, "Registro da etapa");

    novo = novo.replace(/Finalizar atendimento(?:\s+atendimento)+/gi, "Finalizar atendimento");
    novo = novo.replace(/Iniciar atendimento(?:\s+atendimento)+/gi, "Iniciar atendimento");
    novo = novo.replace(/Salvar atendimento(?:\s+atendimento)+/gi, "Salvar atendimento");
    novo = novo.replace(/Editar atendimento(?:\s+atendimento)+/gi, "Editar atendimento");

    novo = novo.replace(/Status alterado para Em atendimento\./gi, "Atendimento iniciado com sucesso.");
    novo = novo.replace(/Status alterado para Concluído\./gi, "Atendimento finalizado com sucesso.");

    return novo;
  }

  function corrigirElemento(el) {
    if (!el) return;

    const texto = (el.textContent || "").trim();

    if (!texto) return;

    if (el.tagName === "BUTTON") {
      if (/Confirmar etapa/i.test(texto)) {
        el.textContent = "Confirmar etapa";
        return;
      }

      if (/Finalizar atendimento/i.test(texto)) {
        el.textContent = "Finalizar atendimento";
        return;
      }

      if (/Iniciar atendimento/i.test(texto)) {
        el.textContent = "Iniciar atendimento";
        return;
      }

      if (/Salvar atendimento/i.test(texto)) {
        el.textContent = "Salvar atendimento";
        return;
      }
    }

    if (
      el.children.length === 0 &&
      (
        /etapa etapa/i.test(texto) ||
        /atendimento atendimento/i.test(texto) ||
        /Registro da etapa/i.test(texto) ||
        /Status alterado para Em atendimento/i.test(texto)
      )
    ) {
      el.textContent = limparTexto(texto);
      return;
    }

    el.childNodes.forEach(function (node) {
      if (node.nodeType === Node.TEXT_NODE) {
        const limpo = limparTexto(node.nodeValue);
        if (limpo !== node.nodeValue) {
          node.nodeValue = limpo;
        }
      }
    });
  }

  function limparTela() {
    if (!deveRodarNestaPagina()) return;

    document
      .querySelectorAll("button, span, strong, label, p, div")
      .forEach(corrigirElemento);
  }

  function limparPorPoucoTempo() {
    let contador = 0;

    const timer = setInterval(function () {
      contador += 1;
      limparTela();

      if (contador >= 12) {
        clearInterval(timer);
      }
    }, 120);
  }

  document.addEventListener("DOMContentLoaded", function () {
    limparPorPoucoTempo();
  });

  window.addEventListener("load", function () {
    limparPorPoucoTempo();
  });

  document.addEventListener("click", function () {
    setTimeout(limparPorPoucoTempo, 30);
  }, true);
})();