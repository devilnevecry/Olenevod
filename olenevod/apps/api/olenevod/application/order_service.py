"""Сервис заказов: оформление заказа с атомарным резервом стока и смена статуса.

OrderRepository — запись и чтение заказов/позиций.
OrderService — оформление заказа: резерв стока через InventoryRepository,
расчёт итога через PricingService, создание заказа + order_items в одной транзакции.
"""

import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from olenevod.application.pricing_service import PricingService
from olenevod.domain.exceptions import NotFound, OutOfStock
from olenevod.infrastructure.models import (
    City,
    Order,
    OrderItem,
    StockLevel,
    Warehouse,
)
from olenevod.infrastructure.repositories import CatalogRepository, InventoryRepository


class OrderRepository:
    """Чтение и запись заказов и их позиций."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, order_id: uuid.UUID) -> Order | None:
        """Заказ по идентификатору или None."""
        return await self._session.get(Order, order_id)

    async def get_by_idempotency_key(self, key: str) -> Order | None:
        """Заказ по ключу идемпотентности или None."""
        result = await self._session.execute(
            select(Order).where(Order.idempotency_key == key)
        )
        return result.scalar_one_or_none()

    async def list_items(self, order_id: uuid.UUID) -> Sequence[OrderItem]:
        """Позиции заказа."""
        result = await self._session.execute(
            select(OrderItem).where(OrderItem.order_id == order_id).order_by(OrderItem.id)
        )
        return list(result.scalars().all())

    async def create_order(
        self,
        city_id: uuid.UUID,
        customer_name: str,
        customer_phone: str,
        total_amount: int,
        idempotency_key: str | None = None,
    ) -> Order:
        """Создать заказ в статусе pending_payment и flushed (id доступен)."""
        order = Order(
            city_id=city_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            status="pending_payment",
            total_amount=total_amount,
            idempotency_key=idempotency_key,
        )
        self._session.add(order)
        await self._session.flush()
        return order

    async def add_item(
        self,
        order_id: uuid.UUID,
        product_variant_id: uuid.UUID,
        qty: int,
        price: int,
    ) -> OrderItem:
        """Добавить позицию заказа."""
        item = OrderItem(
            order_id=order_id,
            product_variant_id=product_variant_id,
            qty=qty,
            price=price,
        )
        self._session.add(item)
        await self._session.flush()
        return item

    async def change_status(self, order_id: uuid.UUID, status: str) -> Order | None:
        """Сменить статус заказа. None, если заказ не найден."""
        order = await self.get(order_id)
        if order is None:
            return None
        order.status = status
        await self._session.flush()
        return order


class OrderService:
    """Оформление заказа. Весь сквозной процесс — в одной транзакции."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._orders = OrderRepository(session)
        self._inventory = InventoryRepository(session)
        self._pricing = PricingService(CatalogRepository(session))

    async def place_order(
        self,
        city_id: uuid.UUID,
        customer_name: str,
        customer_phone: str,
        items: list[dict[str, Any]],
        idempotency_key: str | None = None,
    ) -> tuple[Order, list[OrderItem]]:
        """Оформить заказ: резерв стока + создание заказа и позиций атомарно.

        items — список {product_variant_id, qty}.
        idempotency_key — при повторном запросе с тем же ключом возвращается
        существующий заказ без повторного резерва стока.
        """
        if not items:
            raise ValueError("order must contain at least one item")

        # Идемпотентность: если заказ с таким ключом уже существует, вернуть его.
        if idempotency_key is not None:
            existing = await self._orders.get_by_idempotency_key(idempotency_key)
            if existing is not None:
                existing_items = await self._orders.list_items(existing.id)
                return existing, list(existing_items)

        pricing_items = [
            {"variant_id": item["product_variant_id"], "qty": item["qty"]} for item in items
        ]
        pricing = await self._pricing.calculate_total(city_id, pricing_items)
        total_kop = int(pricing["total_kop"])
        unit_prices: dict[uuid.UUID, int] = {
            line["variant_id"]: int(line["unit_price_kop"]) for line in pricing["lines"]
        }

        city = await self._session.get(City, city_id)
        if city is None:
            raise NotFound("city", str(city_id))

        # Атомарный резерв стока для каждой позиции (UPDATE ... WHERE ... RETURNING).
        for item in items:
            variant_id = item["product_variant_id"]
            qty = int(item["qty"])
            warehouse_id = await self._select_warehouse(city_id, variant_id, qty)
            await self._inventory.reserve(warehouse_id, variant_id, qty)

        order = await self._orders.create_order(
            city_id, customer_name, customer_phone, total_kop, idempotency_key
        )
        created_items: list[OrderItem] = []
        for item in items:
            variant_id = item["product_variant_id"]
            qty = int(item["qty"])
            created_items.append(
                await self._orders.add_item(
                    order.id, variant_id, qty, unit_prices[variant_id]
                )
            )
        # Все изменения (резерв + заказ + позиции) коммитится одной транзакцией.
        await self._session.commit()
        return order, created_items

    async def get_order(self, order_id: uuid.UUID) -> tuple[Order, Sequence[OrderItem]] | None:
        """Заказ с позициями или None."""
        order = await self._orders.get(order_id)
        if order is None:
            return None
        items = await self._orders.list_items(order_id)
        return order, items

    async def _select_warehouse(
        self, city_id: uuid.UUID, variant_id: uuid.UUID, qty: int
    ) -> uuid.UUID:
        """Склад города с наибольшим доступным остатком варианта, закрывающий qty."""
        result = await self._session.execute(
            select(
                Warehouse.id,
                StockLevel.on_hand,
                StockLevel.reserved,
            )
            .join(StockLevel, StockLevel.warehouse_id == Warehouse.id)
            .where(Warehouse.city_id == city_id, StockLevel.variant_id == variant_id)
            .order_by((StockLevel.on_hand - StockLevel.reserved).desc())
        )
        for row in result.all():
            wh_id: uuid.UUID = row[0]
            on_hand: int = row[1]
            reserved: int = row[2]
            if on_hand - reserved >= qty:
                return wh_id
        raise OutOfStock(str(variant_id), available=0, requested=qty)
