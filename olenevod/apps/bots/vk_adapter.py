"""Адаптер VK: команда /start, каталог, оформление заказа.

Бизнес-логика — в base.BotAdapter (CatalogService/OrderService).
vk_api загружается лениво (importlib), чтобы модуль импортировался и
проверялся без установленной библиотеки. Реальный токен владельца —
TODO_OWNER, задаётся в vk_main.py.
"""

import importlib

from sqlalchemy.ext.asyncio import AsyncSession

from base import BotAdapter


class VkBotAdapter(BotAdapter):
    """VK-бот."""

    def __init__(self, session: AsyncSession, token: str | None = None) -> None:
        super().__init__(session)
        self._token = token

    async def send_message(self, chat_id: str, text: str) -> None:
        """Отправить сообщение через VK API."""
        vk = importlib.import_module("vk_api")
        api = vk.VkApi(token=self._token)
        try:
            await api.method(
                "messages.send",
                {"peer_id": int(chat_id), "message": text, "random_id": 0},
            )
        finally:
            session = getattr(api, "http", None)
            if session is not None:
                await session.close()
