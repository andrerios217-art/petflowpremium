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

    function limparStoragesDeTema() {
        const themeKeys = [
            "petflow_theme",
            "theme",
            "color-theme",
            "darkMode",
            "modo_escuro",
            "tema",
        ];

        themeKeys.forEach((key) => {
            try {
                localStorage.removeItem(key);
            } catch (error) {
                console.warn(`Não foi possível limpar ${key} do localStorage:`, error);
            }

            try {
                sessionStorage.removeItem(key);
            } catch (error) {
                console.warn(`Não foi possível limpar ${key} do sessionStorage:`, error);
            }
        });
    }

    function removerClassesTemaEscuro(element) {
        if (!element || !element.classList) {
            return;
        }

        element.classList.remove(
            "dark",
            "theme-dark",
            "dark-mode",
            "modo-escuro",
            "is-dark"
        );
    }

    function removerBotoesTema() {
        const seletores = [
            "#theme-toggle-btn",
            "[data-theme-toggle]",
            "[data-action='toggle-theme']",
            ".theme-toggle",
            ".theme-switch",
            ".dark-mode-toggle",
        ];

        seletores.forEach((seletor) => {
            document.querySelectorAll(seletor).forEach((elemento) => elemento.remove());
        });
    }

    function garantirTemaClaro() {
        limparStoragesDeTema();

        document.documentElement.removeAttribute("data-theme");
        document.body?.removeAttribute("data-theme");

        removerClassesTemaEscuro(document.documentElement);
        removerClassesTemaEscuro(document.body);

        removerBotoesTema();
    }

    function observarMutacoesTema() {
        const observer = new MutationObserver((mutations) => {
            let deveReaplicarTemaClaro = false;

            mutations.forEach((mutation) => {
                if (mutation.type === "attributes") {
                    deveReaplicarTemaClaro = true;
                }

                if (mutation.type === "childList" && mutation.addedNodes.length > 0) {
                    deveReaplicarTemaClaro = true;
                }
            });

            if (deveReaplicarTemaClaro) {
                garantirTemaClaro();
            }
        });

        observer.observe(document.documentElement, {
            subtree: true,
            childList: true,
            attributes: true,
            attributeFilter: ["data-theme", "class"],
        });
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
    observarMutacoesTema();
    aplicarPermissoesSidebar();
});