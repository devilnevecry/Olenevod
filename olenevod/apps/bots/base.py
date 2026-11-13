"""Базовый адаптер бота: команда /start, каталог, оформление заказа.

Бизнес-логика делегируется CatalogService и OrderService (этапы 3-5),
адаптер не дублирует её. Протокол конкретного мессенджера (отправка
сообщения, long-polling) реализуется в привязке: telegram/aiogram, vk, max.
send_message переопределяется в конкретном адаптере.
"""

from collections.abc import Sequence
from typing import Any

from olenevod.application.catalog_service import CatalogService
from olenevod.application.order_service import OrderService
from olenevod.infrastructure.repositories import CatalogRepository
from sqlalchemy.ext.asyncio import AsyncSession


class BotAdapter:
    """Адаптер бота поверх сервисов каталога и заказов.

    session — сессия SQLAlchemy (в тестах — тестовая БД с NullPool).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._catalog = CatalogService(CatalogRepository(session))
        self._orders = OrderService(session)

    async def send_message(self, chat_id: str, text: str) -> None:
        """Отправить текст пользователю. Реализуется привязкой мессенджера."""
        raise NotImplementedError

    async def handle_start(self, chat_id: str) -> str:
        """Команда /start: приветствие и список городов."""
        cities: Sequence[Any] = await self._catalog.list_cities()
        lines = ["Привет! Я помогу оформить заказ.", "Доступные города:"]
        lines.extend(f"- {city.name} ({city.slug})" for city in cities)
        text = "\n".join(lines)
        await self.send_message(chat_id, text)
        return text

    async def handle_catalog(self, chat_id: str, city_slug: str) -> str:
        """Показать начало каталога города (первые 5 позиций)."""
        items, total = await self._catalog.list_products(city_slug, page_size=5)
        if not items:
            text = f"В городе {city_slug} нет доступных товаров."
        else:
            lines = [f"Каталог города {city_slug} ({total} позиций):"]
            for item in items:
                variant = item["variant"]
                offer = item["offer"]
                lines.append(
                    f"{variant.name} ({variant.sku}) — "
                    f"{offer.price_kop} коп., остаток {item['available_qty']}"
                )
            text = "\n".join(lines)
        await self.send_message(chat_id, text)
        return text

    async def handle_order(
        self,
        chat_id: str,
        city_slug: str,
        customer_name: str,
        customer_phone: str,
        items: list[dict[str, Any]],
    ) -> str:
        """Оформить заказ через OrderService (резерв стока + заказ атомарно)."""
        city = await self._catalog.get_city(city_slug)
        order, created = await self._orders.place_order(
            city_id=city.id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            items=items,
        )
        total = sum(item.price for item in created)
        text = (
            f"Заказ оформлен: {order.id}, статус {order.status}, "
            f"итого {total} коп., позиций {len(created)}."
        )
        await self.send_message(chat_id, text)
        return text
