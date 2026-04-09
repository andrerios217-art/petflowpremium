document.addEventListener("DOMContentLoaded", () => {
    const competenciaInicioInput = document.getElementById("dreCompetenciaInicio");
    const competenciaFimInput = document.getElementById("dreCompetenciaFim");
    const modoVisualizacaoSelect = document.getElementById("dreModoVisualizacao");
    const btnAplicarFiltros = document.getElementById("btnAplicarFiltrosDre");

    const resumoReceita = document.getElementById("dreResumoReceita");
    const resumoDespesa = document.getElementById("dreResumoDespesa");
    const resumoResultado = document.getElementById("dreResumoResultado");

    const tabelaBody = document.getElementById("dreTabelaBody");
    const linhaTemplate = document.getElementById("dreLinhaTemplate");

    const estado = {
        dados: null,
        expandido: new Set()
    };

    inicializarCompetencias();
    registrarEventos();
    carregarDre();

    function registrarEventos() {
        if (btnAplicarFiltros) {
            btnAplicarFiltros.addEventListener("click", carregarDre);
        }

        if (modoVisualizacaoSelect) {
            modoVisualizacaoSelect.addEventListener("change", renderizarTabela);
        }

        if (tabelaBody) {
            tabelaBody.addEventListener("click", (event) => {
                const botao = event.target.closest("[data-toggle='expandir']");
                if (!botao) return;

                const row = botao.closest("tr");
                if (!row) return;

                const chave = row.dataset.chave;
                if (!chave) return;

                if (estado.expandido.has(chave)) {
                    estado.expandido.delete(chave);
                } else {
                    estado.expandido.add(chave);
                }

                renderizarTabela();
            });
        }
    }

    function inicializarCompetencias() {
        const hoje = new Date();
        const ano = hoje.getFullYear();
        const mes = String(hoje.getMonth() + 1).padStart(2, "0");

        const competenciaAtual = `${ano}-${mes}`;
        const inicioAno = `${ano}-01`;

        if (competenciaInicioInput && !competenciaInicioInput.value) {
            competenciaInicioInput.value = inicioAno;
        }

        if (competenciaFimInput && !competenciaFimInput.value) {
            competenciaFimInput.value = competenciaAtual;
        }
    }

    async function carregarDre() {
        setLoading();

        try {
            const empresaId = obterEmpresaId();
            if (!empresaId) {
                throw new Error("Empresa não identificada");
            }

            const competencia_inicio = competenciaInicioInput?.value || "";
            const competencia_fim = competenciaFimInput?.value || "";

            const params = new URLSearchParams();
            params.append("empresa_id", String(empresaId));

            if (competencia_inicio) {
                params.append("competencia_inicio", competencia_inicio);
            }

            if (competencia_fim) {
                params.append("competencia_fim", competencia_fim);
            }

            const response = await fetch(`/api/financeiro/dashboard/?${params.toString()}`, {
                headers: {
                    Authorization: `Bearer ${localStorage.getItem("token") || ""}`
                }
            });

            if (!response.ok) {
                throw new Error("Falha ao carregar DRE");
            }

            const data = await response.json();
            estado.dados = normalizarDados(data);

            renderizarResumo();
            renderizarTabela();
        } catch (error) {
            console.error("[DRE] Erro ao carregar:", error);
            renderizarErro("Não foi possível carregar o DRE.");
        }
    }

    function obterEmpresaId() {
        const candidatos = [
            localStorage.getItem("empresa_id"),
            localStorage.getItem("empresaId"),
            localStorage.getItem("id_empresa")
        ];

        for (const valor of candidatos) {
            const numero = Number(valor);
            if (numero > 0) {
                return numero;
            }
        }

        try {
            const usuario = JSON.parse(localStorage.getItem("usuario") || "{}");
            const numero = Number(usuario?.empresa_id || usuario?.empresaId || usuario?.id_empresa);
            if (numero > 0) {
                return numero;
            }
        } catch (error) {
            console.warn("[DRE] Não foi possível ler empresa do localStorage.", error);
        }

        return 1;
    }

    function normalizarDados(data) {
        const receitas = Number(data?.total_receitas || data?.receita_mes || 0);
        const despesas = Number(data?.total_despesas || data?.despesa_mes || 0);
        const resultado = Number(data?.resultado ?? data?.lucro_mes ?? (receitas - despesas));

        const grupos = Array.isArray(data?.dre_despesas_por_grupo) ? data.dre_despesas_por_grupo : [];
        const categorias = Array.isArray(data?.dre_despesas_por_categoria) ? data.dre_despesas_por_categoria : [];
        const subcategorias = Array.isArray(data?.dre_despesas_por_subcategoria)
            ? data.dre_despesas_por_subcategoria
            : [];

        const mapaCategoriasPorGrupo = new Map();
        const mapaSubcategoriasPorChave = new Map();

        categorias.forEach((item) => {
            const grupo = normalizarTexto(item?.grupo || item?.grupo_dre || "Sem grupo");
            const categoria = normalizarTexto(item?.categoria || item?.categoria_dre || "Sem categoria");

            if (!mapaCategoriasPorGrupo.has(grupo)) {
                mapaCategoriasPorGrupo.set(grupo, []);
            }

            mapaCategoriasPorGrupo.get(grupo).push({
                nome: categoria,
                valor: Number(item?.valor ?? item?.total ?? 0),
                tipo: "Despesa",
                filhos: []
            });
        });

        subcategorias.forEach((item) => {
            const grupo = normalizarTexto(item?.grupo || item?.grupo_dre || "Sem grupo");
            const categoria = normalizarTexto(item?.categoria || item?.categoria_dre || "Sem categoria");
            const subcategoria = normalizarTexto(
                item?.subcategoria || item?.subcategoria_dre || "Sem subcategoria"
            );

            const chave = `${grupo}|||${categoria}`;

            if (!mapaSubcategoriasPorChave.has(chave)) {
                mapaSubcategoriasPorChave.set(chave, []);
            }

            mapaSubcategoriasPorChave.get(chave).push({
                nome: subcategoria,
                valor: Number(item?.valor ?? item?.total ?? 0),
                tipo: "Despesa"
            });
        });

        const estruturaGrupos = grupos.map((grupoItem) => {
            const nomeGrupo = normalizarTexto(grupoItem?.grupo || grupoItem?.grupo_dre || "Sem grupo");
            const categoriasDoGrupo = (mapaCategoriasPorGrupo.get(nomeGrupo) || []).map((categoria) => {
                const chave = `${nomeGrupo}|||${categoria.nome}`;
                return {
                    ...categoria,
                    filhos: mapaSubcategoriasPorChave.get(chave) || []
                };
            });

            return {
                nome: nomeGrupo,
                valor: Number(grupoItem?.valor ?? grupoItem?.total ?? 0),
                tipo: "Despesa",
                filhos: categoriasDoGrupo
            };
        });

        return {
            receitas,
            despesas,
            resultado,
            grupos: estruturaGrupos
        };
    }

    function renderizarResumo() {
        if (!estado.dados) return;

        resumoReceita.textContent = formatarMoeda(estado.dados.receitas);
        resumoDespesa.textContent = formatarMoeda(estado.dados.despesas);
        resumoResultado.textContent = formatarMoeda(estado.dados.resultado);

        resumoResultado.classList.remove("text-danger", "text-success");
        if (estado.dados.resultado < 0) {
            resumoResultado.classList.add("text-danger");
        } else {
            resumoResultado.classList.add("text-success");
        }
    }

    function renderizarTabela() {
        if (!estado.dados || !tabelaBody) return;

        const modo = modoVisualizacaoSelect?.value || "agrupado";
        tabelaBody.innerHTML = "";

        const linhas = modo === "lista" ? montarLinhasLista() : montarLinhasAgrupadas();

        if (!linhas.length) {
            tabelaBody.innerHTML = `
                <tr>
                    <td colspan="5" class="dre-empty">Nenhum dado encontrado para o período informado.</td>
                </tr>
            `;
            return;
        }

        linhas.forEach((linha) => {
            tabelaBody.appendChild(criarLinhaTabela(linha));
        });
    }

    function montarLinhasAgrupadas() {
        const linhas = [];

        linhas.push({
            chave: "receita-total",
            descricao: "Receita total",
            competencia: competenciaFormatadaFaixa(),
            tipo: "Receita",
            percentual: percentualSobreReceita(estado.dados.receitas),
            valor: estado.dados.receitas,
            nivel: 0,
            expansivel: false,
            classe: "is-total is-receita",
            visivel: true
        });

        estado.dados.grupos.forEach((grupo) => {
            const chaveGrupo = `grupo:${grupo.nome}`;

            linhas.push({
                chave: chaveGrupo,
                descricao: grupo.nome,
                competencia: competenciaFormatadaFaixa(),
                tipo: grupo.tipo,
                percentual: percentualSobreReceita(grupo.valor),
                valor: grupo.valor,
                nivel: 0,
                expansivel: grupo.filhos.length > 0,
                expandido: estado.expandido.has(chaveGrupo),
                classe: "is-grupo",
                visivel: true
            });

            grupo.filhos.forEach((categoria) => {
                const chaveCategoria = `categoria:${grupo.nome}:${categoria.nome}`;
                const grupoExpandido = estado.expandido.has(chaveGrupo);

                linhas.push({
                    chave: chaveCategoria,
                    descricao: categoria.nome,
                    competencia: competenciaFormatadaFaixa(),
                    tipo: categoria.tipo,
                    percentual: percentualSobreReceita(categoria.valor),
                    valor: categoria.valor,
                    nivel: 1,
                    expansivel: (categoria.filhos || []).length > 0,
                    expandido: estado.expandido.has(chaveCategoria),
                    classe: "is-categoria",
                    visivel: grupoExpandido
                });

                (categoria.filhos || []).forEach((subcategoria) => {
                    linhas.push({
                        chave: `subcategoria:${grupo.nome}:${categoria.nome}:${subcategoria.nome}`,
                        descricao: subcategoria.nome,
                        competencia: competenciaFormatadaFaixa(),
                        tipo: subcategoria.tipo,
                        percentual: percentualSobreReceita(subcategoria.valor),
                        valor: subcategoria.valor,
                        nivel: 2,
                        expansivel: false,
                        classe: "is-subcategoria",
                        visivel: grupoExpandido && estado.expandido.has(chaveCategoria)
                    });
                });
            });

            linhas.push({
                chave: `subtotal:${grupo.nome}`,
                descricao: `Subtotal ${grupo.nome}`,
                competencia: competenciaFormatadaFaixa(),
                tipo: "Subtotal",
                percentual: percentualSobreReceita(grupo.valor),
                valor: grupo.valor,
                nivel: 0,
                expansivel: false,
                classe: "is-subtotal",
                visivel: true
            });
        });

        linhas.push({
            chave: "resultado-final",
            descricao: "Resultado final",
            competencia: competenciaFormatadaFaixa(),
            tipo: "Resultado",
            percentual: percentualSobreReceita(estado.dados.resultado),
            valor: estado.dados.resultado,
            nivel: 0,
            expansivel: false,
            classe: estado.dados.resultado < 0 ? "is-total is-negativo" : "is-total is-positivo",
            visivel: true
        });

        return linhas.filter((linha) => linha.visivel);
    }

    function montarLinhasLista() {
        const linhas = [];

        linhas.push({
            chave: "lista-receita-total",
            descricao: "Receita total",
            competencia: competenciaFormatadaFaixa(),
            tipo: "Receita",
            percentual: percentualSobreReceita(estado.dados.receitas),
            valor: estado.dados.receitas,
            nivel: 0,
            expansivel: false,
            classe: "is-total is-receita",
            visivel: true
        });

        estado.dados.grupos.forEach((grupo) => {
            linhas.push({
                chave: `lista-grupo:${grupo.nome}`,
                descricao: grupo.nome,
                competencia: competenciaFormatadaFaixa(),
                tipo: "Grupo",
                percentual: percentualSobreReceita(grupo.valor),
                valor: grupo.valor,
                nivel: 0,
                expansivel: false,
                classe: "is-grupo",
                visivel: true
            });

            grupo.filhos.forEach((categoria) => {
                linhas.push({
                    chave: `lista-categoria:${grupo.nome}:${categoria.nome}`,
                    descricao: categoria.nome,
                    competencia: competenciaFormatadaFaixa(),
                    tipo: "Categoria",
                    percentual: percentualSobreReceita(categoria.valor),
                    valor: categoria.valor,
                    nivel: 1,
                    expansivel: false,
                    classe: "is-categoria",
                    visivel: true
                });

                (categoria.filhos || []).forEach((subcategoria) => {
                    linhas.push({
                        chave: `lista-subcategoria:${grupo.nome}:${categoria.nome}:${subcategoria.nome}`,
                        descricao: subcategoria.nome,
                        competencia: competenciaFormatadaFaixa(),
                        tipo: "Subcategoria",
                        percentual: percentualSobreReceita(subcategoria.valor),
                        valor: subcategoria.valor,
                        nivel: 2,
                        expansivel: false,
                        classe: "is-subcategoria",
                        visivel: true
                    });
                });
            });

            linhas.push({
                chave: `lista-subtotal:${grupo.nome}`,
                descricao: `Subtotal ${grupo.nome}`,
                competencia: competenciaFormatadaFaixa(),
                tipo: "Subtotal",
                percentual: percentualSobreReceita(grupo.valor),
                valor: grupo.valor,
                nivel: 0,
                expansivel: false,
                classe: "is-subtotal",
                visivel: true
            });
        });

        linhas.push({
            chave: "lista-resultado-final",
            descricao: "Resultado final",
            competencia: competenciaFormatadaFaixa(),
            tipo: "Resultado",
            percentual: percentualSobreReceita(estado.dados.resultado),
            valor: estado.dados.resultado,
            nivel: 0,
            expansivel: false,
            classe: estado.dados.resultado < 0 ? "is-total is-negativo" : "is-total is-positivo",
            visivel: true
        });

        return linhas;
    }

    function criarLinhaTabela(linha) {
        const fragment = linhaTemplate.content.cloneNode(true);
        const tr = fragment.querySelector("tr");
        const descricao = fragment.querySelector(".dre-descricao");
        const toggle = fragment.querySelector(".dre-toggle");
        const toggleIcon = fragment.querySelector(".dre-toggle-icon");
        const competencia = fragment.querySelector(".dre-competencia");
        const tipo = fragment.querySelector(".dre-tipo");
        const percentual = fragment.querySelector(".dre-percentual");
        const valor = fragment.querySelector(".dre-valor");

        tr.dataset.chave = linha.chave;
        tr.classList.add(...linha.classe.split(" ").filter(Boolean));
        tr.style.setProperty("--dre-level", linha.nivel);

        descricao.textContent = linha.descricao;
        competencia.textContent = linha.competencia;
        tipo.textContent = linha.tipo;
        percentual.textContent = linha.percentual;
        valor.textContent = formatarMoeda(linha.valor);

        if (linha.valor < 0) {
            valor.classList.add("text-danger");
        }

        if (!linha.expansivel) {
            toggle.classList.add("is-hidden");
            toggle.setAttribute("tabindex", "-1");
        } else {
            toggleIcon.textContent = linha.expandido ? "−" : "+";
            toggle.setAttribute("aria-expanded", linha.expandido ? "true" : "false");
        }

        return fragment;
    }

    function percentualSobreReceita(valor) {
        const receita = Number(estado.dados?.receitas || 0);
        if (!receita) return "0,00%";
        return `${((Number(valor || 0) / receita) * 100).toFixed(2).replace(".", ",")}%`;
    }

    function competenciaFormatadaFaixa() {
        const inicio = competenciaInicioInput?.value || "";
        const fim = competenciaFimInput?.value || "";

        if (inicio && fim && inicio !== fim) {
            return `${formatarCompetencia(inicio)} a ${formatarCompetencia(fim)}`;
        }

        if (inicio) return formatarCompetencia(inicio);
        if (fim) return formatarCompetencia(fim);
        return "Geral";
    }

    function formatarCompetencia(valor) {
        if (!valor || !valor.includes("-")) return valor || "-";
        const [ano, mes] = valor.split("-");
        return `${mes}/${ano}`;
    }

    function formatarMoeda(valor) {
        return Number(valor || 0).toLocaleString("pt-BR", {
            style: "currency",
            currency: "BRL"
        });
    }

    function normalizarTexto(valor) {
        return String(valor || "").trim() || "Não informado";
    }

    function setLoading() {
        if (!tabelaBody) return;
        tabelaBody.innerHTML = `
            <tr>
                <td colspan="5" class="dre-empty">Carregando DRE...</td>
            </tr>
        `;
    }

    function renderizarErro(mensagem) {
        if (!tabelaBody) return;
        tabelaBody.innerHTML = `
            <tr>
                <td colspan="5" class="dre-empty dre-error">${mensagem}</td>
            </tr>
        `;

        resumoReceita.textContent = "R$ 0,00";
        resumoDespesa.textContent = "R$ 0,00";
        resumoResultado.textContent = "R$ 0,00";
        resumoResultado.classList.remove("text-danger", "text-success");
    }
});