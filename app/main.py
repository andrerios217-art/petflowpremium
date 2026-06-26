from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.core.database import Base, engine
from app.models import *  # noqa
import app.models  # noqa

from app.api import auth, empresas, usuarios, configuracoes
from app.api import agenda_api
from app.api import clientes_api
from app.api import funcionarios_api
from app.api import pets_api
from app.api import servicos_api
from app.api import precificacao_api
from app.api.agenda_veterinaria_api import router as agenda_veterinaria_router
from app.api.assinaturas_api import router as assinaturas_router
from app.api.atendimento_clinico_api import router as atendimento_clinico_router
from app.api.caixa_api import router as caixa_router
from app.api.cashback_api import router as cashback_router
from app.api.comissao import router as comissao_router
from app.api.estoque_api import router as estoque_router
from app.api.financeiro_api import router as financeiro_router
from app.api.financeiro_dashboard import router as financeiro_dashboard_router
from app.api.financeiro_dre_api import router as financeiro_dre_router
from app.api.financeiro_extrato_api import router as financeiro_extrato_router
from app.api.financeiro_pagar_api import router as financeiro_pagar_router
from app.api.fluxo_caixa_api import router as fluxo_caixa_router
from app.api.conciliacao_bancaria_api import router as conciliacao_bancaria_router
from app.api.nota_entrada_api import router as nota_entrada_router
from app.api.pdv_api import router as pdv_router
from app.api.producao_api import router as producao_router
from app.api.relatorios_banho_tosa_api import router as relatorios_banho_tosa_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME, version="1.0.0")


# === PATCH AGENDA VETERINARIA CLINICO RECEITA VECTORPET ===
from datetime import datetime as _VPVetDatetime
from html import escape as _VPVetEscape

from fastapi import Depends as _VPVetDepends
from fastapi import Query as _VPVetQuery
from fastapi.responses import HTMLResponse as _VPVetHTMLResponse
from sqlalchemy.orm import Session as _VPVetSession

try:
    from app.database import get_db as _VPVetGetDb
except Exception:
    from app.core.deps import get_db as _VPVetGetDb

from app.models.agendamento import Agendamento as _VPVetAgendamento
from app.models.atendimento_clinico import AtendimentoClinico as _VPVetAtendimentoClinico
from app.models.cliente import Cliente as _VPVetCliente
from app.models.pet import Pet as _VPVetPet


def _vpvet_colunas(modelo):
    try:
        return {coluna.name for coluna in modelo.__table__.columns}
    except Exception:
        return set()


def _vpvet_set(obj, campo, valor):
    try:
        if campo in _vpvet_colunas(type(obj)):
            setattr(obj, campo, valor)
            return True
    except Exception:
        pass

    return False


def _vpvet_get(obj, *campos, default=None):
    for campo in campos:
        try:
            valor = getattr(obj, campo, None)

            if valor is not None:
                return valor
        except Exception:
            pass

    return default


def _vpvet_data(valor):
    if not valor:
        return ""

    try:
        return valor.strftime("%d/%m/%Y")
    except Exception:
        return str(valor)


def _vpvet_texto(valor):
    return _VPVetEscape(str(valor or ""))


def _vpvet_dict_atendimento(atendimento):
    return {
        "id": getattr(atendimento, "id", None),
        "agendamento_id": getattr(atendimento, "agendamento_id", None),
        "cliente_id": getattr(atendimento, "cliente_id", None),
        "pet_id": getattr(atendimento, "pet_id", None),
        "empresa_id": getattr(atendimento, "empresa_id", None),
        "status": getattr(atendimento, "status", None),
    }


@app.post("/api/clinico/iniciar-por-agendamento/{agendamento_id}")
async def vectorpet_iniciar_clinico_por_agendamento_seguro(
    agendamento_id: int,
    empresa_id: int | None = _VPVetQuery(None),
    db: _VPVetSession = _VPVetDepends(_VPVetGetDb),
):
    agendamento = (
        db.query(_VPVetAgendamento)
        .filter(_VPVetAgendamento.id == agendamento_id)
        .first()
    )

    if agendamento is None:
        return {
            "ok": False,
            "detail": "Agendamento não encontrado.",
        }

    empresa_real = _vpvet_get(agendamento, "empresa_id", default=empresa_id)
    cliente_id = _vpvet_get(agendamento, "cliente_id")
    pet_id = _vpvet_get(agendamento, "pet_id")
    funcionario_id = _vpvet_get(agendamento, "funcionario_id", "veterinario_id")

    atendimento = (
        db.query(_VPVetAtendimentoClinico)
        .filter(_VPVetAtendimentoClinico.agendamento_id == agendamento_id)
        .first()
    )

    if atendimento is None:
        atendimento = _VPVetAtendimentoClinico()

        _vpvet_set(atendimento, "empresa_id", empresa_real)
        _vpvet_set(atendimento, "agendamento_id", agendamento_id)
        _vpvet_set(atendimento, "cliente_id", cliente_id)
        _vpvet_set(atendimento, "pet_id", pet_id)
        _vpvet_set(atendimento, "funcionario_id", funcionario_id)
        _vpvet_set(atendimento, "veterinario_id", funcionario_id)
        _vpvet_set(atendimento, "status", "EM_ATENDIMENTO")
        _vpvet_set(atendimento, "data_atendimento", _VPVetDatetime.utcnow())
        _vpvet_set(atendimento, "created_at", _VPVetDatetime.utcnow())

        db.add(atendimento)
    else:
        _vpvet_set(atendimento, "status", "EM_ATENDIMENTO")
        _vpvet_set(atendimento, "empresa_id", _vpvet_get(atendimento, "empresa_id", default=empresa_real))

    _vpvet_set(agendamento, "status", "EM_ATENDIMENTO")
    _vpvet_set(agendamento, "status_agendamento", "EM_ATENDIMENTO")
    _vpvet_set(agendamento, "em_atendimento", True)

    db.add(agendamento)
    db.add(atendimento)
    db.commit()
    db.refresh(atendimento)

    return {
        "ok": True,
        "mensagem": "Atendimento iniciado com sucesso.",
        "atendimento": _vpvet_dict_atendimento(atendimento),
        "atendimento_id": atendimento.id,
        "id": atendimento.id,
        "receita_url": f"/receita/{atendimento.id}",
        "impressao_receita_url": f"/receita/{atendimento.id}",
    }


