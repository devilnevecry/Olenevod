"""Тесты HTTP-роута доставки GET /delivery/quote (этап 9) на реальной тестовой PostgreSQL.

БД: TEST_DATABASE_URL (postgres:postgres@localhost:5432/olenevod_test).
Зависимость сессии переопределяется на тестовую БД; данные сидятся
прямыми INSERT'ами — моки не используются. Каждый тест — sync-функция с
anyio.run + httpx.ASGITransport, поэтому сессии SQLAlchemy и asyncpg-соединения
никогда не переплетаются между циклами.
"""

import uuid

import anyio
import asyncpg
import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from olenevod.interfaces.http.delivery import get_session as delivery_get_session
from olenevod.main import app

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/olenevod_test"

DELIVERY_CITY_MSK = uuid.UUID("11111111-1111-1111-1111-111111111101")
DELIVERY_CITY_SPB = uuid.UUID("11111111-1111-1111-1111-111111111102")
DELIVERY_CITY_KAZAN = uuid.UUID("11111111-1111-1111-1111-111111111103")  # без зоны доставки
DELIVERY_CATEGORY_ID = uuid.UUID("22222222-2222-2222-2222-222222222103")
DELIVERY_PRODUCT_ID = uuid.UUID("33333333-3333-3333-3333-333333333104")
DELIVERY_VARIANT_LIGHT = uuid.UUID("44444444-4444-4444-4444-444444444101")  # 500 г
DELIVERY_VARIANT_HEAVY = uuid.UUID("44444444-4444-4444-4444-444444444102")  # 2000 г
DELIVERY_ZONE_MSK_ID = uuid.UUID("77777777-7777-7777-7777-777777777101")
DELIVERY_ZONE_SPB_ID = uuid.UUID("77777777-7777-7777-7777-777777777102")
DELIVERY_TARIFF_MSK_ID = uuid.UUID("88888888-8888-8888-8888-888888888101")
DELIVERY_TARIFF_SPB_ID = uuid.UUID("88888888-8888-8888-8888-888888888102")
DELIVERY_WH_MSK = uuid.UUID("55555555-5555-5555-5555-555555555101")
DELIVERY_WH_SPB = uuid.UUID("55555555-5555-5555-5555-555555555102")
DELIVERY_OFFER_MSK_LIGHT = uuid.UUID("66666666-6666-6666-6666-666666666101")
DELIVERY_OFFER_MSK_HEAVY = uuid.UUID("66666666-6666-6666-6666-666666666102")
DELIVERY_OFFER_SPB_LIGHT = uuid.UUID("66666666-6666-6666-6666-666666666103")
DELIVERY_OFFER_SPB_HEAVY = uuid.UUID("66666666-6666-6666-6666-666666666104")

_test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
_test_session_factory = async_sessionmaker(_test_engine, expire_on_commit=False)

SEED_SQL = """
INSERT INTO cities (id, slug, name, region, timezone, is_active) VALUES
  ('11111111-1111-1111-1111-111111111101', 'delivery-moscow', 'Москва доставка', 'Москва', 'Europe/Moscow', true),
  ('11111111-1111-1111-1111-111111111102', 'delivery-spb', 'Петербург доставка', 'СПб', 'Europe/Moscow', true),
  ('11111111-1111-1111-1111-111111111103', 'delivery-kazan', 'Казань доставка', 'Татарстан', 'Europe/Moscow', true)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO categories (id, parent_id, slug, name, is_published, sort) VALUES
  ('22222222-2222-2222-2222-222222222103', NULL, 'delivery-test', 'Тест доставки', true, 100)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO products (id, category_id, slug, name, is_published) VALUES
  ('33333333-3333-3333-3333-333333333104', '22222222-2222-2222-2222-222222222103', 'delivery-produkt', 'Продукт доставки', true)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO product_variants (id, product_id, sku, name, unit_type, pack_weight_g) VALUES
  ('44444444-4444-4444-4444-444444444101', '33333333-3333-3333-3333-333333333104', 'DELIV-LIGHT', 'Лёгкий вариант', 'piece', 500),
  ('44444444-4444-4444-4444-444444444102', '33333333-3333-3333-3333-333333333104', 'DELIV-HEAVY', 'Тяжёлый вариант', 'piece', 2000)
ON CONFLICT (sku) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO city_offers (id, city_id, variant_id, price_kop, is_published) VALUES
  ('66666666-6666-6666-6666-666666666101', '11111111-1111-1111-1111-111111111101', '44444444-4444-4444-4444-444444444101', 1000, true),
  ('66666666-6666-6666-6666-666666666102', '11111111-1111-1111-1111-111111111101', '44444444-4444-4444-4444-444444444102', 1000, true),
  ('66666666-6666-6666-6666-666666666103', '11111111-1111-1111-1111-111111111102', '44444444-4444-4444-4444-444444444101', 1000, true),
  ('66666666-6666-6666-6666-666666666104', '11111111-1111-1111-1111-111111111102', '44444444-4444-4444-4444-444444444102', 1000, true)
ON CONFLICT (city_id, variant_id) DO UPDATE SET price_kop = EXCLUDED.price_kop;

INSERT INTO warehouses (id, city_id, name, is_active) VALUES
  ('55555555-5555-5555-5555-555555555101', '11111111-1111-1111-1111-111111111101', 'Склад Москва доставка', true),
  ('55555555-5555-5555-5555-555555555102', '11111111-1111-1111-1111-111111111102', 'Склад СПб доставка', true)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO stock_levels (warehouse_id, variant_id, on_hand, reserved) VALUES
  ('55555555-5555-5555-5555-555555555101', '44444444-4444-4444-4444-444444444101', 10, 0),
  ('55555555-5555-5555-5555-555555555101', '44444444-4444-4444-4444-444444444102', 10, 0),
  ('55555555-5555-5555-5555-555555555102', '44444444-4444-4444-4444-444444444101', 10, 0),
  ('55555555-5555-5555-5555-555555555102', '44444444-4444-4444-4444-444444444102', 10, 0)
ON CONFLICT (warehouse_id, variant_id) DO UPDATE SET on_hand = EXCLUDED.on_hand, reserved = EXCLUDED.reserved;

INSERT INTO delivery_zones (id, city_id, zone_name, base_fee, per_kg_fee, free_from_amount) VALUES
  ('77777777-7777-7777-7777-777777777101', '11111111-1111-1111-1111-111111111101', 'Центральный', 500, 100, 5000),
  ('77777777-7777-7777-7777-777777777102', '11111111-1111-1111-1111-111111111102', 'Северо-Западный', 700, 150, NULL)
ON CONFLICT (city_id) DO UPDATE SET zone_name = EXCLUDED.zone_name;

INSERT INTO delivery_tariffs (id, zone_id, name, estimated_days, is_active) VALUES
  ('88888888-8888-8888-8888-888888888101', '77777777-7777-7777-7777-777777777101', 'Стандарт', 3, true),
  ('88888888-8888-8888-8888-888888888102', '77777777-7777-7777-7777-777777777102', 'Стандарт', 2, true)
ON CONFLICT (zone_id) DO UPDATE SET name = EXCLUDED.name;
"""


