"""Фикстуры и хелперы для тестов адаптеров ботов (этап 7).

БД: TEST_DATABASE_URL (postgres:postgres@localhost:5432/olenevod_test).
Схема уже применена alembic (таблицы есть); семяним демо-данные прямыми
INSERT'ами (idem-потентно) через SQLAlchemy. Тесты — sync-функции с
anyio.run (как на этапе 5), каждый тест — свой цикл, сессии не
переплетаются. Моки провайдеров мессенджеров не используются.
"""

import asyncio
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TypeVar

import anyio
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

# Импорты olenevod (API) и bots работают из любого рабочего каталога.
ROOT = Path(__file__).resolve().parents[3]  # C:\...\Olenevod\olenevod
for _path in (str(ROOT / "apps" / "api"), str(ROOT / "apps" / "bots")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/olenevod_test"

CITY_ID = "11111111-1111-1111-1111-111111111010"
CITY_SLUG = "bots-gorod"
CATEGORY_ID = "22222222-2222-2222-2222-222222222010"
PRODUCT_ID = "33333333-3333-3333-3333-333333333010"
VARIANT_ID = "44444444-4444-4444-4444-444444444010"
WAREHOUSE_ID = "55555555-5555-5555-5555-555555555010"
CITY_OFFER_ID = "66666666-6666-6666-6666-666666666010"

SEED_SQL = f"""
INSERT INTO cities (id, slug, name, region, timezone, is_active) VALUES
  ('{CITY_ID}', '{CITY_SLUG}', 'Ботс-Город', 'Тест', 'Europe/Moscow', true)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO categories (id, parent_id, slug, name, is_published, sort) VALUES
  ('{CATEGORY_ID}', NULL, 'bots-category', 'Категория ботов', true, 100)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO products (id, category_id, slug, name, is_published) VALUES
  ('{PRODUCT_ID}', '{CATEGORY_ID}', 'bots-tovar', 'Товар для ботов', true)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO product_variants (id, product_id, sku, name, unit_type) VALUES
  ('{VARIANT_ID}', '{PRODUCT_ID}', 'BOTS-001', 'Вариант для ботов', 'piece')
ON CONFLICT (sku) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO warehouses (id, city_id, name, is_active) VALUES
  ('{WAREHOUSE_ID}', '{CITY_ID}', 'Склад ботов', true)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO stock_levels (warehouse_id, variant_id, on_hand, reserved) VALUES
  ('{WAREHOUSE_ID}', '{VARIANT_ID}', 10, 0)
ON CONFLICT (warehouse_id, variant_id) DO UPDATE SET on_hand = EXCLUDED.on_hand, reserved = EXCLUDED.reserved;

INSERT INTO city_offers (id, city_id, variant_id, price_kop, is_published) VALUES
  ('{CITY_OFFER_ID}', '{CITY_ID}', '{VARIANT_ID}', 5000, true)
ON CONFLICT (city_id, variant_id) DO UPDATE SET price_kop = EXCLUDED.price_kop;
"""

_test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
_test_session_factory = async_sessionmaker(_test_engine, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop_policy() -> asyncio.AbstractEventLoopPolicy:
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture(scope="session", autouse=True)
def _seed_db() -> None:
    """Загрузить демо-данные в тестовую БД (idem-потентно)."""

    async def _seed() -> None:
        async with _test_session_factory() as session:
            for statement in SEED_SQL.split(";"):
                statement = statement.strip()
                if statement:
                    await session.execute(text(statement))
            await session.commit()

    anyio.run(_seed)


T = TypeVar("T")


def run(async_fn: Callable[[], Awaitable[T]]) -> T:  # noqa: UP047
    """Выполнить асинхронную функцию в своём цикле anyio."""
    return anyio.run(async_fn)


def session_factory() -> async_sessionmaker[AsyncSession]:
    return _test_session_factory
