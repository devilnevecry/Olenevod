import asyncio
import os

import anyio
import asyncpg
import pytest
from alembic import command
from alembic.config import Config

pytestmark = pytest.mark.anyio


@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """URL тестовой БД (PostgreSQL). По умолчанию локальная тестовая БД."""
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/olenevod_test",
    )


@pytest.fixture(scope="session")
def alembic_config(test_db_url: str):
    """Alembic-конфигурация с URL тестовой БД."""
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", test_db_url)
    return config


async def _pg_available(url: str) -> bool:
    """Проверка, что PostgreSQL доступен по переданному URL."""
    try:
        conn = await asyncpg.connect(url.replace("+asyncpg", ""))
        await conn.close()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def db_available(test_db_url: str) -> bool:
    """True, если тестовая PostgreSQL-БД доступна."""
    return anyio.run(_pg_available, test_db_url)


@pytest.fixture
def alembic_upgrade_head(alembic_config, db_available):
    """Выполнить `alembic upgrade head` (пропускается, если нет БД)."""

    def runner():
        command.upgrade(alembic_config, "head")

    if not db_available:
        pytest.skip("Тестовая PostgreSQL-БД недоступна (нужен локальный postgres/Docker)")
    runner()
