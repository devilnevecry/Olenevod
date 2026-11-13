"""Асинхронное подключение к PostgreSQL (SQLAlchemy 2)."""

import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped

from olenevod.settings import settings

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)

async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Декларативная база всех ORM-моделей (метаданные для Alembic)."""

    pass


type IdPk = Mapped[uuid.UUID]
type Ts = Mapped[datetime]
type JsonDict = dict[str, Any]


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
