"""Смок-тесты эндпоинтов здоровья (этап 1 каркаса).

Проверяются без внешних сервисов: /healthz всегда 200, /readyz отвечает
200 когда БД/Redis/миграции доступны (после `make up` + `make migrate`),
и 503 в противном случае — что подтверждает, что эндпоинт подключён.
"""

from fastapi.testclient import TestClient

from olenevod.main import app


def test_healthz_returns_200():
    with TestClient(app) as client:
        response = client.get("/healthz")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["components"] == {}


def test_readyz_responds_with_status():
    with TestClient(app) as client:
        response = client.get("/readyz")
        assert response.status_code in (200, 503)
        body = response.json()
        assert isinstance(body, dict)
