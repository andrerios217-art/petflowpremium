from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.database import Base, engine
from app.models import *  # noqa
from app.api import auth, empresas, usuarios, configuracoes

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Pet Flow Premium", version="1.0.0")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(auth.router)
app.include_router(empresas.router)
app.include_router(usuarios.router)
app.include_router(configuracoes.router)


@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})