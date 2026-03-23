import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.estoque_api import router as estoque_router
from app.core.deps import get_db


def _fake_db():
    yield None


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(estoque_router)
    app.dependency_overrides[get_db] = _fake_db
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    return TestClient(app)