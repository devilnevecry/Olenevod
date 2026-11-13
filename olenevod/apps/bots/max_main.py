"""Точка входа MAX-бота (polling).

Запуск: python olenevod/apps/bots/max_main.py
Токен владельца не задан — место помечено TODO_OWNER. Без реального токена
бот не подключается к MAX.
"""

import asyncio
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from olenevod.infrastructure.db import async_session
from olenevod.settings import settings

from max_adapter import MaxBotAdapter


async def _run() -> None:
    max_sdk = importlib.import_module("max")

    token: str | None = settings.bot_token_max  # TODO_OWNER: реальный токен MAX-бота
    if not token:
        raise RuntimeError("bot_token_max не задан (TODO_OWNER)")

    async with async_session() as session:
        _adapter = MaxBotAdapter(session, token=token)
        bot: object = max_sdk.Bot(token=token)
        # Polling-сессия MAX; обработка сообщений — через MaxBotAdapter.
        _poller = max_sdk.Poller(bot)


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
