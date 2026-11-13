"""Сервис корзины покупателя: добавить/удалить/посмотреть позиции.

Ключ корзины — session_id (гость) или user_id (авторизованный покупатель).
Хранение — в памяти (на다음 этап — Redis). Проверка наличия — по остаткам
stock_levels выбранного города.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from olenevod.infrastructure.models import StockLevel, Warehouse


@dataclass(frozen=True)
class CartLine:
    product_variant_id: uuid.UUID
    qty: int


class CartService:
    """Корзина покупателя в памяти.

    Ключ корзины — session_id (гость) или user_id (авторизованный).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._carts: dict[str, list[CartLine]] = {}

    def _cart_key(
        self,
        *,
        session_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
    ) -> str:
        if user_id is not None:
            return f"user:{user_id}"
        if session_id is not None:
            return f"session:{session_id}"
        raise ValueError("session_id or user_id is required")

    def add(
        self,
        *,
        session_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        product_variant_id: uuid.UUID,
        qty: int,
    ) -> list[CartLine]:
        """Добавить позицию в корзину (или увеличить количество существующей)."""
        if qty < 1:
            raise ValueError("qty must be >= 1")
        key = self._cart_key(session_id=session_id, user_id=user_id)
        lines = self._carts.setdefault(key, [])
        for index, line in enumerate(lines):
            if line.product_variant_id == product_variant_id:
                lines[index] = CartLine(product_variant_id, line.qty + qty)
                return list(lines)
        lines.append(CartLine(product_variant_id, qty))
        return list(lines)

    def remove(
        self,
        *,
        session_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        product_variant_id: uuid.UUID,
    ) -> None:
        """Удалить позицию из корзины."""
        key = self._cart_key(session_id=session_id, user_id=user_id)
        lines = self._carts.get(key, [])
        self._carts[key] = [
            line for line in lines if line.product_variant_id != product_variant_id
        ]

    def view(
        self,
        *,
        session_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
    ) -> list[CartLine]:
        """Вернуть позиции корзины."""
        key = self._cart_key(session_id=session_id, user_id=user_id)
        return list(self._carts.get(key, []))

    async def check_availability(
        self, city_id: uuid.UUID, product_variant_id: uuid.UUID, qty: int
    ) -> bool:
        """Проверка наличия варианта на складах города (доступно = on_hand - reserved)."""
        result = await self._session.execute(
            select(func.coalesce(func.sum(StockLevel.on_hand - StockLevel.reserved), 0))
            .join(Warehouse, Warehouse.id == StockLevel.warehouse_id)
            .where(
                Warehouse.city_id == city_id,
                StockLevel.variant_id == product_variant_id,
            )
        )
        available = int(result.scalar_one())
        return available >= qty