async def _load_seed() -> None:
    conn = await asyncpg.connect(TEST_DATABASE_URL.replace("+asyncpg", ""))
    try:
        await conn.execute(SEED_SQL)
    finally:
        await conn.close()


async def _override_get_session():
    async with _test_session_factory() as session:
        yield session


app.dependency_overrides[delivery_get_session] = _override_get_session


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


def test_quote_moscow_light_paid() -> None:
    response = _request(
        "GET",
        "/delivery/quote",
        params={
            "city_id": str(DELIVERY_CITY_MSK),
            "items": [str(DELIVERY_VARIANT_LIGHT)],
            "total_amount": 1000,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    # 500 г -> 1 кг, fee = 500 + 100*1 = 600 kop; 1000 < 5000 -> платная.
    assert body["fee"] == 600
    assert body["free_delivery"] is False
    assert body["estimated_days"] == 3
    assert body["zone"] == "Центральный"
    assert body["city_id"] == str(DELIVERY_CITY_MSK)


def test_quote_moscow_free_above_threshold() -> None:
    response = _request(
        "GET",
        "/delivery/quote",
        params={
            "city_id": str(DELIVERY_CITY_MSK),
            "items": [str(DELIVERY_VARIANT_LIGHT)],
            "total_amount": 6000,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["fee"] == 0
    assert body["free_delivery"] is True
    assert body["estimated_days"] == 3
    assert body["zone"] == "Центральный"


def test_quote_spb_heavy() -> None:
    response = _request(
        "GET",
        "/delivery/quote",
        params={
            "city_id": str(DELIVERY_CITY_SPB),
            "items": [str(DELIVERY_VARIANT_HEAVY)],
            "total_amount": 0,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    # 2000 г -> 2 кг, fee = 700 + 150*2 = 1000 kop; free_from_amount нет -> платная.
    assert body["fee"] == 1000
    assert body["free_delivery"] is False
    assert body["estimated_days"] == 2
    assert body["zone"] == "Северо-Западный"


def test_quote_multi_item() -> None:
    response = _request(
        "GET",
        "/delivery/quote",
        params={
            "city_id": str(DELIVERY_CITY_MSK),
            "items": [str(DELIVERY_VARIANT_LIGHT), str(DELIVERY_VARIANT_HEAVY)],
            "total_amount": 0,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    # 500 + 2000 = 2500 г -> 3 кг, fee = 500 + 100*3 = 800 kop.
    assert body["fee"] == 800
    assert body["free_delivery"] is False
    assert body["estimated_days"] == 3


def test_quote_unknown_city_returns_404() -> None:
    response = _request(
        "GET",
        "/delivery/quote",
        params={"city_id": str(uuid.uuid4()), "items": [str(DELIVERY_VARIANT_LIGHT)]},
    )
    assert response.status_code == 404


def test_quote_known_city_without_zone_returns_404() -> None:
    response = _request(
        "GET",
        "/delivery/quote",
        params={"city_id": str(DELIVERY_CITY_KAZAN), "items": [str(DELIVERY_VARIANT_LIGHT)]},
    )
    assert response.status_code == 404
