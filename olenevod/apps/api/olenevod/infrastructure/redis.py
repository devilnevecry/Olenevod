"""ÐšÐ»Ð¸ÐµÐ½Ñ‚ Redis Ð¸ Ð¿Ñ€Ð¾Ð²ÐµÑ€ÐºÐ° ÐµÐ³Ð¾ Ð³Ð¾Ñ‚Ð¾Ð²Ð½Ð¾ÑÑ‚Ð¸."""

from collections.abc import Awaitable, Callable

import redis.asyncio as aioredis

from olenevod.settings import settings

_redis = aioredis.from_url(settings.redis_url, decode_responses=True)  # type: ignore[no-untyped-call]


async def check_redis() -> tuple[bool, str | None]:
    """ÐŸÑ€Ð¾Ð²ÐµÑ€ÐºÐ° Ð¿Ð¾Ð´ÐºÐ»ÑŽÑ‡ÐµÐ½Ð¸Ñ Ðº Redis. Ð’Ð¾Ð·Ð²Ñ€Ð°Ñ‰Ð°ÐµÑ‚ (ok, detail)."""
    try:
        await _redis.ping()
        return True, None
    except Exception as exc:  # noqa: BLE001
        return False, f"redis unreachable: {exc.__class__.__name__}"


type ComponentCheck = Callable[[], Awaitable[tuple[bool, str | None]]]

