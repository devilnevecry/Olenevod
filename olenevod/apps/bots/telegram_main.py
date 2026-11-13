"""Точка входа Telegram-бота (aiogram polling).

Запуск: python olenevod/apps/bots/telegram_main.py
Токен владельца не задан — место помечено TODO_OWNER. Без реального токена
бот не подключается к Telegram.
"""

import asyncio
import importlib
import sys
from pathlib import Path
from typing import Any

# Каталог API-приложения, чтобы пакет olenevod был импортируем.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from olenevod.infrastructure.db import async_session
from olenevod.settings import settings

from telegram_adapter import TelegramBotAdapter


async def _run() -> None:
    aiogram = importlib.import_module("aiogram")

    token: str | None = settings.bot_token_telegram  # TODO_OWNER: реальный токен Telegram-бота
    if not token:
        raise RuntimeError("bot_token_telegram не задан (TODO_OWNER)")

    async with async_session() as session:
        adapter = TelegramBotAdapter(session, token=token)
        dispatcher: Any = aiogram.Dispatcher()

        async def on_start(message: Any) -> None:
            await adapter.handle_start(str(message.chat.id))

        dispatcher.message.register(
            on_start,
            aiogram.filters.Command("start"),
        )

        bot: Any = aiogram.Bot(token=token)
        try:
            await dispatcher.start_polling(bot)
        finally:
            await bot.session.close()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