@app.get("/receita/{atendimento_id}", response_class=_VPVetHTMLResponse)
@app.get("/atendimento-clinico/receita/{atendimento_id}", response_class=_VPVetHTMLResponse)
@app.get("/imprimir-receita/{atendimento_id}", response_class=_VPVetHTMLResponse)
async def vectorpet_receita_impressao_page(
    atendimento_id: int,
    db: _VPVetSession = _VPVetDepends(_VPVetGetDb),
):
    atendimento = (
        db.query(_VPVetAtendimentoClinico)
        .filter(_VPVetAtendimentoClinico.id == atendimento_id)
        .first()
    )

    if atendimento is None:
        return _VPVetHTMLResponse(
            "<h1>Receita não encontrada</h1><p>Atendimento clínico não localizado.</p>",
            status_code=404,
        )

    cliente = None
    pet = None

    cliente_id = _vpvet_get(atendimento, "cliente_id")
    pet_id = _vpvet_get(atendimento, "pet_id")

    if cliente_id:
        cliente = db.query(_VPVetCliente).filter(_VPVetCliente.id == cliente_id).first()

    if pet_id:
        pet = db.query(_VPVetPet).filter(_VPVetPet.id == pet_id).first()

    tutor_nome = _vpvet_texto(_vpvet_get(cliente, "nome", default="-"))
    pet_nome = _vpvet_texto(_vpvet_get(pet, "nome", default="-"))

    data = _vpvet_data(
        _vpvet_get(
            atendimento,
            "data_atendimento",
            "created_at",
            default=_VPVetDatetime.utcnow(),
        )
    )

    queixa = _vpvet_texto(_vpvet_get(atendimento, "queixa_principal", "queixa", default=""))
    historico = _vpvet_texto(_vpvet_get(atendimento, "historico_atual", "historico", default=""))
    conduta = _vpvet_texto(_vpvet_get(atendimento, "conduta", "conduta_servicos_executados", default=""))
    medicacoes = _vpvet_texto(_vpvet_get(atendimento, "medicacoes", "medicamentos", default=""))
    exames = _vpvet_texto(_vpvet_get(atendimento, "exames_diagnostico", "exames", "diagnostico", default=""))
    receita = _vpvet_texto(_vpvet_get(atendimento, "receita_orientacoes", "receita", "orientacoes", default=""))
    observacoes = _vpvet_texto(_vpvet_get(atendimento, "observacoes_gerais", "observacoes", default=""))

    html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>Receita / Atendimento #{atendimento_id}</title>
  <style>
    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      padding: 32px;
      font-family: Arial, sans-serif;
      color: #111827;
      background: #f8fafc;
    }}

    .pagina {{
      max-width: 860px;
      margin: 0 auto;
      background: #fff;
      border: 1px solid #e5e7eb;
      border-radius: 18px;
      padding: 30px;
    }}

    .topo {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      border-bottom: 2px solid #e5e7eb;
      padding-bottom: 18px;
      margin-bottom: 24px;
    }}

    h1 {{
      margin: 0;
      color: #172554;
      font-size: 26px;
    }}

    .sub {{
      margin-top: 6px;
      color: #64748b;
    }}

    .dados {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
      margin-bottom: 24px;
    }}

    .box {{
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      padding: 12px;
      background: #f8fafc;
    }}

    .box span {{
      display: block;
      color: #64748b;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      margin-bottom: 5px;
    }}

    .box strong {{
      font-size: 16px;
    }}

    .secao {{
      margin-top: 18px;
    }}

    .secao h2 {{
      margin: 0 0 8px;
      color: #172554;
      font-size: 17px;
    }}

    .campo {{
      min-height: 48px;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      padding: 12px;
      white-space: pre-wrap;
      background: #fff;
    }}

    .assinatura {{
      margin-top: 44px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
    }}

    .linha {{
      border-top: 1px solid #111827;
      padding-top: 8px;
      text-align: center;
      color: #374151;
      font-size: 13px;
    }}

    .acoes {{
      margin-top: 24px;
      display: flex;
      justify-content: flex-end;
      gap: 10px;
    }}

    button {{
      border: 0;
      border-radius: 10px;
      padding: 11px 16px;
      font-weight: 700;
      cursor: pointer;
    }}

    .primario {{
      background: #172554;
      color: #fff;
    }}

    .secundario {{
      background: #e5e7eb;
      color: #111827;
    }}

    @media print {{
      body {{
        background: #fff;
        padding: 0;
      }}

      .pagina {{
        border: 0;
        border-radius: 0;
        max-width: none;
      }}

      .acoes {{
        display: none;
      }}
    }}
  </style>
