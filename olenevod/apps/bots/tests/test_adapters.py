"""Тесты адаптеров ботов на реальной тестовой PostgreSQL (этап 7).

Заказы создаются через OrderService (базовый адаптер). send_message
переопределен в тестовом адаптере и只是 записывает отправленные тексты —
реальные провайдеры мессенджеров не используются.
"""

import uuid
from typing import Any

import pytest
from conftest import (  # noqa: E402
    CITY_ID,
    CITY_SLUG,
    VARIANT_ID,
    run,
    session_factory,
)
from olenevod.domain.exceptions import NotFound
from olenevod.infrastructure.models import Order, StockLevel, Warehouse
from sqlalchemy import func, select

from base import BotAdapter
from max_adapter import MaxBotAdapter
from telegram_adapter import TelegramBotAdapter
from vk_adapter import VkBotAdapter

ADAPTER_CLASSES = [TelegramBotAdapter, VkBotAdapter, MaxBotAdapter]


class _RecordingAdapter(BotAdapter):
    """Тестовый адаптер: записывает отправленные сообщения вместо реальной отправки."""

    def __init__(self, session: Any) -> None:
        super().__init__(session)
        self.sent: list[tuple[str, str]] = []

    async def send_message(self, chat_id: str, text: str) -> None:
        self.sent.append((chat_id, text))


async def _reserved_for(session: Any, city_id: str, variant_id: str) -> int:
    result = await session.execute(
        select(func.coalesce(func.sum(StockLevel.reserved), 0))
        .join(Warehouse, Warehouse.id == StockLevel.warehouse_id)
        .where(
            Warehouse.city_id == uuid.UUID(city_id),
            StockLevel.variant_id == uuid.UUID(variant_id),
        )
    )
    return int(result.scalar_one())


async def _last_order(session: Any, phone: str) -> Any:
    result = await session.execute(
        select(Order)
        .where(Order.customer_phone == phone)
        .order_by(Order.created_at.desc())
        .limit(1)
    )
    return result.scalars().first()


@pytest.mark.parametrize("base_cls", ADAPTER_CLASSES)
def test_handle_start_lists_cities(base_cls: type[BotAdapter]) -> None:
    async def body() -> None:
        async with session_factory()() as session:
            adapter = _RecordingAdapter(session)
            text = await adapter.handle_start("chat-1")
            assert "Привет" in text
            assert "Ботс-Город" in text
            assert any("Ботс-Город" in sent for _, sent in adapter.sent)

    run(body)


@pytest.mark.parametrize("base_cls", ADAPTER_CLASSES)
def test_handle_catalog_shows_products(base_cls: type[BotAdapter]) -> None:
    async def body() -> None:
        async with session_factory()() as session:
            adapter = _RecordingAdapter(session)
            text = await adapter.handle_catalog("chat-1", CITY_SLUG)
            assert "Вариант для ботов" in text
            assert any("Вариант для ботов" in sent for _, sent in adapter.sent)

    run(body)


@pytest.mark.parametrize("base_cls", ADAPTER_CLASSES)
def test_handle_order_creates_order_and_reserves_stock(base_cls: type[BotAdapter]) -> None:
    async def body() -> None:
        async with session_factory()() as session:
            adapter = _RecordingAdapter(session)
            before = await _reserved_for(session, CITY_ID, VARIANT_ID)
            items = [{"product_variant_id": uuid.UUID(VARIANT_ID), "qty": 3}]
            await adapter.handle_order(
                "chat-1", CITY_SLUG, "Покупатель Ботов", "+79000000001", items
            )
            after = await _reserved_for(session, CITY_ID, VARIANT_ID)
            assert after == before + 3
            assert any("Заказ оформлен" in sent for _, sent in adapter.sent)

            order = await _last_order(session, "+79000000001")
            assert order is not None
            assert order.status == "pending_payment"
            assert order.total_amount == 15000  # 5000 kop * 3

    run(body)


@pytest.mark.parametrize("base_cls", ADAPTER_CLASSES)
def test_handle_order_unknown_city_raises(base_cls: type[BotAdapter]) -> None:
    async def body() -> None:
        async with session_factory()() as session:
            adapter = _RecordingAdapter(session)
            items = [{"product_variant_id": uuid.UUID(VARIANT_ID), "qty": 1}]
            with pytest.raises(NotFound):
                await adapter.handle_order(
                    "chat-1", "nonexistent-city", "Имя", "Телефон", items
                )

    run(body)


@pytest.mark.parametrize("cls", ADAPTER_CLASSES)
def test_adapter_constructs(cls: type[BotAdapter]) -> None:
    async def body() -> None:
        async with session_factory()() as session:
            adapter = cls(session)
            assert isinstance(adapter, BotAdapter)

    run(body)
