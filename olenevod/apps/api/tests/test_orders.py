"""Тесты HTTP-роутов заказов (этап 5) на реальной тестовой PostgreSQL.

БД: TEST_DATABASE_URL (postgres:postgres@localhost:5432/olenevod_test).
Зависимость сессии переопределяется на тестовую БД; данные сидятся
прямыми INSERT'ами — моки не используются. Каждый тест выполняется в
своём цикле anyio (httpx.ASGITransport), поэтому сессии SQLAlchemy и
asyncpg-соединения никогда не переплетаются между циклами.
"""

import uuid

import anyio
import asyncpg
import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from olenevod.interfaces.http.orders import get_session as orders_get_session
from olenevod.main import app

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/olenevod_test"

ORDER_CITY_ID = uuid.UUID("11111111-1111-1111-1111-111111111001")
ORDER_CATEGORY_ID = uuid.UUID("22222222-2222-2222-2222-222222222003")
ORDER_PRODUCT_ID = uuid.UUID("33333333-3333-3333-3333-333333333002")
ORDER_VARIANT_ID = uuid.UUID("44444444-4444-4444-4444-444444444002")
ORDER_WAREHOUSE_ID = uuid.UUID("55555555-5555-5555-5555-555555555003")
ORDER_CITY_OFFER_ID = uuid.UUID("66666666-6666-6666-6666-666666666003")

_test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
_test_session_factory = async_sessionmaker(_test_engine, expire_on_commit=False)


async def _override_get_session():
    async with _test_session_factory() as session:
        yield session


app.dependency_overrides[orders_get_session] = _override_get_session

SEED_SQL = """
INSERT INTO cities (id, slug, name, region, timezone, is_active) VALUES
  ('11111111-1111-1111-1111-111111111001', 'moscow', 'Москва', 'Москва', 'Europe/Moscow', true)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO categories (id, parent_id, slug, name, is_published, sort) VALUES
  ('22222222-2222-2222-2222-222222222003', NULL, 'zakazy-test', 'Тест заказов', true, 100)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO products (id, category_id, slug, name, is_published) VALUES
  ('33333333-3333-3333-3333-333333333002', '22222222-2222-2222-2222-222222222003', 'zakaz-produkt', 'Продукт для заказа', true)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO product_variants (id, product_id, sku, name, unit_type) VALUES
  ('44444444-4444-4444-4444-444444444002', '33333333-3333-3333-3333-333333333002', 'ZAKAZ-001', 'Вариант для заказа', 'piece')
ON CONFLICT (sku) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO city_offers (id, city_id, variant_id, price_kop, is_published) VALUES
  ('66666666-6666-6666-6666-666666666003', '11111111-1111-1111-1111-111111111001', '44444444-4444-4444-4444-444444444002', 9500, true)
ON CONFLICT (city_id, variant_id) DO UPDATE SET price_kop = EXCLUDED.price_kop;

INSERT INTO warehouses (id, city_id, name, is_active) VALUES
  ('55555555-5555-5555-5555-555555555003', '11111111-1111-1111-1111-111111111001', 'Склад заказы', true)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO stock_levels (warehouse_id, variant_id, on_hand, reserved) VALUES
  ('55555555-5555-5555-5555-555555555003', '44444444-4444-4444-4444-444444444002', 10, 2)
ON CONFLICT (warehouse_id, variant_id) DO UPDATE SET on_hand = EXCLUDED.on_hand, reserved = EXCLUDED.reserved;
"""


async def _load_seed() -> None:
    conn = await asyncpg.connect(TEST_DATABASE_URL.replace("+asyncpg", ""))
    try:
        await conn.execute(SEED_SQL)
    finally:
        await conn.close()


async def _reserved_for(variant_id: uuid.UUID, city_id: uuid.UUID = ORDER_CITY_ID) -> int:
    conn = await asyncpg.connect(TEST_DATABASE_URL.replace("+asyncpg", ""))
    try:
        row = await conn.fetchrow(
            """
            SELECT coalesce(sum(sl.reserved), 0)
            FROM stock_levels sl
            JOIN warehouses w ON w.id = sl.warehouse_id
            WHERE w.city_id = $1 AND sl.variant_id = $2
            """,
            city_id,
            variant_id,
        )
        return int(row[0])
    finally:
        await conn.close()


@pytest.fixture(autouse=True)
def _seed_db(alembic_upgrade_head: None) -> None:
    """Применить миграции и загрузить демо-данные в тестовую БД."""
    anyio.run(_load_seed)


def _request(method: str, path: str, params: dict | None = None, json_body: dict | None = None) -> httpx.Response:
    async def _run() -> httpx.Response:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            return await client.request(method, path, params=params, json=json_body)

    return anyio.run(_run)


def test_place_order_returns_201_and_reserves_stock() -> None:
    before = anyio.run(_reserved_for, ORDER_VARIANT_ID)

    response = _request(
        "POST",
        "/orders",
        json_body={
            "city_id": str(ORDER_CITY_ID),
            "customer_name": "Покупатель Тестовый",
            "customer_phone": "+79000000000",
            "items": [{"product_variant_id": str(ORDER_VARIANT_ID), "qty": 3}],
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "pending_payment"
    assert body["total_amount"] == 28500  # 9500 kop * 3
    assert len(body["items"]) == 1
    assert body["items"][0]["product_variant_id"] == str(ORDER_VARIANT_ID)
    assert body["items"][0]["qty"] == 3
    assert body["items"][0]["price"] == 9500

    order_id = body["id"]

    # Резерв стока вырос (on_hand - reserved уменьшился, reserved увеличился).
    after = anyio.run(_reserved_for, ORDER_VARIANT_ID)
    assert after == before + 3

    # Карточка заказа.
    get_response = _request("GET", f"/orders/{order_id}")
    assert get_response.status_code == 200, get_response.text
    get_body = get_response.json()
    assert get_body["id"] == order_id
    assert get_body["status"] == "pending_payment"
    assert get_body["total_amount"] == 28500
    assert len(get_body["items"]) == 1


def test_get_unknown_order_returns_404() -> None:
    response = _request("GET", f"/orders/{uuid.uuid4()}")
    assert response.status_code == 404
