"""Тесты HTTP-роутов каталога (этап 4) на реальной тестовой PostgreSQL.

БД: TEST_DATABASE_URL (postgres:postgres@localhost:5432/olenevod_test).
Зависимость сессии переопределяется на тестовую БД; данные сидятся
прямыми INSERT'ами — моки не используются. Каждый тест выполняется в
своем цикле anyio (httpx.ASGITransport), поэтому сессии SQLAlchemy и
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

from olenevod.interfaces.http.catalog import get_session
from olenevod.main import app

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/olenevod_test"

CITY_MOSCOW_ID = uuid.UUID("11111111-1111-1111-1111-111111111001")
CATEGORY_PRODUCTS_ID = uuid.UUID("22222222-2222-2222-2222-222222222001")
PRODUCT_MILK_ID = uuid.UUID("33333333-3333-3333-3333-333333333001")
VARIANT_MILK_1L_ID = uuid.UUID("44444444-4444-4444-4444-444444444001")

_test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
_test_session_factory = async_sessionmaker(_test_engine, expire_on_commit=False)


async def _override_get_session():
    async with _test_session_factory() as session:
        yield session


app.dependency_overrides[get_session] = _override_get_session

SEED_SQL = """
INSERT INTO cities (id, slug, name, region, timezone, is_active) VALUES
  ('11111111-1111-1111-1111-111111111001', 'moscow', 'Москва', 'Москва', 'Europe/Moscow', true),
  ('11111111-1111-1111-1111-111111111002', 'spb', 'Санкт-Петербург', 'Санкт-Петербург', 'Europe/Moscow', true)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO categories (id, parent_id, slug, name, is_published, sort) VALUES
  ('22222222-2222-2222-2222-222222222001', NULL, 'produkty', 'Продукты', true, 10),
  ('22222222-2222-2222-2222-222222222002', '22222222-2222-2222-2222-222222222001', 'moloko', 'Молоко и молочные продукты', true, 20)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO products (id, category_id, slug, name, short_description, is_published) VALUES
  ('33333333-3333-3333-3333-333333333001', '22222222-2222-2222-2222-222222222002', 'moloko-klassicheskoe', 'Молоко классическое', 'Пастеризованное 2,5%', true)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO product_variants (id, product_id, sku, name, unit_type, pack_weight_g) VALUES
  ('44444444-4444-4444-4444-444444444001', '33333333-3333-3333-3333-333333333001', 'MOLOKO-1L', '1 л', 'piece', 1000)
ON CONFLICT (sku) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO city_offers (id, city_id, variant_id, price_kop, old_price_kop, is_published) VALUES
  ('66666666-6666-6666-6666-666666666001', '11111111-1111-1111-1111-111111111001', '44444444-4444-4444-4444-444444444001', 9500, 10500, true),
  ('66666666-6666-6666-6666-666666666002', '11111111-1111-1111-1111-111111111002', '44444444-4444-4444-4444-444444444001', 9900, NULL, true)
ON CONFLICT (city_id, variant_id) DO UPDATE SET price_kop = EXCLUDED.price_kop;

INSERT INTO warehouses (id, city_id, name, address, is_active) VALUES
  ('55555555-5555-5555-5555-555555555001', '11111111-1111-1111-1111-111111111001', 'Склад Москва-1', 'ул. Тестовая, 1', true),
  ('55555555-5555-5555-5555-555555555002', '11111111-1111-1111-1111-111111111001', 'Склад Москва-2', 'ул. Тестовая, 2', true)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO stock_levels (warehouse_id, variant_id, on_hand, reserved) VALUES
  ('55555555-5555-5555-5555-555555555001', '44444444-4444-4444-4444-444444444001', 10, 2),
  ('55555555-5555-5555-5555-555555555002', '44444444-4444-4444-4444-444444444001', 5, 0)
ON CONFLICT (warehouse_id, variant_id) DO UPDATE SET on_hand = EXCLUDED.on_hand, reserved = EXCLUDED.reserved;
"""


async def _load_seed() -> None:
    conn = await asyncpg.connect(TEST_DATABASE_URL.replace("+asyncpg", ""))
    try:
        await conn.execute(SEED_SQL)
    finally:
        await conn.close()


@pytest.fixture(autouse=True)
def _seed_db(alembic_upgrade_head: None) -> None:
    """Применить миграции и загрузить демо-данные в тестовую БД."""
    anyio.run(_load_seed)


def _request(method: str, path: str, params: dict | None = None) -> httpx.Response:
    async def _run() -> httpx.Response:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            return await client.request(method, path, params=params)

    return anyio.run(_run)


def test_cities_returns_200() -> None:
    response = _request("GET", "/cities")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert any(city["slug"] == "moscow" for city in body)


def _find_slug(nodes: list[dict], slug: str) -> bool:
    for node in nodes:
        if node.get("slug") == slug:
            return True
        if _find_slug(node.get("children", []), slug):
            return True
    return False


def test_categories_returns_200() -> None:
    response = _request("GET", "/categories")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert _find_slug(body, "moloko")


def test_products_returns_200() -> None:
    response = _request(
        "GET",
        "/products",
        params={"city_id": str(CITY_MOSCOW_ID), "limit": 10, "offset": 0},
    )
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert body[0]["variant_id"] == str(VARIANT_MILK_1L_ID)
    assert body[0]["available_qty"] >= 0


def test_products_with_category_filter_returns_200() -> None:
    response = _request(
        "GET",
        "/products",
        params={
            "city_id": str(CITY_MOSCOW_ID),
            "category_id": str(CATEGORY_PRODUCTS_ID),
            "search": "Молоко",
        },
    )
    assert response.status_code == 200


def test_product_card_returns_200() -> None:
    response = _request(
        "GET",
        f"/products/{PRODUCT_MILK_ID}",
        params={"city_id": str(CITY_MOSCOW_ID)},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(PRODUCT_MILK_ID)
    assert isinstance(body["variants"], list)
    assert len(body["variants"]) >= 1
    variant = body["variants"][0]
    assert variant["sku"] == "MOLOKO-1L"
    assert variant["price_kop"] == 9500
    assert isinstance(variant["available_by_city"], list)


def test_stock_returns_200() -> None:
    response = _request(
        "GET", "/stock", params={"variant_ids": [str(VARIANT_MILK_1L_ID)]}
    )
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert any(item["variant_id"] == str(VARIANT_MILK_1L_ID) for item in body)


def test_unknown_city_returns_404() -> None:
    response = _request(
        "GET", "/products", params={"city_id": str(uuid.uuid4()), "limit": 10}
    )
    assert response.status_code == 404
