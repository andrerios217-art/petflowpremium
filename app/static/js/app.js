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

    function aplicarPermissoesSidebar() {
        const permissoes = obterPermissoes();
        const tipoUsuario = obterTipoUsuario();

        if (tipoUsuario !== "funcionario") {
            return;
        }

        const mapaPermissoes = {
            "/dashboard": "dashboard",
            "/clientes": "clientes",
            "/pets": "pets",
            "/servicos": "servicos",
            "/funcionarios": "funcionarios",
            "/agenda": "agenda",
            "/agenda-veterinaria": "agenda",
            "/producao": "producao",
            "/estoque": "estoque",
            "/financeiro": "financeiro",
            "/crm": "crm",
            "/relatorios": "relatorios",
            "/configuracoes": "configuracoes",
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

    function garantirTemaClaro() {
        document.documentElement.removeAttribute("data-theme");

        try {
            localStorage.removeItem("petflow_theme");
        } catch (error) {
            console.warn("Não foi possível limpar tema salvo no localStorage:", error);
        }

        try {
            sessionStorage.removeItem("petflow_theme");
        } catch (error) {
            console.warn("Não foi possível limpar tema salvo no sessionStorage:", error);
        }

        const botaoTema = document.getElementById("theme-toggle-btn");
        if (botaoTema) {
            botaoTema.remove();
        }
    }

    function criarContainerToast() {
        let container = document.getElementById("toast-container");

        if (container) {
            return container;
        }

        container = document.createElement("div");
        container.id = "toast-container";
        container.className = "toast-container";
        document.body.appendChild(container);

        return container;
    }

    function showToast(message, type = "success") {
        if (!message) return;

        const container = criarContainerToast();
        const toast = document.createElement("div");

        toast.className = `toast toast-${type}`;
        toast.textContent = message;

        container.appendChild(toast);

        requestAnimationFrame(() => {
            toast.classList.add("show");
        });

        setTimeout(() => {
            toast.classList.remove("show");
            setTimeout(() => {
                toast.remove();
            }, 250);
        }, 3000);
    }

    if (typeof window.showToast !== "function") {
        window.showToast = showToast;
    }

    garantirTemaClaro();
    aplicarPermissoesSidebar();
});