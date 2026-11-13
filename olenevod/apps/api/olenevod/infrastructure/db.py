"""Асинхронное подключение к PostgreSQL (SQLAlchemy 2)."""

from collections.abc import Awaitable, Callable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from olenevod.settings import settings

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def check_db() -> tuple[bool, str | None]:
    """Проверка подключения к БД. Возвращает (ok, detail)."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True, None
    except Exception as exc:  # noqa: BLE001 — любая ошибка БД означает неготовность
        return False, f"db unreachable: {exc.__class__.__name__}"


# Псевдотип для удобства типизации проверок компонентов.
type ComponentCheck = Callable[[], Awaitable[tuple[bool, str | None]]]
