"""Репозиторий остатков (атомарное резервирование, списание, освобождение, перемещение)."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from olenevod.domain.exceptions import OutOfStock
from olenevod.infrastructure.models import Reservation, StockLevel


class InventoryRepository:
    """Запись и чтение остатков. Остатки никогда не изменяются read-modify-write в приложении."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_levels(
        self, warehouse_id: uuid.UUID, variant_ids: list[uuid.UUID]
    ) -> list[StockLevel]:
        """Текущие уровни остатков для вариантов на складе."""
        result = await self._session.execute(
            select(StockLevel).where(
                StockLevel.warehouse_id == warehouse_id,
                StockLevel.variant_id.in_(variant_ids),
            )
        )
        return list(result.scalars().all())

    async def reserve(
        self, warehouse_id: uuid.UUID, variant_id: uuid.UUID, qty: int
    ) -> tuple[int, int]:
        """Атомарный резерв: reserved += qty, если on_hand - reserved >= qty.

        Возвращает (on_hand, reserved) или выбрасывает OutOfStock при недостатке.
        """
        result = await self._session.execute(
            update(StockLevel)
            .where(
                StockLevel.warehouse_id == warehouse_id,
                StockLevel.variant_id == variant_id,
                StockLevel.on_hand - StockLevel.reserved >= qty,
            )
            .values(reserved=StockLevel.reserved + qty)
            .returning(StockLevel.on_hand, StockLevel.reserved)
        )
        row = result.first()
        if row is None:
            raise OutOfStock(str(variant_id), available=0, requested=qty)
        return int(row[0]), int(row[1])

    async def release(
        self, warehouse_id: uuid.UUID, variant_id: uuid.UUID, qty: int
    ) -> None:
        """Освободить резерв (reserved -= qty)."""
        await self._session.execute(
            update(StockLevel)
            .where(
                StockLevel.warehouse_id == warehouse_id,
                StockLevel.variant_id == variant_id,
                StockLevel.reserved >= qty,
            )
            .values(reserved=StockLevel.reserved - qty)
        )

    async def commit(
        self, warehouse_id: uuid.UUID, variant_id: uuid.UUID, qty: int
    ) -> None:
        """Списать с остатка: on_hand -= qty, reserved -= qty (отгрузка)."""
        await self._session.execute(
            update(StockLevel)
            .where(
                StockLevel.warehouse_id == warehouse_id,
                StockLevel.variant_id == variant_id,
                StockLevel.on_hand >= qty,
                StockLevel.reserved >= qty,
            )
            .values(on_hand=StockLevel.on_hand - qty, reserved=StockLevel.reserved - qty)
        )

    async def create_reservation(
        self,
        order_id: uuid.UUID,
        warehouse_id: uuid.UUID,
        variant_id: uuid.UUID,
        qty: int,
        expires_at: datetime | None = None,
    ) -> Reservation:
        """Создать запись резерва."""
        reservation = Reservation(
            order_id=order_id,
            warehouse_id=warehouse_id,
            variant_id=variant_id,
            qty=qty,
            status="active",
            expires_at=expires_at,
        )
        self._session.add(reservation)
        await self._session.flush()
        return reservation

    async def record_movement(
        self, sql: str, parameters: dict[str, Any] | None = None
    ) -> None:
        """Записать движение остатка (вызывается сервисом в рамках транзакции)."""
        await self._session.execute(text(sql), parameters or {})
