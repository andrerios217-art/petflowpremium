console.log("Pet Flow Premium frontend carregado");

document.addEventListener("DOMContentLoaded", () => {
  const permissoes = JSON.parse(
    localStorage.getItem("petflow_permissoes") ||
    sessionStorage.getItem("petflow_permissoes") ||
    "{}"
  );

  const tipoUsuario =
    localStorage.getItem("petflow_tipo_usuario") ||
    sessionStorage.getItem("petflow_tipo_usuario") ||
    "";

  if (tipoUsuario === "funcionario") {
    document.querySelectorAll(".sidebar-nav .nav-item").forEach(item => {
      const href = item.getAttribute("href");

      const mapa = {
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

      const chave = mapa[href];
      if (chave && !permissoes[chave]) {
        item.style.display = "none";
      }
    });
  }
});