</head>
<body>
  <main class="pagina">
    <div class="topo">
      <div>
        <h1>Receita / Atendimento clínico</h1>
        <div class="sub">VectorPet • Atendimento #{atendimento_id}</div>
      </div>
      <div class="sub">Data: {data}</div>
    </div>

    <section class="dados">
      <div class="box">
        <span>Tutor</span>
        <strong>{tutor_nome}</strong>
      </div>
      <div class="box">
        <span>Pet</span>
        <strong>{pet_nome}</strong>
      </div>
    </section>

    <section class="secao">
      <h2>Queixa principal</h2>
      <div class="campo">{queixa}</div>
    </section>

    <section class="secao">
      <h2>Histórico atual</h2>
      <div class="campo">{historico}</div>
    </section>

    <section class="secao">
      <h2>Conduta / serviços executados</h2>
      <div class="campo">{conduta}</div>
    </section>

    <section class="secao">
      <h2>Medicações</h2>
      <div class="campo">{medicacoes}</div>
    </section>

    <section class="secao">
      <h2>Exames / diagnóstico</h2>
      <div class="campo">{exames}</div>
    </section>

    <section class="secao">
      <h2>Receita / orientações</h2>
      <div class="campo">{receita}</div>
    </section>

    <section class="secao">
      <h2>Observações gerais</h2>
      <div class="campo">{observacoes}</div>
    </section>

    <section class="assinatura">
      <div class="linha">Assinatura do responsável</div>
      <div class="linha">Assinatura do veterinário</div>
    </section>

    <div class="acoes">
      <button class="secundario" onclick="window.close()">Fechar</button>
      <button class="primario" onclick="window.print()">Imprimir</button>
    </div>
  </main>

  <script>
    setTimeout(function () {{
      window.print();
    }}, 500);
  </script>
