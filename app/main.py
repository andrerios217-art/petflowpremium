from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.database import Base, engine
from app.models import *  # noqa
import app.models  # noqa
from app.api import auth, empresas, usuarios, configuracoes
from app.api import agenda_api
from app.api import clientes_api
from app.api import funcionarios_api
from app.api import pets_api
from app.api import servicos_api
from app.api.agenda_veterinaria_api import router as agenda_veterinaria_router
from app.api.atendimento_clinico_api import router as atendimento_clinico_router
from app.api.caixa_api import router as caixa_router
from app.api.comissao import router as comissao_router
from app.api.estoque_api import router as estoque_router
from app.api.financeiro_api import router as financeiro_router
from app.api.financeiro_dashboard import router as financeiro_dashboard_router
from app.api.financeiro_pagar_api import router as financeiro_pagar_router
from app.api.pdv_api import router as pdv_router
from app.api.producao_api import router as producao_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Pet Flow Premium", version="1.0.0")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

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
app.include_router(financeiro_router)
app.include_router(financeiro_dashboard_router)
app.include_router(financeiro_pagar_router)
app.include_router(pdv_router)
app.include_router(caixa_router)


@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/clientes", response_class=HTMLResponse)
def clientes_page(request: Request):
    return templates.TemplateResponse("clientes.html", {"request": request})


@app.get("/clientes/novo", response_class=HTMLResponse)
def clientes_form_page(request: Request):
    return templates.TemplateResponse("clientes_form.html", {"request": request})


@app.get("/clientes/editar/{cliente_id}", response_class=HTMLResponse)
def clientes_edit_page(request: Request, cliente_id: int):
    return templates.TemplateResponse(
        "clientes_form.html", {"request": request, "cliente_id": cliente_id},
    )


@app.get("/pets", response_class=HTMLResponse)
def pets_page(request: Request):
    return templates.TemplateResponse("pets.html", {"request": request})


@app.get("/pets/novo", response_class=HTMLResponse)
def pets_form_page(request: Request):
    return templates.TemplateResponse("pets_form.html", {"request": request})


@app.get("/servicos", response_class=HTMLResponse)
def servicos_page(request: Request):
    return templates.TemplateResponse("servicos.html", {"request": request})


@app.get("/funcionarios", response_class=HTMLResponse)
def funcionarios_page(request: Request):
    return templates.TemplateResponse("funcionarios.html", {"request": request})


@app.get("/agenda", response_class=HTMLResponse)
def agenda_page(request: Request):
    return templates.TemplateResponse("agenda.html", {"request": request})


@app.get("/agenda-veterinaria", response_class=HTMLResponse)
def agenda_veterinaria_page(request: Request):
    return templates.TemplateResponse("agenda_veterinaria.html", {"request": request})


@app.get("/atendimento-clinico/{agendamento_id}", response_class=HTMLResponse)
def atendimento_clinico_page(request: Request, agendamento_id: int):
    return templates.TemplateResponse(
        "atendimento_clinico.html", {"request": request, "agendamento_id": agendamento_id},
    )


@app.get("/producao", response_class=HTMLResponse)
def producao_page(request: Request):
    return templates.TemplateResponse("producao.html", {"request": request})


@app.get("/estoque", response_class=HTMLResponse)
def estoque_page(request: Request):
    return templates.TemplateResponse("estoque.html", {"request": request})


@app.get("/financeiro", response_class=HTMLResponse)
def financeiro_page(request: Request):
    return templates.TemplateResponse("financeiro.html", {"request": request})


@app.get("/pdv", response_class=HTMLResponse)
def pdv_page(request: Request):
    return templates.TemplateResponse("pdv.html", {"request": request})


@app.get("/crm", response_class=HTMLResponse)
def crm_page(request: Request):
    return templates.TemplateResponse("crm.html", {"request": request})


@app.get("/relatorios", response_class=HTMLResponse)
def relatorios_page(request: Request):
    return templates.TemplateResponse("relatorios.html", {"request": request})


@app.get("/relatorios/comissao/demonstrativo/{fechamento_id}", response_class=HTMLResponse)
def demonstrativo_comissao_page(request: Request, fechamento_id: int):
    return templates.TemplateResponse(
        "comissao_demonstrativo.html",
        {
            "request": request,
            "fechamento_id": fechamento_id,
        },
    )


@app.get("/configuracoes", response_class=HTMLResponse)
def configuracoes_page(request: Request):
    return templates.TemplateResponse("configuracoes.html", {"request": request})


@app.get("/servicos/novo", response_class=HTMLResponse)
def servicos_form_page(request: Request):
    return templates.TemplateResponse("servicos_form.html", {"request": request})


@app.get("/servicos/editar/{servico_id}", response_class=HTMLResponse)
def servicos_edit_page(request: Request, servico_id: int):
    return templates.TemplateResponse(
        "servicos_form.html", {"request": request, "servico_id": servico_id},
    )


@app.get("/funcionarios/novo", response_class=HTMLResponse)
def funcionarios_form_page(request: Request):
    return templates.TemplateResponse("funcionarios_form.html", {"request": request})


@app.get("/funcionarios/editar/{funcionario_id}", response_class=HTMLResponse)
def funcionarios_edit_page(request: Request, funcionario_id: int):
    return templates.TemplateResponse(
        "funcionarios_form.html", {"request": request, "funcionario_id": funcionario_id},
    )