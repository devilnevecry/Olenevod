"""Тесты InventoryService (этап 8) на реальной тестовой PostgreSQL.

БД: TEST_DATABASE_URL (postgres:postgres@localhost:5432/olenevod_test).
Сервис вызывается напрямую с тестовой сессией (NullPool); данные сидятся
прямыми INSERT'ами — моки не используются. Каждый тест — sync-функция с
anyio.run, сессия SQLAlchemy коммитится в тесте после операции сервиса.
"""

import uuid

import anyio
import asyncpg
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from olenevod.application.inventory_service import InventoryService

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/olenevod_test"

INV_CITY_MSK = uuid.UUID("11111111-1111-1111-1111-111111111011")
INV_CITY_SPB = uuid.UUID("11111111-1111-1111-1111-111111111012")
INV_VARIANT_ID = uuid.UUID("44444444-4444-4444-4444-444444444011")
INV_WH_MSK = uuid.UUID("55555555-5555-5555-5555-555555555011")
INV_WH_SPB = uuid.UUID("55555555-5555-5555-5555-555555555012")

_test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
_test_session_factory = async_sessionmaker(_test_engine, expire_on_commit=False)

SEED_SQL = """
INSERT INTO cities (id, slug, name, region, timezone, is_active) VALUES
  ('11111111-1111-1111-1111-111111111011', 'inv-moscow', 'Москва инв', 'Москва', 'Europe/Moscow', true),
  ('11111111-1111-1111-1111-111111111012', 'inv-spb', 'Петербург инв', 'СПб', 'Europe/Moscow', true)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO categories (id, parent_id, slug, name, is_published, sort) VALUES
  ('22222222-2222-2222-2222-222222222011', NULL, 'inv-test', 'Тест инв', true, 100)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO products (id, category_id, slug, name, is_published) VALUES
  ('33333333-3333-3333-3333-333333333011', '22222222-2222-2222-2222-222222222011', 'inv-produkt', 'Продукт инв', true)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO product_variants (id, product_id, sku, name, unit_type) VALUES
  ('44444444-4444-4444-4444-444444444011', '33333333-3333-3333-3333-333333333011', 'INV-001', 'Вариант инв', 'piece')
ON CONFLICT (sku) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO city_offers (id, city_id, variant_id, price_kop, is_published) VALUES
  ('66666666-6666-6666-6666-666666666011', '11111111-1111-1111-1111-111111111011', '44444444-4444-4444-4444-444444444011', 9500, true),
  ('66666666-6666-6666-6666-666666666012', '11111111-1111-1111-1111-111111111012', '44444444-4444-4444-4444-444444444011', 9500, true)
ON CONFLICT (city_id, variant_id) DO UPDATE SET price_kop = EXCLUDED.price_kop;

INSERT INTO warehouses (id, city_id, name, is_active) VALUES
  ('55555555-5555-5555-5555-555555555011', '11111111-1111-1111-1111-111111111011', 'Склад Москва инв', true),
  ('55555555-5555-5555-5555-555555555012', '11111111-1111-1111-1111-111111111012', 'Склад СПб инв', true)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO stock_levels (warehouse_id, variant_id, on_hand, reserved) VALUES
  ('55555555-5555-5555-5555-555555555011', '44444444-4444-4444-4444-444444444011', 10, 0),
  ('55555555-5555-5555-5555-555555555012', '44444444-4444-4444-4444-444444444011', 5, 0)
ON CONFLICT (warehouse_id, variant_id) DO UPDATE SET on_hand = EXCLUDED.on_hand, reserved = EXCLUDED.reserved;
"""


async def _load_seed() -> None:
    conn = await asyncpg.connect(TEST_DATABASE_URL.replace("+asyncpg", ""))
    try:
        await conn.execute(SEED_SQL)
    finally:
        await conn.close()


async def _pg_fetchrow(sql: str, *args):
    conn = await asyncpg.connect(TEST_DATABASE_URL.replace("+asyncpg", ""))
    try:
        return await conn.fetchrow(sql, *args)
    finally:
        await conn.close()


async def _pg_execute(sql: str, *args) -> None:
    conn = await asyncpg.connect(TEST_DATABASE_URL.replace("+asyncpg", ""))
    try:
        await conn.execute(sql, *args)
    finally:
        await conn.close()


async def _available(warehouse_id: uuid.UUID, variant_id: uuid.UUID) -> int:
    row = await _pg_fetchrow(
        "SELECT on_hand - reserved FROM stock_levels WHERE warehouse_id = $1 AND variant_id = $2",
        warehouse_id,
        variant_id,
    )
    return int(row[0])


