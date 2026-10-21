import os

import pytest
from fastapi.testclient import TestClient

# Тестам нужна живая PostgreSQL. Локально: `docker compose up -d db`,
# в CI — service-контейнер postgres (см. .github/workflows/ci.yml).
os.environ.setdefault("POSTGRES_PASSWORD", "test")

from guestbook import db  # noqa: E402
from guestbook.config import get_settings  # noqa: E402
from guestbook.main import app  # noqa: E402


@pytest.fixture
def db_url() -> str:
    return get_settings().database_url


@pytest.fixture
def client(db_url):
    with TestClient(app) as c:  # lifespan прогоняет миграции
        with db.connect(db_url) as conn:
            conn.execute("TRUNCATE messages RESTART IDENTITY")
        yield c
