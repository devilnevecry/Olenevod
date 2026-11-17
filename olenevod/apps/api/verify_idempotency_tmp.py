"""Быстрая проверка идемпотентности заказов через HTTP-слой (без моков)."""
import uuid, anyio, asyncpg, httpx
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from olenevod.interfaces.http.orders import get_session as orders_get_session
from olenevod.main import app

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/olenevod_test"

CITY_ID = uuid.UUID("11111111-1111-1111-1111-111111111001")
VARIANT_ID = uuid.UUID("44444444-4444-4444-4444-444444444002")

_test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
_test_session_factory = async_sessionmaker(_test_engine, expire_on_commit=False)

async def _override_get_session():
    async with _test_session_factory() as session:
        yield session

app.dependency_overrides[orders_get_session] = _override_get_session

async def _reserved_for(variant_id: uuid.UUID) -> int:
    conn = await asyncpg.connect(TEST_DATABASE_URL.replace("+asyncpg", ""))
    try:
        row = await conn.fetchrow(
            "SELECT coalesce(sum(sl.reserved), 0) FROM stock_levels sl JOIN warehouses w ON w.id = sl.warehouse_id WHERE w.city_id = $1 AND sl.variant_id = $2",
            CITY_ID, variant_id,
        )
        return int(row[0])
    finally:
        await conn.close()

async def main():
    # Seed data (same as test_orders.py)
    conn = await asyncpg.connect(TEST_DATABASE_URL.replace("+asyncpg", ""))
    await conn.execute("""
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
      ('55555555-5555-5555-5555-555555555003', '44444444-4444-4444-4444-444444444002', 100, 0)
    ON CONFLICT (warehouse_id, variant_id) DO UPDATE SET on_hand = EXCLUDED.on_hand, reserved = EXCLUDED.reserved;
    """)
    await conn.close()

    # Clean up any existing orders with our test key
    conn = await asyncpg.connect(TEST_DATABASE_URL.replace("+asyncpg", ""))
    await conn.execute("DELETE FROM orders WHERE idempotency_key = 'test-idempotent-key-1'")
    await conn.close()

    before = await _reserved_for(VARIANT_ID)
    print(f"Reserved before: {before}")

    IDEMPOTENCY_KEY = "test-idempotent-key-1"
    order_payload = {
        "city_id": str(CITY_ID),
        "customer_name": "Тестовый Покупатель",
        "customer_phone": "+79000000000",
        "items": [{"product_variant_id": str(VARIANT_ID), "qty": 3}],
        "idempotency_key": IDEMPOTENCY_KEY,
    }

    # First request
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        r1 = await client.post("/orders", json=order_payload)
    assert r1.status_code == 201, f"First request failed: {r1.text}"
    body1 = r1.json()
    order_id_1 = body1["id"]
    print(f"First request: order_id={order_id_1}, key={body1.get('idempotency_key')}, reserved_items={len(body1['items'])}")
    assert body1["idempotency_key"] == IDEMPOTENCY_KEY

    after1 = await _reserved_for(VARIANT_ID)
    print(f"Reserved after first: {after1} (delta={after1 - before})")
    assert after1 == before + 3, f"Expected reserved to increase by 3, got {after1 - before}"

    # Second request with same key
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        r2 = await client.post("/orders", json=order_payload)
    assert r2.status_code == 201, f"Second request failed: {r2.text}"
    body2 = r2.json()
    order_id_2 = body2["id"]
    print(f"Second request: order_id={order_id_2}, key={body2.get('idempotency_key')}, reserved_items={len(body2['items'])}")

    # Same order_id returned
    assert order_id_1 == order_id_2, f"Expected same order_id, got {order_id_1} vs {order_id_2}"
    print("PASS: Same order_id returned for duplicate key")

    # Reserved not doubled
    after2 = await _reserved_for(VARIANT_ID)
    print(f"Reserved after second: {after2} (delta from first={after2 - after1})")
    assert after2 == after1, f"Expected reserved unchanged after duplicate, got {after2} vs {after1}"
    print("PASS: Stock not double-reserved")

    # Third request without key (should create new order)
    order_payload_no_key = dict(order_payload)
    del order_payload_no_key["idempotency_key"]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        r3 = await client.post("/orders", json=order_payload_no_key)
    assert r3.status_code == 201, f"Third request failed: {r3.text}"
    body3 = r3.json()
    order_id_3 = body3["id"]
    print(f"Third request (no key): order_id={order_id_3}")
    assert order_id_3 != order_id_1, "Expected different order_id for request without key"
    print("PASS: Request without idempotency_key creates new order")

    # Cleanup: delete test orders
    conn = await asyncpg.connect(TEST_DATABASE_URL.replace("+asyncpg", ""))
    await conn.execute("DELETE FROM orders WHERE idempotency_key = 'test-idempotent-key-1'")
    await conn.execute("DELETE FROM orders WHERE customer_name = 'Тестовый Покупатель' AND idempotency_key IS NULL")
    await conn.close()

    print("\nAll idempotency checks PASSED")

anyio.run(main)
