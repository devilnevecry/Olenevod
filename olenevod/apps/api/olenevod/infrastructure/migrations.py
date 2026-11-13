"""Проверка применённых Alembic-миграций."""

from collections.abc import Awaitable, Callable

from sqlalchemy import text

from olenevod.infrastructure.db import engine

type ComponentCheck = Callable[[], Awaitable[tuple[bool, str | None]]]


async def check_migrations() -> tuple[bool, str | None]:
    """Проверка, что таблица alembic_version существует и содержит версию.

    На этапе каркаса миграций ещё нет; проверка возвращает ошибку, пока
    `make migrate` не применён. В production это гарантирует, что схема
    актуальна перед приёмом трафика.
    """
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
            row = result.fetchone()
            if row is None or not row[0]:
                return False, "alembic_version is empty"
            return True, row[0]
    except Exception as exc:  # noqa: BLE001
        return False, f"migrations not applied: {exc.__class__.__name__}"
