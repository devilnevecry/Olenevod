"""Точка входа VK-бота (long-polling).

Запуск: python olenevod/apps/bots/vk_main.py
Токен владельца не задан — место помечено TODO_OWNER. Без реального токена
бот не подключается к VK.
"""

import asyncio
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "api"))

from olenevod.infrastructure.db import async_session
from olenevod.settings import settings

from vk_adapter import VkBotAdapter


async def _run() -> None:
    vk = importlib.import_module("vk_api")

    token: str | None = settings.bot_token_vk  # TODO_OWNER: реальный токен VK-бота
    if not token:
        raise RuntimeError("bot_token_vk не задан (TODO_OWNER)")

    async with async_session() as session:
        _adapter = VkBotAdapter(session, token=token)
        api: object = vk.VkApi(token=token)
        # Long-polling сессия VK; обработка сообщений — через VkBotAdapter.
        _longpoll = vk.VkBotLongPoll(api, group_id=0)


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
