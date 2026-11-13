"""Адаптер Telegram (aiogram): команда /start, каталог, оформление заказа.

Бизнес-логика — в base.BotAdapter (CatalogService/OrderService).
aiogram загружается лениво (importlib), чтобы модуль импортировался и
проверялся без установленной библиотеки. Реальный токен владельца —
TODO_OWNER, задаётся в telegram_main.py.
"""

import importlib

from sqlalchemy.ext.asyncio import AsyncSession

from base import BotAdapter


class TelegramBotAdapter(BotAdapter):
    """Telegram-бот на aiogram."""

    def __init__(self, session: AsyncSession, token: str | None = None) -> None:
        super().__init__(session)
        self._token = token

    async def send_message(self, chat_id: str, text: str) -> None:
        """Отправить сообщение через aiogram Bot."""
        aiogram = importlib.import_module("aiogram")
        bot = aiogram.Bot(token=self._token)
        try:
            await bot.send_message(chat_id=chat_id, text=text)
        finally:
            await bot.session.close()