</body>
</html>
    """

    return _VPVetHTMLResponse(html)
# === FIM PATCH AGENDA VETERINARIA CLINICO RECEITA VECTORPET ===


# === ROTAS VISUAIS ASSINATURAS VECTORPET ===
from datetime import date as _VPAssDate
from decimal import Decimal as _VPAssDecimal

from fastapi import Depends as _VPAssDepends
from fastapi import Query as _VPAssQuery
from fastapi import Request as _VPAssRequest
from fastapi.responses import HTMLResponse as _VPAssHTMLResponse
from fastapi.responses import RedirectResponse as _VPAssRedirectResponse
from fastapi.templating import Jinja2Templates as _VPAssTemplates
from sqlalchemy.orm import Session as _VPAssSession

try:
    from app.core.deps import get_db as _VPAssGetDb
except Exception:
    from app.database import get_db as _VPAssGetDb

from app.models.assinatura_pet import AssinaturaPet as _VPAssinaturaPet
from app.models.cliente import Cliente as _VPAssCliente
from app.models.pet import Pet as _VPAssPet

_vp_ass_templates = _VPAssTemplates(directory="app/templates")


def _vp_ass_moeda(valor):
    if valor is None:
        valor = 0

    if isinstance(valor, _VPAssDecimal):
        valor = float(valor)

    try:
        valor = float(valor)
    except Exception:
        valor = 0

    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return "R$ " + texto


def _vp_ass_data(valor):
    if not valor:
        return "-"

    try:
        return valor.strftime("%d/%m/%Y")
    except Exception:
        return str(valor)


def _vp_ass_item(db: _VPAssSession, assinatura: _VPAssinaturaPet):
    cliente = (
        db.query(_VPAssCliente)
        .filter(_VPAssCliente.id == assinatura.cliente_id)
        .first()
    )

    pet = (
        db.query(_VPAssPet)
        .filter(_VPAssPet.id == assinatura.pet_id)
        .first()
    )

    valor_final = getattr(assinatura, "valor_final", 0)

    try:
        from app.models.assinatura_pet_item import AssinaturaPetItem as _VPAssItemCalc

        itens_calc = (
            db.query(_VPAssItemCalc)
            .filter(_VPAssItemCalc.assinatura_id == assinatura.id)
            .all()
        )

        if itens_calc:
            total_calc = _VPAssDecimal("0.00")

            for item_calc in itens_calc:
                if hasattr(item_calc, "ativo") and getattr(item_calc, "ativo") is False:
                    continue

                quantidade = _VPAssDecimal(str(getattr(item_calc, "quantidade_contratada", 1) or 1))
                preco = _VPAssDecimal(str(getattr(item_calc, "preco_unitario_base", 0) or 0))
                desconto = _VPAssDecimal(str(getattr(item_calc, "percentual_desconto", 0) or 0))

                subtotal = quantidade * preco
                total_calc += subtotal - (subtotal * desconto / _VPAssDecimal("100"))

            valor_final = total_calc
    except Exception:
        pass

    return {
        "id": assinatura.id,
        "cliente_id": getattr(assinatura, "cliente_id", None),
        "cliente_nome": getattr(cliente, "nome", "") if cliente else "-",
        "pet_id": getattr(assinatura, "pet_id", None),
        "pet_nome": getattr(pet, "nome", "") if pet else "-",
        "status": getattr(assinatura, "status", "") or "-",
        "data_inicio_formatada": _vp_ass_data(getattr(assinatura, "data_inicio", None)),
        "data_fim_formatada": _vp_ass_data(getattr(assinatura, "data_fim", None)),
        "valor_final": float(valor_final or 0),
        "valor_final_formatado": _vp_ass_moeda(valor_final),
    }


@app.get("/assinaturas", response_class=_VPAssHTMLResponse)
async def vectorpet_assinaturas_lista_page(
    request: _VPAssRequest,
    busca: str | None = _VPAssQuery(None),
    status: str | None = _VPAssQuery(None),
    db: _VPAssSession = _VPAssDepends(_VPAssGetDb),
):
    query = db.query(_VPAssinaturaPet)

    if status:
        query = query.filter(_VPAssinaturaPet.status == status)

    registros = query.order_by(_VPAssinaturaPet.id.desc()).limit(300).all()
    assinaturas = [_vp_ass_item(db, assinatura) for assinatura in registros]

    if busca:
        termo = busca.strip().lower()

        assinaturas = [
            item for item in assinaturas
            if termo in str(item["id"]).lower()
            or termo in str(item["cliente_nome"]).lower()
            or termo in str(item["pet_nome"]).lower()
        ]

    total_ativas = len([item for item in assinaturas if item["status"] == "ATIVA"])
    total_canceladas = len([item for item in assinaturas if item["status"] == "CANCELADA"])
    valor_ativo = sum(
        item["valor_final"]
        for item in assinaturas
        if item["status"] == "ATIVA"
    )

    return _vp_ass_templates.TemplateResponse(
        request,
        "assinaturas_lista.html",
        {
            "request": request,
            "system_name": "VectorPet",
            "assinaturas": assinaturas,
            "busca": busca or "",
            "status": status or "",
            "total": len(assinaturas),
            "total_ativas": total_ativas,
            "total_canceladas": total_canceladas,
            "valor_ativo_formatado": _vp_ass_moeda(valor_ativo),
        },
    )


@app.get("/assinaturas/novo", response_class=_VPAssHTMLResponse)
async def vectorpet_assinaturas_novo_page(request: _VPAssRequest):
    return _vp_ass_templates.TemplateResponse(
        request,
        "assinaturas.html",
        {
            "request": request,
            "system_name": "VectorPet",
            "assinatura_id": "",
        },
    )


@app.get("/assinaturas/editar/{assinatura_id}", response_class=_VPAssHTMLResponse)
async def vectorpet_assinaturas_editar_page(request: _VPAssRequest, assinatura_id: int):
    return _vp_ass_templates.TemplateResponse(
        request,
        "assinaturas.html",
        {
            "request": request,
            "system_name": "VectorPet",
            "assinatura_id": assinatura_id,
        },
    )


@app.post("/assinaturas/cancelar-visual/{assinatura_id}")
async def vectorpet_assinaturas_cancelar_visual(
    assinatura_id: int,
    db: _VPAssSession = _VPAssDepends(_VPAssGetDb),
):
    assinatura = (
        db.query(_VPAssinaturaPet)
        .filter(_VPAssinaturaPet.id == assinatura_id)
        .first()
    )

    if assinatura is not None:
        assinatura.status = "CANCELADA"

        if hasattr(assinatura, "data_cancelamento"):
            assinatura.data_cancelamento = _VPAssDate.today()

        db.add(assinatura)
        db.commit()

    return _VPAssRedirectResponse("/assinaturas", status_code=303)
# === FIM ROTAS VISUAIS ASSINATURAS VECTORPET ===

# === PATCH VECTORPET UPDATE ASSINATURA ITENS ===
from datetime import date as _VPUpdateDate
from decimal import Decimal as _VPUpdateDecimal
from fastapi import Body as _VPUpdateBody
from fastapi import HTTPException as _VPUpdateHTTPException

from app.models.assinatura_pet_item import AssinaturaPetItem as _VPUpdateAssinaturaPetItem


def _vp_update_decimal(valor):
    texto = str(valor or "0").strip().replace("R$", "").replace(" ", "")

    if "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")
    else:
        texto = texto.replace(",", ".")

    try:
        return _VPUpdateDecimal(texto).quantize(_VPUpdateDecimal("0.01"))
    except Exception:
        return _VPUpdateDecimal("0.00")


def _vp_update_int(valor, padrao=0):
    try:
        return int(valor)
    except Exception:
        return padrao


def _vp_update_date(valor):
    if not valor:
        return None

    if isinstance(valor, _VPUpdateDate):
        return valor

    try:
        return _VPUpdateDate.fromisoformat(str(valor))
    except Exception:
        return None


def _vp_update_item_dict(item):
    if hasattr(item, "model_dump"):
        return item.model_dump()

    if isinstance(item, dict):
        return item

    return {}


def _vp_update_set_seguro(obj, campo, valor):
    """
    Evita erro em propriedades calculadas do model, como quantidade_disponivel,
    que existem no objeto mas não têm setter.
    """
    try:
        setattr(obj, campo, valor)
        return True
    except AttributeError:
        return False
    except Exception:
        return False


@app.put("/assinaturas/{assinatura_id}")
async def vectorpet_update_assinatura_com_itens(
    assinatura_id: int,
    payload: dict = _VPUpdateBody(...),
    db: _VPAssSession = _VPAssDepends(_VPAssGetDb),
):
    assinatura = (
        db.query(_VPAssinaturaPet)
        .filter(_VPAssinaturaPet.id == assinatura_id)
        .first()
    )

    if assinatura is None:
        raise _VPUpdateHTTPException(status_code=404, detail="Assinatura não encontrada.")

    try:
        campos_simples = [
            "cliente_id",
            "pet_id",
            "status",
            "dia_fechamento_ciclo",
            "usar_limite_ate_dia_28",
            "nao_cumulativa",
            "ativa_renovacao",
            "origem",
            "observacoes",
            "contrato_externo_id",
        ]

        for campo in campos_simples:
            if campo in payload:
                _vp_update_set_seguro(assinatura, campo, payload.get(campo))

        if "data_inicio" in payload:
            _vp_update_set_seguro(assinatura, "data_inicio", _vp_update_date(payload.get("data_inicio")))

        if "data_fim" in payload:
            _vp_update_set_seguro(assinatura, "data_fim", _vp_update_date(payload.get("data_fim")))

        empresa_id = getattr(assinatura, "empresa_id", None)

        itens_payload = payload.get("itens") or []

        if not itens_payload:
            raise _VPUpdateHTTPException(
                status_code=400,
                detail="A assinatura deve ter ao menos um serviço.",
            )

        itens_antigos = (
            db.query(_VPUpdateAssinaturaPetItem)
            .filter(_VPUpdateAssinaturaPetItem.assinatura_id == assinatura.id)
            .order_by(_VPUpdateAssinaturaPetItem.id.asc())
            .all()
        )

        total_bruto = _VPUpdateDecimal("0.00")
        total_desconto = _VPUpdateDecimal("0.00")
        total_final = _VPUpdateDecimal("0.00")

        for index, item_payload in enumerate(itens_payload):
            item_dados = _vp_update_item_dict(item_payload)

            servico_id = _vp_update_int(item_dados.get("servico_id"), 0)
            nome_servico = str(item_dados.get("nome_servico") or "").strip()
            quantidade = max(1, _vp_update_int(item_dados.get("quantidade_contratada"), 1))
            preco_base = _vp_update_decimal(item_dados.get("preco_unitario_base"))
            percentual = _vp_update_decimal(item_dados.get("percentual_desconto"))

            if servico_id <= 0:
                raise _VPUpdateHTTPException(status_code=400, detail="Serviço inválido na assinatura.")

            if not nome_servico:
                raise _VPUpdateHTTPException(status_code=400, detail="Nome do serviço obrigatório na assinatura.")

            if percentual < 0 or percentual > 100:
                raise _VPUpdateHTTPException(status_code=400, detail="O desconto deve estar entre 0 e 100.")

            if index < len(itens_antigos):
                item = itens_antigos[index]
            else:
                item = _VPUpdateAssinaturaPetItem(
                    assinatura_id=assinatura.id,
                    empresa_id=empresa_id,
                    servico_id=servico_id,
                    nome_servico=nome_servico,
                    quantidade_contratada=quantidade,
                    preco_unitario_base=preco_base,
                    percentual_desconto=percentual,
                )
                db.add(item)

            _vp_update_set_seguro(item, "empresa_id", empresa_id)
            _vp_update_set_seguro(item, "servico_id", servico_id)
            _vp_update_set_seguro(item, "nome_servico", nome_servico)
            _vp_update_set_seguro(item, "quantidade_contratada", quantidade)
            _vp_update_set_seguro(item, "preco_unitario_base", preco_base)
            _vp_update_set_seguro(item, "percentual_desconto", percentual)

            subtotal_bruto = (preco_base * quantidade).quantize(_VPUpdateDecimal("0.01"))
            subtotal_desconto = (subtotal_bruto * percentual / _VPUpdateDecimal("100")).quantize(_VPUpdateDecimal("0.01"))
            subtotal_final = (subtotal_bruto - subtotal_desconto).quantize(_VPUpdateDecimal("0.01"))

            # Campos calculados: grava só se forem colunas graváveis.
            _vp_update_set_seguro(item, "valor_desconto_unitario", (preco_base * percentual / _VPUpdateDecimal("100")).quantize(_VPUpdateDecimal("0.01")))
            _vp_update_set_seguro(item, "preco_unitario_final", (preco_base - (preco_base * percentual / _VPUpdateDecimal("100"))).quantize(_VPUpdateDecimal("0.01")))
            _vp_update_set_seguro(item, "subtotal_bruto", subtotal_bruto)
            _vp_update_set_seguro(item, "subtotal_desconto", subtotal_desconto)
            _vp_update_set_seguro(item, "subtotal_final", subtotal_final)
            _vp_update_set_seguro(item, "ativo", True)

            db.add(item)

            total_bruto += subtotal_bruto
            total_desconto += subtotal_desconto
            total_final += subtotal_final

        # Remove itens excedentes para evitar duplicidade de valor na lista.
        for item_extra in itens_antigos[len(itens_payload):]:
            marcado = _vp_update_set_seguro(item_extra, "ativo", False)

            if marcado:
                db.add(item_extra)
            else:
                db.delete(item_extra)

        _vp_update_set_seguro(assinatura, "valor_bruto", total_bruto.quantize(_VPUpdateDecimal("0.01")))
        _vp_update_set_seguro(assinatura, "valor_desconto", total_desconto.quantize(_VPUpdateDecimal("0.01")))
        _vp_update_set_seguro(assinatura, "valor_final", total_final.quantize(_VPUpdateDecimal("0.01")))

        db.add(assinatura)
        db.commit()
        db.refresh(assinatura)

        return {
            "ok": True,
            "mensagem": "Assinatura atualizada com sucesso.",
            "assinatura": {
                "id": assinatura.id,
                "cliente_id": assinatura.cliente_id,
                "pet_id": assinatura.pet_id,
                "status": assinatura.status,
                "valor_bruto": str(getattr(assinatura, "valor_bruto", total_bruto)),
                "valor_desconto": str(getattr(assinatura, "valor_desconto", total_desconto)),
                "valor_final": str(getattr(assinatura, "valor_final", total_final)),
            },
        }

    except _VPUpdateHTTPException:
        raise
    except Exception as erro:
        db.rollback()
        raise _VPUpdateHTTPException(
            status_code=500,
            detail=f"Erro ao atualizar assinatura: {erro}",
        ) from erro
# === FIM PATCH VECTORPET UPDATE ASSINATURA ITENS ===


app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

templates.env.globals["system_name"] = settings.APP_NAME
templates.env.globals["system_tagline"] = settings.APP_TAGLINE

app.include_router(auth.router)
app.include_router(empresas.router)
app.include_router(usuarios.router)
app.include_router(configuracoes.router)
app.include_router(clientes_api.router)
app.include_router(pets_api.router)
app.include_router(servicos_api.router)
app.include_router(funcionarios_api.router)
app.include_router(agenda_api.router)
app.include_router(agenda_veterinaria_router)
app.include_router(atendimento_clinico_router)
app.include_router(producao_router)
app.include_router(comissao_router)
app.include_router(estoque_router)
app.include_router(nota_entrada_router)
app.include_router(financeiro_router)
app.include_router(financeiro_dashboard_router)
app.include_router(financeiro_dre_router)
app.include_router(financeiro_extrato_router)
app.include_router(financeiro_pagar_router)
app.include_router(fluxo_caixa_router)
app.include_router(conciliacao_bancaria_router)
app.include_router(pdv_router)
app.include_router(caixa_router)
app.include_router(cashback_router)
app.include_router(precificacao_api.router)
app.include_router(relatorios_banho_tosa_router)

app.include_router(assinaturas_router)


@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse(request, "dashboard.html", {"request": request})


@app.get("/clientes", response_class=HTMLResponse)
def clientes_page(request: Request):
    return templates.TemplateResponse(request, "clientes.html", {"request": request})


@app.get("/clientes/novo", response_class=HTMLResponse)
def clientes_form_page(request: Request):
    return templates.TemplateResponse(request, "clientes_form.html", {"request": request})


@app.get("/clientes/editar/{cliente_id}", response_class=HTMLResponse)
def clientes_edit_page(request: Request, cliente_id: int):
    return templates.TemplateResponse(
        request, "clientes_form.html", {"request": request, "cliente_id": cliente_id}
    )


@app.get("/pets", response_class=HTMLResponse)
def pets_page(request: Request):
    return templates.TemplateResponse(request, "pets.html", {"request": request})


@app.get("/pets/novo", response_class=HTMLResponse)
def pets_form_page(request: Request):
    return templates.TemplateResponse(request, "pets_form.html", {"request": request})


@app.get("/servicos", response_class=HTMLResponse)
def servicos_page(request: Request):
    return templates.TemplateResponse(request, "servicos.html", {"request": request})


@app.get("/servicos/novo", response_class=HTMLResponse)
def servicos_form_page(request: Request):
    return templates.TemplateResponse(request, "servicos_form.html", {"request": request})


@app.get("/servicos/editar/{servico_id}", response_class=HTMLResponse)
def servicos_edit_page(request: Request, servico_id: int):
    return templates.TemplateResponse(
        request, "servicos_form.html", {"request": request, "servico_id": servico_id}
    )


@app.get("/funcionarios", response_class=HTMLResponse)
def funcionarios_page(request: Request):
    return templates.TemplateResponse(request, "funcionarios.html", {"request": request})


@app.get("/funcionarios/novo", response_class=HTMLResponse)
def funcionarios_form_page(request: Request):
    return templates.TemplateResponse(request, "funcionarios_form.html", {"request": request})


@app.get("/funcionarios/editar/{funcionario_id}", response_class=HTMLResponse)
def funcionarios_edit_page(request: Request, funcionario_id: int):
    return templates.TemplateResponse(
        request, "funcionarios_form.html", {"request": request, "funcionario_id": funcionario_id}
    )


@app.get("/agenda", response_class=HTMLResponse)
def agenda_page(request: Request):
    return templates.TemplateResponse(request, "agenda.html", {"request": request})


@app.get("/agenda-veterinaria", response_class=HTMLResponse)
def agenda_veterinaria_page(request: Request):
    return templates.TemplateResponse(request, "agenda_veterinaria.html", {"request": request})


@app.get("/atendimento-clinico/{agendamento_id}", response_class=HTMLResponse)
def atendimento_clinico_page(request: Request, agendamento_id: int):
    return templates.TemplateResponse(
        request,
        "atendimento_clinico.html",
        {"request": request, "agendamento_id": agendamento_id},
    )


@app.get("/producao", response_class=HTMLResponse)
def producao_page(request: Request):
    return templates.TemplateResponse(request, "producao.html", {"request": request})


@app.get("/estoque", response_class=HTMLResponse)
def estoque_page(request: Request):
    return templates.TemplateResponse(request, "estoque.html", {"request": request})


@app.get("/notas-entrada", response_class=HTMLResponse)
def notas_entrada_page(request: Request):
    return templates.TemplateResponse(request, "notas_entrada.html", {"request": request})


@app.get("/precificacao", response_class=HTMLResponse)
def precificacao_page(request: Request):
    return templates.TemplateResponse(request, "precificacao.html", {"request": request})


@app.get("/financeiro", response_class=HTMLResponse)
def financeiro_page(request: Request):
    return templates.TemplateResponse(request, "financeiro.html", {"request": request})


@app.get("/fluxo-caixa", response_class=HTMLResponse)
def fluxo_caixa_page(request: Request):
    return templates.TemplateResponse(request, "fluxo_caixa.html", {"request": request})


@app.get("/dre", response_class=HTMLResponse)
def dre_page(request: Request):
    return templates.TemplateResponse(request, "dre.html", {"request": request})


@app.get("/pdv", response_class=HTMLResponse)
def pdv_page(request: Request):
    return templates.TemplateResponse(request, "pdv.html", {"request": request})


@app.get("/relatorio-vendas", response_class=HTMLResponse)
def relatorio_vendas_page(request: Request):
    return templates.TemplateResponse(request, "relatorio_vendas.html", {"request": request})


@app.get("/ia-compras", response_class=HTMLResponse)
def ia_compras_page(request: Request):
    return templates.TemplateResponse(request, "ia_compras.html", {"request": request})


@app.get("/crm", response_class=HTMLResponse)
def crm_page(request: Request):
    return templates.TemplateResponse(request, "crm.html", {"request": request})


@app.get("/relatorios", response_class=HTMLResponse)
def relatorios_page(request: Request):
    return templates.TemplateResponse(request, "relatorios.html", {"request": request})


@app.get("/relatorios/comissao", response_class=HTMLResponse)
def relatorios_comissao_page(request: Request):
    return templates.TemplateResponse(request, "relatorios_comissao.html", {"request": request})


@app.get("/relatorios/comissao/demonstrativo/{fechamento_id}", response_class=HTMLResponse)
def demonstrativo_comissao_page(request: Request, fechamento_id: int):
    return templates.TemplateResponse(
        request,
        "comissao_demonstrativo.html",
        {
            "request": request,
            "fechamento_id": fechamento_id,
        },
    )


@app.get("/configuracoes", response_class=HTMLResponse)
def configuracoes_page(request: Request):
    return templates.TemplateResponse(request, "configuracoes.html", {"request": request})


@app.get("/assinaturas", response_class=HTMLResponse)
def assinaturas_page(request: Request):
    return templates.TemplateResponse(request, "assinaturas.html", {"request": request})


@app.get("/assinaturas/nova", response_class=HTMLResponse)
def assinaturas_form_page(request: Request):
    return templates.TemplateResponse(request, "assinaturas_form.html", {"request": request})


@app.get("/assinaturas/editar/{assinatura_id}", response_class=HTMLResponse)
def assinaturas_edit_page(request: Request, assinatura_id: int):
    return templates.TemplateResponse(
        request,
        "assinaturas_form.html",
        {"request": request, "assinatura_id": assinatura_id},
    )

@app.get("/conciliacao-bancaria", response_class=HTMLResponse)
def conciliacao_bancaria_page(request: Request):
    return templates.TemplateResponse(
        request,
        "conciliacao_bancaria.html",
        {"request": request},
    )


@app.get("/auditoria-visual", response_class=HTMLResponse)
def auditoria_visual_page(request: Request):
    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Auditoria Visual | PetFlow Premium</title>
      <style>
        body {
          margin: 0;
          padding: 32px;
          font-family: Arial, sans-serif;
          background: #f4f7fb;
          color: #172033;
        }

        .wrap {
          max-width: 1180px;
          margin: 0 auto;
        }

        .header {
          background: #ffffff;
          border: 1px solid #dbe3ef;
          border-radius: 18px;
          padding: 24px;
          box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
          margin-bottom: 22px;
        }

        .header h1 {
          margin: 0 0 8px;
          font-size: 28px;
        }

        .header p {
          margin: 0;
          color: #64748b;
          font-size: 15px;
          line-height: 1.5;
        }

        .alert {
          margin-top: 14px;
          padding: 12px 14px;
          border-radius: 12px;
          background: #fff7ed;
          border: 1px solid #fed7aa;
          color: #9a3412;
          font-weight: 700;
          font-size: 14px;
        }

        .grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 16px;
        }

        .card {
          background: #ffffff;
          border: 1px solid #dbe3ef;
          border-radius: 18px;
          padding: 18px;
          box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
        }

        .card h2 {
          margin: 0 0 12px;
          font-size: 18px;
          color: #0f172a;
        }

        .link-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        a {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 10px;
          padding: 10px 12px;
          border-radius: 12px;
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          color: #1d4ed8;
          text-decoration: none;
          font-weight: 800;
          font-size: 14px;
        }

        a:hover {
          background: #eff6ff;
          border-color: #93c5fd;
        }

        .path {
          color: #64748b;
          font-size: 12px;
          font-weight: 700;
        }

        .checklist {
          margin-top: 22px;
          background: #ffffff;
          border: 1px solid #dbe3ef;
          border-radius: 18px;
          padding: 20px;
          box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
        }

        .checklist h2 {
          margin: 0 0 12px;
        }

        .checklist ul {
          margin: 0;
          padding-left: 20px;
          color: #475569;
          line-height: 1.75;
        }

        @media (max-width: 980px) {
          .grid {
            grid-template-columns: 1fr;
          }

          body {
            padding: 16px;
          }
        }
      </style>
    </head>
    <body>
      <main class="wrap">
        <section class="header">
          <h1>Auditoria Visual do Sistema</h1>
          <p>
            Página temporária para revisar telas, nomes, botões, ortografia, duplicidades,
            menus e problemas visuais. Não execute operações reais com dados sensíveis.
          </p>
          <div class="alert">
            Após a revisão, remova esta rota ou deixe o túnel Cloudflare desligado.
          </div>
        </section>

        <section class="grid">
          <article class="card">
            <h2>Principal</h2>
            <div class="link-list">
              <a href="/" target="_blank">Login <span class="path">/</span></a>
              <a href="/dashboard" target="_blank">Dashboard <span class="path">/dashboard</span></a>
              <a href="/configuracoes" target="_blank">Configurações <span class="path">/configuracoes</span></a>
              <a href="/empresas" target="_blank">Empresas <span class="path">/empresas</span></a>
              <a href="/usuarios" target="_blank">Usuários <span class="path">/usuarios</span></a>
            </div>
          </article>

          <article class="card">
            <h2>Cadastros</h2>
            <div class="link-list">
              <a href="/clientes" target="_blank">Clientes <span class="path">/clientes</span></a>
              <a href="/pets" target="_blank">Pets <span class="path">/pets</span></a>
              <a href="/servicos" target="_blank">Serviços <span class="path">/servicos</span></a>
              <a href="/funcionarios" target="_blank">Funcionários <span class="path">/funcionarios</span></a>
            </div>
          </article>

          <article class="card">
            <h2>Operação</h2>
            <div class="link-list">
              <a href="/agenda" target="_blank">Agenda Banho e Tosa <span class="path">/agenda</span></a>
              <a href="/agenda-veterinaria" target="_blank">Agenda Veterinária <span class="path">/agenda-veterinaria</span></a>
              <a href="/producao" target="_blank">Produção <span class="path">/producao</span></a>
              <a href="/pdv" target="_blank">PDV <span class="path">/pdv</span></a>
              <a href="/caixa" target="_blank">Caixa <span class="path">/caixa</span></a>
            </div>
          </article>

          <article class="card">
            <h2>Financeiro</h2>
            <div class="link-list">
              <a href="/financeiro" target="_blank">Financeiro <span class="path">/financeiro</span></a>
              <a href="/fluxo-caixa" target="_blank">Fluxo de Caixa <span class="path">/fluxo-caixa</span></a>
              <a href="/dre" target="_blank">DRE <span class="path">/dre</span></a>
              <a href="/conciliacao-bancaria" target="_blank">Conciliação Bancária <span class="path">/conciliacao-bancaria</span></a>
            </div>
          </article>

          <article class="card">
            <h2>Estoque</h2>
            <div class="link-list">
              <a href="/estoque" target="_blank">Estoque <span class="path">/estoque</span></a>
              <a href="/notas-entrada" target="_blank">Notas de Entrada <span class="path">/notas-entrada</span></a>
              <a href="/produtos-parados" target="_blank">Produtos Parados <span class="path">/produtos-parados</span></a>
              <a href="/ia-compras" target="_blank">IA de Compras <span class="path">/ia-compras</span></a>
            </div>
          </article>

          <article class="card">
            <h2>Relatórios e Regras</h2>
            <div class="link-list">
              <a href="/relatorios-comissao" target="_blank">Relatório de Comissão <span class="path">/relatorios-comissao</span></a>
              <a href="/relatorio-banho-tosa" target="_blank">Relatório Banho e Tosa <span class="path">/relatorio-banho-tosa</span></a>
              <a href="/assinaturas" target="_blank">Assinaturas <span class="path">/assinaturas</span></a>
              <a href="/configuracoes-comissao" target="_blank">Configuração de Comissão <span class="path">/configuracoes-comissao</span></a>
              <a href="/configuracoes-precificacao" target="_blank">Precificação <span class="path">/configuracoes-precificacao</span></a>
            </div>
          </article>
        </section>

        <section class="checklist">
          <h2>Checklist de revisão</h2>
          <ul>
            <li>Verificar se a tela carrega sem erro visual.</li>
            <li>Verificar se nomes dos menus estão duplicados ou antigos.</li>
            <li>Procurar textos com grafia incorreta ou sem acento.</li>
            <li>Conferir botões sem ação aparente.</li>
            <li>Conferir se o nome do sistema está padronizado.</li>
            <li>Verificar se tabelas, cards e filtros seguem o mesmo padrão visual.</li>
            <li>Verificar se há tela antiga ou módulo que deveria ter sido removido.</li>
          </ul>
        </section>
      </main>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


# === ROTAS RELATORIO COMISSAO (VectorPet) ===
from fastapi import Request as _VectorPetRequest
from fastapi.responses import HTMLResponse as _VectorPetHTMLResponse
from fastapi.templating import Jinja2Templates as _VectorPetJinja2Templates

_vectorpet_templates = globals().get("templates")

if _vectorpet_templates is None:
    _vectorpet_templates = _VectorPetJinja2Templates(directory="app/templates")


@app.get("/relatorios-comissao", response_class=_VectorPetHTMLResponse)
@app.get("/relatorio-comissao", response_class=_VectorPetHTMLResponse)
async def vectorpet_relatorios_comissao_page(request: _VectorPetRequest):
    return _vectorpet_templates.TemplateResponse(
        request,
        "relatorios_comissao.html",
        {
            "request": request,
            "system_name": "VectorPet",
        },
    )
# === FIM ROTAS RELATORIO COMISSAO (VectorPet) ===


# === ROTAS RELATORIO BANHO TOSA (VectorPet) ===
from fastapi import Request as _VectorPetBanhoTosaRequest
from fastapi.responses import HTMLResponse as _VectorPetBanhoTosaHTMLResponse
from fastapi.templating import Jinja2Templates as _VectorPetBanhoTosaJinja2Templates

_vectorpet_banho_tosa_templates = globals().get("templates")

if _vectorpet_banho_tosa_templates is None:
    _vectorpet_banho_tosa_templates = _VectorPetBanhoTosaJinja2Templates(directory="app/templates")


@app.get("/relatorio-banho-tosa", response_class=_VectorPetBanhoTosaHTMLResponse)
@app.get("/relatorios-banho-tosa", response_class=_VectorPetBanhoTosaHTMLResponse)
async def vectorpet_relatorio_banho_tosa_page(request: _VectorPetBanhoTosaRequest):
    return _vectorpet_banho_tosa_templates.TemplateResponse(
        request,
        "relatorios.html",
        {
            "request": request,
            "system_name": "VectorPet",
        },
    )
# === FIM ROTAS RELATORIO BANHO TOSA (VectorPet) ===