async def _on_hand(warehouse_id: uuid.UUID, variant_id: uuid.UUID) -> int:
    row = await _pg_fetchrow(
        "SELECT on_hand FROM stock_levels WHERE warehouse_id = $1 AND variant_id = $2",
        warehouse_id,
        variant_id,
    )
    return int(row[0])


async def _reserved_in_city(city_id: uuid.UUID, variant_id: uuid.UUID) -> int:
    row = await _pg_fetchrow(
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


async def _outbox_count(aggregate_type: str, event_type: str) -> int:
    row = await _pg_fetchrow(
        """
        SELECT count(*) FROM outbox
        WHERE aggregate_type = $1 AND event_type = $2
        """,
        aggregate_type,
        event_type,
    )
    return int(row[0])


async def _count_reservations_by_key(key: str) -> int:
    row = await _pg_fetchrow(
        "SELECT count(*) FROM inventory_reservations WHERE idempotency_key = $1",
        key,
    )
    return int(row[0])


async def _reset_spb() -> None:
    """Сбросить состояние СПб перед проверкой сверки (изоляция от других тестов)."""
    await _pg_execute("DELETE FROM inventory_reservations WHERE city_id = $1", INV_CITY_SPB)
    await _pg_execute(
        "UPDATE stock_levels SET reserved = 0 WHERE warehouse_id = $1 AND variant_id = $2",
        INV_WH_SPB,
        INV_VARIANT_ID,
    )


async def _do(fn):
    """Выполнить fn(service, session) в тестовой сессии и закоммитить."""
    async with _test_session_factory() as session:
        service = InventoryService(session)
        result = await fn(service, session)
        await session.commit()
        return result


@pytest.fixture(autouse=True)
def _seed_db(alembic_config: Config, db_available: bool) -> None:
    """Применить миграции и загрузить демо-данные в тестовую БД."""

    def runner() -> None:
        command.upgrade(alembic_config, "head")

    if not db_available:
        pytest.skip("Тестовая PostgreSQL-БД недоступна (нужен локальный postgres/Docker)")
    runner()
    anyio.run(_load_seed)


def _items(variant_id: uuid.UUID, city_id: uuid.UUID, qty: int) -> list[dict]:
    return [{"variant_id": variant_id, "city_id": city_id, "qty": qty}]


def test_reserve_reduces_available() -> None:
    before = anyio.run(_available, INV_WH_MSK, INV_VARIANT_ID)
    reservations = anyio.run(
        _do, lambda s, _: s.reserve(uuid.uuid4(), _items(INV_VARIANT_ID, INV_CITY_MSK, 3))
    )

    assert len(reservations) == 1
    assert reservations[0].status == "active"
    assert reservations[0].qty == 3
    assert reservations[0].city_id == INV_CITY_MSK
    assert reservations[0].expires_at is not None

    after = anyio.run(_available, INV_WH_MSK, INV_VARIANT_ID)
    assert after == before - 3

    assert anyio.run(_outbox_count, "inventory_reservation", "reserved") >= 1


def test_commit_fixes_stock() -> None:
    reservations = anyio.run(
        _do, lambda s, _: s.reserve(uuid.uuid4(), _items(INV_VARIANT_ID, INV_CITY_MSK, 3))
    )
    reservation_id = reservations[0].id

    before_on_hand = anyio.run(_on_hand, INV_WH_MSK, INV_VARIANT_ID)
    before_reserved = anyio.run(_reserved_in_city, INV_CITY_MSK, INV_VARIANT_ID)

    updated = anyio.run(_do, lambda s, _: s.commit(reservation_id))
    assert updated is not None
    assert updated.status == "committed"

    assert anyio.run(_on_hand, INV_WH_MSK, INV_VARIANT_ID) == before_on_hand - 3
    assert anyio.run(_reserved_in_city, INV_CITY_MSK, INV_VARIANT_ID) == before_reserved - 3


def test_release_returns_stock() -> None:
    reservations = anyio.run(
        _do, lambda s, _: s.reserve(uuid.uuid4(), _items(INV_VARIANT_ID, INV_CITY_MSK, 3))
    )
    reservation_id = reservations[0].id

    before_reserved = anyio.run(_reserved_in_city, INV_CITY_MSK, INV_VARIANT_ID)
    before_available = anyio.run(_available, INV_WH_MSK, INV_VARIANT_ID)

    updated = anyio.run(_do, lambda s, _: s.release(reservation_id))
    assert updated is not None
    assert updated.status == "released"

    assert anyio.run(_reserved_in_city, INV_CITY_MSK, INV_VARIANT_ID) == before_reserved - 3
    assert anyio.run(_available, INV_WH_MSK, INV_VARIANT_ID) == before_available + 3


def test_return_increases_stock() -> None:
    before_on_hand = anyio.run(_on_hand, INV_WH_MSK, INV_VARIANT_ID)

    anyio.run(
        _do, lambda s, _: s.return_items(_items(INV_VARIANT_ID, INV_CITY_MSK, 4))
    )
    assert anyio.run(_on_hand, INV_WH_MSK, INV_VARIANT_ID) == before_on_hand + 4


def test_transfer_moves_between_cities() -> None:
    before_msk = anyio.run(_on_hand, INV_WH_MSK, INV_VARIANT_ID)
    before_spb = anyio.run(_on_hand, INV_WH_SPB, INV_VARIANT_ID)

    anyio.run(
        _do,
        lambda s, _: s.transfer(
            INV_CITY_MSK, INV_CITY_SPB, [{"variant_id": INV_VARIANT_ID, "qty": 3}]
        ),
    )
    assert anyio.run(_on_hand, INV_WH_MSK, INV_VARIANT_ID) == before_msk - 3
    assert anyio.run(_on_hand, INV_WH_SPB, INV_VARIANT_ID) == before_spb + 3


def test_expire_reservations_marks_expired_and_returns_stock() -> None:
    order_id = uuid.uuid4()
    reservation_id = uuid.uuid4()
    anyio.run(
        _pg_execute,
        """
        INSERT INTO inventory_reservations (id, order_id, warehouse_id, variant_id, city_id, qty, status, expires_at, created_at)
        VALUES ($1, $2, $3, $4, $5, 3, 'active', '2020-01-01 00:00:00+00', now())
        """,
        reservation_id,
        order_id,
        INV_WH_MSK,
        INV_VARIANT_ID,
        INV_CITY_MSK,
    )
    anyio.run(
        _pg_execute,
        "UPDATE stock_levels SET reserved = reserved + 3 WHERE warehouse_id = $1 AND variant_id = $2",
        INV_WH_MSK,
        INV_VARIANT_ID,
    )

    before_reserved = anyio.run(_reserved_in_city, INV_CITY_MSK, INV_VARIANT_ID)
    expired = anyio.run(_do, lambda s, _: s.expire_reservations())

    assert len(expired) == 1
    assert expired[0].status == "expired"
    assert anyio.run(_reserved_in_city, INV_CITY_MSK, INV_VARIANT_ID) == before_reserved - 3


def test_idempotency_key_returns_existing_reservations() -> None:
    order_id = uuid.uuid4()
    key = "inv-idempotency-key-1"
    first = anyio.run(
        _do,
        lambda s, _: s.reserve(
            order_id, _items(INV_VARIANT_ID, INV_CITY_MSK, 2), idempotency_key=key
        ),
    )
    first_ids = {r.id for r in first}

    second = anyio.run(
        _do,
        lambda s, _: s.reserve(
            order_id, _items(INV_VARIANT_ID, INV_CITY_MSK, 2), idempotency_key=key
        ),
    )
    second_ids = {r.id for r in second}

    assert first_ids == second_ids
    assert len(first) == len(second) == 1
    assert anyio.run(_count_reservations_by_key, key) == 1


def test_reconcile_no_discrepancies_then_discrepancy() -> None:
    anyio.run(_reset_spb)

    def spb_diffs(diffs: list[dict]) -> list[dict]:
        return [d for d in diffs if d["city_id"] == INV_CITY_SPB]

    assert spb_diffs(anyio.run(_do, lambda s, _: s.reconcile())) == []

    anyio.run(
        _do,
        lambda s, _: s.reserve(uuid.uuid4(), _items(INV_VARIANT_ID, INV_CITY_SPB, 3)),
    )
    assert spb_diffs(anyio.run(_do, lambda s, _: s.reconcile())) == []

    anyio.run(
        _pg_execute,
        "UPDATE stock_levels SET reserved = reserved + 7, on_hand = on_hand + 7 WHERE warehouse_id = $1 AND variant_id = $2",
        INV_WH_SPB,
        INV_VARIANT_ID,
    )

    diffs = spb_diffs(anyio.run(_do, lambda s, _: s.reconcile()))
    assert len(diffs) == 1
    assert diffs[0]["city_id"] == INV_CITY_SPB
    assert diffs[0]["variant_id"] == INV_VARIANT_ID
    assert diffs[0]["difference"] == 7
