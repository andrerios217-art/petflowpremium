console.log("Pet Flow Premium frontend carregado");

document.addEventListener("DOMContentLoaded", () => {
  function obterPermissoes() {
    try {
      const local = localStorage.getItem("petflow_permissoes");
      const session = sessionStorage.getItem("petflow_permissoes");

      if (local) return JSON.parse(local);
      if (session) return JSON.parse(session);

      return {};
    } catch (error) {
      console.warn("Erro ao ler permissões:", error);
      return {};
    }
  }

  function obterTipoUsuario() {
    return (
      localStorage.getItem("petflow_tipo_usuario") ||
      sessionStorage.getItem("petflow_tipo_usuario") ||
      ""
    );
  }

  function obterTemaAtual() {
    return document.documentElement.getAttribute("data-theme") || "light";
  }

  function salvarTema(tema) {
    try {
      localStorage.setItem("petflow_theme", tema);
    } catch (error) {
      console.warn("Não foi possível salvar o tema:", error);
    }
  }

  function aplicarTema(tema) {
    const temaNormalizado = tema === "dark" ? "dark" : "light";

    document.documentElement.setAttribute("data-theme", temaNormalizado);
    salvarTema(temaNormalizado);
    atualizarBotaoTema(temaNormalizado);
  }

  function atualizarBotaoTema(tema) {
    const botao = document.getElementById("theme-toggle-btn");
    const icone = document.getElementById("theme-toggle-icon");
    const texto = document.getElementById("theme-toggle-text");

    if (!botao || !icone || !texto) return;

    if (tema === "dark") {
      icone.textContent = "☀️";
      texto.textContent = "Modo claro";
      botao.setAttribute("aria-label", "Ativar modo claro");
      botao.setAttribute("title", "Ativar modo claro");
    } else {
      icone.textContent = "🌙";
      texto.textContent = "Modo escuro";
      botao.setAttribute("aria-label", "Ativar modo escuro");
      botao.setAttribute("title", "Ativar modo escuro");
    }
  }

  function alternarTema() {
    const temaAtual = obterTemaAtual();
    const novoTema = temaAtual === "dark" ? "light" : "dark";
    aplicarTema(novoTema);
  }

  const permissoes = obterPermissoes();
  const tipoUsuario = obterTipoUsuario();

  if (tipoUsuario === "funcionario") {
    const mapaPermissoes = {
      "/dashboard": "dashboard",
      "/clientes": "clientes",
      "/pets": "pets",
      "/servicos": "servicos",
      "/funcionarios": "funcionarios",
      "/agenda": "agenda",
      "/producao": "producao",
      "/estoque": "estoque",
      "/financeiro": "financeiro",
      "/crm": "crm",
      "/relatorios": "relatorios",
      "/configuracoes": "configuracoes"
    };

    const itensSidebar = document.querySelectorAll(".sidebar-nav .nav-item");

    itensSidebar.forEach((item) => {
      const href = item.getAttribute("href");

      if (!href) return;

      const chavePermissao = mapaPermissoes[href];

      if (chavePermissao && !permissoes[chavePermissao]) {
        item.style.display = "none";
      }
    });
  }

  const themeToggleBtn = document.getElementById("theme-toggle-btn");
  atualizarBotaoTema(obterTemaAtual());

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", alternarTema);
  }
});