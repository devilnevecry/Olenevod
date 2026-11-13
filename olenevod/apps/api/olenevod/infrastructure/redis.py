"""Клиент Redis и проверка его готовности."""

from collections.abc import Awaitable, Callable

import redis.asyncio as aioredis

from olenevod.settings import settings

_redis = aioredis.from_url(settings.redis_url, decode_responses=True)


async def check_redis() -> tuple[bool, str | None]:
    """Проверка подключения к Redis. Возвращает (ok, detail)."""
    try:
        await _redis.ping()
        return True, None
    except Exception as exc:  # noqa: BLE001
        return False, f"redis unreachable: {exc.__class__.__name__}"


type ComponentCheck = Callable[[], Awaitable[tuple[bool, str | None]]]
