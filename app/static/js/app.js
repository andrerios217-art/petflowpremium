console.log("VectorPet frontend carregado");

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
            "/pdv": "dashboard",
            "/estoque": "estoque",
            "/notas-entrada": "estoque",
            "/precificacao": "estoque",
            "/financeiro": "financeiro",
            "/dre": "financeiro",
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

        if (document.documentElement) {
            document.documentElement.removeAttribute("data-theme");
            removerClassesTemaEscuro(document.documentElement);
        }

        if (document.body) {
            document.body.removeAttribute("data-theme");
            removerClassesTemaEscuro(document.body);
        }

        removerBotoesTema();
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

    function normalizarPath(pathname) {
        if (!pathname) return "/";
        if (pathname.length > 1 && pathname.endsWith("/")) {
            return pathname.slice(0, -1);
        }
        return pathname;
    }

    function marcarSidebarAtiva() {
        const itens = document.querySelectorAll(".sidebar .nav-item[href]");
        if (!itens.length) return;

        const pathAtual = normalizarPath(window.location.pathname);

        const alias = {
            "/": "/dashboard",
        };

        const pathResolvido = alias[pathAtual] || pathAtual;

        let itemMarcado = null;
        let maiorMatch = 0;

        itens.forEach((item) => {
            item.classList.remove("active");

            const href = item.getAttribute("href");
            if (!href || href.startsWith("javascript:") || href === "#") return;

            const pathItem = normalizarPath(href);

            const matchExato = pathResolvido === pathItem;
            const matchPorPrefixo =
                pathItem !== "/" &&
                pathResolvido.startsWith(`${pathItem}/`);

            if (matchExato || matchPorPrefixo) {
                const peso = pathItem.length;
                if (peso >= maiorMatch) {
                    maiorMatch = peso;
                    itemMarcado = item;
                }
            }
        });

        if (itemMarcado) {
            itemMarcado.classList.add("active");
        }
    }

    function garantirModalStyles() {
        if (document.getElementById("vectorpet-confirm-styles")) {
            return;
        }

        const style = document.createElement("style");
        style.id = "vectorpet-confirm-styles";
        style.textContent = `
            .vp-confirm-overlay {
                position: fixed;
                inset: 0;
                background: rgba(18, 24, 38, 0.36);
                backdrop-filter: blur(6px);
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
                z-index: 5000;
            }

            .vp-confirm-modal {
                width: 100%;
                max-width: 440px;
                background: rgba(255, 255, 255, 0.92);
                backdrop-filter: blur(18px);
                border: 1px solid rgba(255, 255, 255, 0.55);
                border-radius: 28px;
                box-shadow: 0 24px 60px rgba(15, 23, 42, 0.18);
                padding: 24px;
                animation: vpConfirmIn 0.18s ease;
            }

            .vp-confirm-header {
                display: flex;
                align-items: flex-start;
                gap: 14px;
                margin-bottom: 12px;
            }

            .vp-confirm-icon {
                min-width: 52px;
                width: 52px;
                height: 52px;
                border-radius: 18px;
                display: grid;
                place-items: center;
                background: linear-gradient(135deg, #006aff, #4da0ff);
                color: #ffffff;
                font-size: 24px;
                box-shadow: 0 14px 28px rgba(0, 106, 255, 0.18);
                flex-shrink: 0;
            }

            .vp-confirm-title {
                margin: 0;
                color: #23324a;
                font-size: 1.2rem;
                font-weight: 800;
                letter-spacing: -0.02em;
            }

            .vp-confirm-description {
                margin: 6px 0 0;
                color: #78859b;
                font-size: 0.95rem;
                line-height: 1.55;
            }

            .vp-confirm-actions {
                display: flex;
                justify-content: flex-end;
                gap: 10px;
                margin-top: 20px;
                flex-wrap: wrap;
            }

            .vp-confirm-btn {
                border: none;
                border-radius: 16px;
                padding: 12px 18px;
                font-size: 0.95rem;
                font-weight: 800;
                cursor: pointer;
                transition: transform 0.18s ease, filter 0.18s ease, box-shadow 0.18s ease;
            }

            .vp-confirm-btn:hover {
                transform: translateY(-1px);
                filter: brightness(1.02);
            }

            .vp-confirm-btn-cancel {
                background: rgba(255, 255, 255, 0.86);
                color: #23324a;
                border: 1px solid rgba(0, 0, 0, 0.08);
                box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
            }

            .vp-confirm-btn-confirm {
                background: linear-gradient(135deg, #dc2626, #b91c1c);
                color: #ffffff;
                box-shadow: 0 14px 30px rgba(220, 38, 38, 0.18);
            }

            @keyframes vpConfirmIn {
                from {
                    opacity: 0;
                    transform: translateY(10px) scale(0.98);
                }
                to {
                    opacity: 1;
                    transform: translateY(0) scale(1);
                }
            }

            @media (max-width: 640px) {
                .vp-confirm-modal {
                    padding: 20px;
                    border-radius: 24px;
                }

                .vp-confirm-actions {
                    flex-direction: column-reverse;
                }

                .vp-confirm-btn {
                    width: 100%;
                }
            }
        `;
        document.head.appendChild(style);
    }

    function abrirConfirmacaoCustomizada({
        title = "Confirmar ação",
        message = "Deseja continuar?",
        confirmText = "Confirmar",
        cancelText = "Cancelar",
        icon = "⚠️",
        confirmButtonClass = "vp-confirm-btn-confirm",
        onConfirm = null,
        onCancel = null,
    }) {
        garantirModalStyles();

        const overlay = document.createElement("div");
        overlay.className = "vp-confirm-overlay";

        const modal = document.createElement("div");
        modal.className = "vp-confirm-modal";
        modal.setAttribute("role", "dialog");
        modal.setAttribute("aria-modal", "true");

        modal.innerHTML = `
            <div class="vp-confirm-header">
                <div class="vp-confirm-icon">${icon}</div>
                <div>
                    <h3 class="vp-confirm-title">${title}</h3>
                    <p class="vp-confirm-description">${message}</p>
                </div>
            </div>
            <div class="vp-confirm-actions">
                <button type="button" class="vp-confirm-btn vp-confirm-btn-cancel">${cancelText}</button>
                <button type="button" class="vp-confirm-btn ${confirmButtonClass}">${confirmText}</button>
            </div>
        `;

        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        const btnCancel = modal.querySelector(".vp-confirm-btn-cancel");
        const btnConfirm = modal.querySelector(`.${confirmButtonClass}`);

        function fechar() {
            overlay.remove();
            document.removeEventListener("keydown", onKeyDown);
        }

        function onKeyDown(event) {
            if (event.key === "Escape") {
                fechar();
                if (typeof onCancel === "function") {
                    onCancel();
                }
            }
        }

        btnCancel.addEventListener("click", () => {
            fechar();
            if (typeof onCancel === "function") {
                onCancel();
            }
        });

        btnConfirm.addEventListener("click", () => {
            fechar();
            if (typeof onConfirm === "function") {
                onConfirm();
            }
        });

        overlay.addEventListener("click", (event) => {
            if (event.target === overlay) {
                fechar();
                if (typeof onCancel === "function") {
                    onCancel();
                }
            }
        });

        document.addEventListener("keydown", onKeyDown);
    }

    function limparSessaoPetFlow() {
        const chaves = [
            "token",
            "access_token",
            "petflow_token",
            "petflow_access_token",
            "petflow_tipo_usuario",
            "petflow_permissoes",
            "petflow_usuario",
            "petflow_user",
            "empresa_id",
            "petflow_empresa_id",
        ];

        chaves.forEach((chave) => {
            try {
                localStorage.removeItem(chave);
            } catch (error) {
                console.warn(`Erro ao limpar ${chave} do localStorage:`, error);
            }

            try {
                sessionStorage.removeItem(chave);
            } catch (error) {
                console.warn(`Erro ao limpar ${chave} do sessionStorage:`, error);
            }
        });
    }

    function configurarLogout() {
        const logoutLink = document.querySelector(".sidebar .nav-item-logout");
        if (!logoutLink) return;

        logoutLink.addEventListener("click", (event) => {
            event.preventDefault();

            abrirConfirmacaoCustomizada({
                title: "Encerrar sessão",
                message: "Deseja encerrar a sessão e voltar para o login?",
                confirmText: "Encerrar sessão",
                cancelText: "Cancelar",
                icon: "🚪",
                confirmButtonClass: "vp-confirm-btn-confirm",
                onConfirm: () => {
                    limparSessaoPetFlow();
                    window.location.href = "/";
                },
            });
        });
    }

    if (typeof window.showToast !== "function") {
        window.showToast = showToast;
    }

    if (typeof window.notifyToast !== "function") {
        window.notifyToast = showToast;
    }

    garantirTemaClaro();
    aplicarPermissoesSidebar();
    marcarSidebarAtiva();
    configurarLogout();
});

window.addEventListener("pageshow", () => {
    try {
        document.documentElement?.removeAttribute("data-theme");
        document.body?.removeAttribute("data-theme");

        document.documentElement?.classList.remove(
            "dark",
            "theme-dark",
            "dark-mode",
            "modo-escuro",
            "is-dark"
        );

        document.body?.classList.remove(
            "dark",
            "theme-dark",
            "dark-mode",
            "modo-escuro",
            "is-dark"
        );
    } catch (error) {
        console.warn("Erro ao reforçar tema claro no pageshow:", error);
    }
});