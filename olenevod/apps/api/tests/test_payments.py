"""Тесты HTTP-роутов платежей (этап 6) на реальной тестовой PostgreSQL.

БД: TEST_DATABASE_URL (postgres:postgres@localhost:5432/olenevod_test).
Сессия переопределяется на тестовую БД (NullPool); данные сидятся прямыми
INSERT'ами — моки провайдера не используются. Каждый тест — в своём цикле
anyio (httpx.ASGITransport), сессии SQLAlchemy не переплетаются.
"""

import uuid

import anyio
import asyncpg
import httpx
import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from olenevod.application.order_service import OrderService
from olenevod.application.payment_service import PaymentService
from olenevod.interfaces.http.orders import get_session as orders_get_session
from olenevod.interfaces.http.payments import get_session as payments_get_session
from olenevod.main import app

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/olenevod_test"

PAY_CITY_ID = uuid.UUID("11111111-1111-1111-1111-111111111004")
PAY_CATEGORY_ID = uuid.UUID("22222222-2222-2222-2222-222222222004")
PAY_PRODUCT_ID = uuid.UUID("33333333-3333-3333-3333-333333333003")
PAY_VARIANT_ID = uuid.UUID("44444444-4444-4444-4444-444444444003")
PAY_WAREHOUSE_ID = uuid.UUID("55555555-5555-5555-5555-555555555004")
PAY_CITY_OFFER_ID = uuid.UUID("66666666-6666-6666-6666-666666666004")

_test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
_test_session_factory = async_sessionmaker(_test_engine, expire_on_commit=False)


async def _override_get_session():
    async with _test_session_factory() as session:
        yield session


app.dependency_overrides[orders_get_session] = _override_get_session
app.dependency_overrides[payments_get_session] = _override_get_session

SEED_SQL = """
INSERT INTO cities (id, slug, name, region, timezone, is_active) VALUES
  ('11111111-1111-1111-1111-111111111004', 'pay-moscow', 'Москва платежи', 'Москва', 'Europe/Moscow', true)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO categories (id, parent_id, slug, name, is_published, sort) VALUES
  ('22222222-2222-2222-2222-222222222004', NULL, 'pay-test', 'Тест платежей', true, 100)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO products (id, category_id, slug, name, is_published) VALUES
  ('33333333-3333-3333-3333-333333333003', '22222222-2222-2222-2222-222222222004', 'pay-produkt', 'Продукт оплаты', true)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO product_variants (id, product_id, sku, name, unit_type) VALUES
  ('44444444-4444-4444-4444-444444444003', '33333333-3333-3333-3333-333333333003', 'PAY-001', 'Вариант оплаты', 'piece')
ON CONFLICT (sku) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO city_offers (id, city_id, variant_id, price_kop, is_published) VALUES
  ('66666666-6666-6666-6666-666666666004', '11111111-1111-1111-1111-111111111004', '44444444-4444-4444-4444-444444444003', 9500, true)
ON CONFLICT (city_id, variant_id) DO UPDATE SET price_kop = EXCLUDED.price_kop;

INSERT INTO warehouses (id, city_id, name, is_active) VALUES
  ('55555555-5555-5555-5555-555555555004', '11111111-1111-1111-1111-111111111004', 'Склад оплаты', true)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO stock_levels (warehouse_id, variant_id, on_hand, reserved) VALUES
  ('55555555-5555-5555-5555-555555555004', '44444444-4444-4444-4444-444444444003', 100, 0)
ON CONFLICT (warehouse_id, variant_id) DO UPDATE SET on_hand = EXCLUDED.on_hand, reserved = EXCLUDED.reserved;
"""


async def _load_seed() -> None:
    conn = await asyncpg.connect(TEST_DATABASE_URL.replace("+asyncpg", ""))
    try:
        await conn.execute(SEED_SQL)
    finally:
        await conn.close()


async def _get_order(order_id: uuid.UUID):
    async with _test_session_factory() as session:
        return await OrderService(session).get_order(order_id)


async def _create_payment_via_service(order_id: uuid.UUID) -> str:
    async with _test_session_factory() as session:
        result = await OrderService(session).get_order(order_id)
        assert result is not None, f"order {order_id} not found"
        order, _items = result
        return await PaymentService(session).create_payment(order)


@pytest.fixture(autouse=True)
def _seed_db(alembic_config: Config, db_available: bool) -> None:
    """Применить миграции и загрузить демо-данные в тестовую БД."""

    def runner() -> None:
        command.upgrade(alembic_config, "head")

    if not db_available:
        pytest.skip("Тестовая PostgreSQL-БД недоступна (нужен локальный postgres/Docker)")
    runner()
    anyio.run(_load_seed)


def _request(
    method: str,
    path: str,
    params: dict | None = None,
    json_body: dict | None = None,
) -> httpx.Response:
    async def _run() -> httpx.Response:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            return await client.request(method, path, params=params, json=json_body)

    return anyio.run(_run)


PAY_ITEMS = [{"product_variant_id": str(PAY_VARIANT_ID), "qty": 3}]


def test_create_payment_returns_simulated_url() -> None:
    response = _request(
        "POST",
        "/orders",
        json_body={
            "city_id": str(PAY_CITY_ID),
            "customer_name": "Покупатель Тестовый",
            "customer_phone": "+79000000000",
            "items": PAY_ITEMS,
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "pending_payment"
    order_id = body["id"]

    url = anyio.run(_create_payment_via_service, order_id)
    assert url.startswith("https://pay.olenevod.local/pay/")
    assert f"provider=yukassa&amount={body['total_amount']}" in url

    # Запись о платеже доступна через эндпоинт статуса.
    status_response = _request("GET", f"/payments/{order_id}/status")
    assert status_response.status_code == 200, status_response.text
    status_body = status_response.json()
    assert status_body["order_id"] == order_id
    assert status_body["provider"] == "yukassa"
    assert status_body["amount"] == body["total_amount"]
    assert status_body["status"] == "pending"


def test_webhook_changes_order_status_pending_payment_to_new() -> None:
    response = _request(
        "POST",
        "/orders",
        json_body={
            "city_id": str(PAY_CITY_ID),
            "customer_name": "Покупатель Тестовый",
            "customer_phone": "+79000000000",
            "items": PAY_ITEMS,
        },
    )
    assert response.status_code == 201, response.text
    order_id = response.json()["id"]
    assert response.json()["status"] == "pending_payment"

    anyio.run(_create_payment_via_service, order_id)

    webhook_response = _request(
        "POST", "/payments/webhook/yukassa", json_body={"order_id": str(order_id)}
    )
    assert webhook_response.status_code == 200, webhook_response.text
    assert webhook_response.json()["status"] == "new"

    get_response = _request("GET", f"/orders/{order_id}")
    assert get_response.status_code == 200, get_response.text
    assert get_response.json()["status"] == "new"


def test_payment_status_unknown_returns_404() -> None:
    response = _request("GET", f"/payments/{uuid.uuid4()}/status")
    assert response.status_code == 404


def test_webhook_unknown_order_returns_404() -> None:
    response = _request(
        "POST", "/payments/webhook/yukassa", json_body={"order_id": str(uuid.uuid4())}
    )
    assert response.status_code == 404
