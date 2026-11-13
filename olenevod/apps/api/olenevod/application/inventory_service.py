"""Сервис остатков: резерв, подтверждение, освобождение, возврат, перемещение, истечение, сверка.

Все изменения остатков выполняются через ``InventoryRepository`` (атомарные
``UPDATE ... WHERE``). Сервис не делает read-modify-write в приложении.
События изменения остатков пишутся в outbox в той же транзакции.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from olenevod.domain.exceptions import InvalidTransition, NotFound, OutOfStock
from olenevod.infrastructure.models import (
    City,
    InventoryReservation,
    Outbox,
    StockLevel,
    Warehouse,
)
from olenevod.infrastructure.repositories import InventoryRepository


class InventoryService:
    """Управление остатками товара по городам/складам."""

    RESERVATION_TTL_MINUTES = 30

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._inventory = InventoryRepository(session)

    # ---------- резерв ----------

    async def reserve(
        self,
        order_id: uuid.UUID,
        items: list[dict[str, Any]],
        *,
        idempotency_key: str | None = None,
        ttl_minutes: int | None = None,
    ) -> list[InventoryReservation]:
        """Зарезервировать остаток под заказ.

        items — список ``{variant_id, city_id, qty}``.
        ``idempotency_key`` — при повторном вызове с тем же ключом возвращаются
        уже созданные резервы (проверка выполняется перед выполнением).
        """
        if idempotency_key is not None:
            existing = await self._find_by_idempotency_key(idempotency_key)
            if existing is not None:
                return existing

        expires_at = self._expires_at(ttl_minutes)

        reservations: list[InventoryReservation] = []
        for item in items:
            variant_id = self._as_uuid(item["variant_id"])
            city_id = self._as_uuid(item["city_id"])
            qty = int(item["qty"])
            if qty <= 0:
                raise ValueError(f"qty must be positive, got {qty}")

            city = await self._session.get(City, city_id)
            if city is None:
                raise NotFound("city", str(city_id))

            warehouse_id = await self._select_warehouse(city_id, variant_id, qty)
            await self._inventory.reserve(warehouse_id, variant_id, qty)

            reservation = InventoryReservation(
                order_id=order_id,
                warehouse_id=warehouse_id,
                variant_id=variant_id,
                city_id=city_id,
                qty=qty,
                status="active",
                expires_at=expires_at,
                idempotency_key=idempotency_key,
            )
            self._session.add(reservation)
            await self._session.flush()
            reservations.append(reservation)

            await self._emit_outbox(
                "inventory_reservation",
                reservation.id,
                "reserved",
                {
                    "order_id": str(order_id),
                    "variant_id": str(variant_id),
                    "city_id": str(city_id),
                    "warehouse_id": str(warehouse_id),
                    "qty": qty,
                },
            )

        return reservations

    async def _find_by_idempotency_key(
        self, key: str
    ) -> list[InventoryReservation] | None:
        result = await self._session.execute(
            select(InventoryReservation)
            .where(InventoryReservation.idempotency_key == key)
            .order_by(InventoryReservation.created_at)
        )
        rows = list(result.scalars().all())
        return rows or None

    async def _select_warehouse(
        self, city_id: uuid.UUID, variant_id: uuid.UUID, qty: int
    ) -> uuid.UUID:
        """Склад города с наибольшим доступным остатком варианта, закрывающий qty."""
        result = await self._session.execute(
            select(Warehouse.id, StockLevel.on_hand, StockLevel.reserved)
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

    @staticmethod
    def _expires_at(ttl_minutes: int | None) -> datetime | None:
        if not ttl_minutes:
            ttl_minutes = InventoryService.RESERVATION_TTL_MINUTES
        return datetime.now(UTC) + timedelta(minutes=ttl_minutes)

    @staticmethod
    def _as_uuid(value: Any) -> uuid.UUID:
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))

    # ---------- подтверждение / освобождение ----------

    async def commit(self, reservation_id: uuid.UUID) -> InventoryReservation | None:
        """Подтвердить резерв: списать со склада (on_hand -= qty, reserved -= qty).

        Возвращает резервацию или None, если не найдена.
        """
        reservation = await self._session.get(InventoryReservation, reservation_id)
        if reservation is None:
            return None
        if reservation.status != "active":
            raise InvalidTransition(
                "inventory_reservation", reservation.status, "committed"
            )

        await self._inventory.commit(
            reservation.warehouse_id, reservation.variant_id, reservation.qty
        )
        reservation.status = "committed"
        await self._session.flush()

        await self._emit_outbox(
            "inventory_reservation",
            reservation.id,
            "committed",
            {
                "order_id": str(reservation.order_id),
                "variant_id": str(reservation.variant_id),
                "city_id": str(reservation.city_id),
                "warehouse_id": str(reservation.warehouse_id),
                "qty": reservation.qty,
            },
        )
        return reservation

    async def release(self, reservation_id: uuid.UUID) -> InventoryReservation | None:
        """Освободить резерв (reserved -= qty, статус released)."""
        reservation = await self._session.get(InventoryReservation, reservation_id)
        if reservation is None:
            return None
        if reservation.status != "active":
            raise InvalidTransition(
                "inventory_reservation", reservation.status, "released"
            )

        await self._inventory.release(
            reservation.warehouse_id, reservation.variant_id, reservation.qty
        )
        reservation.status = "released"
        await self._session.flush()

        await self._emit_outbox(
            "inventory_reservation",
            reservation.id,
            "released",
            {
                "order_id": str(reservation.order_id),
                "variant_id": str(reservation.variant_id),
                "city_id": str(reservation.city_id),
                "warehouse_id": str(reservation.warehouse_id),
                "qty": reservation.qty,
            },
        )
        return reservation

    # ---------- возврат на склад ----------

    async def return_items(
        self, items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Вернуть товар на склад (on_hand += qty).

        items — список ``{variant_id, city_id, qty}``. Возвращает обработанные
        позиции с warehouse_id.
        """
        processed: list[dict[str, Any]] = []
        for item in items:
            variant_id = self._as_uuid(item["variant_id"])
            city_id = self._as_uuid(item["city_id"])
            qty = int(item["qty"])
            if qty <= 0:
                raise ValueError(f"qty must be positive, got {qty}")

            city = await self._session.get(City, city_id)
            if city is None:
                raise NotFound("city", str(city_id))

            warehouse_id = await self._select_any_warehouse(city_id, variant_id)
            await self._receive(warehouse_id, variant_id, qty)

            await self._emit_outbox(
                "stock_level",
                warehouse_id,
                "returned",
                {
                    "variant_id": str(variant_id),
                    "city_id": str(city_id),
                    "warehouse_id": str(warehouse_id),
                    "qty": qty,
                },
            )
            processed.append(
                {
                    "variant_id": variant_id,
                    "city_id": city_id,
                    "warehouse_id": warehouse_id,
                    "qty": qty,
                }
            )
        return processed

    # ---------- перемещение между городами ----------

    async def transfer(
        self, from_city: uuid.UUID, to_city: uuid.UUID, items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Переместить товар между городами.

        items — список ``{variant_id, qty}``. Снимает остаток в from_city и
        пополняет в to_city. Возвращает обработанные позиции.
        """
        processed: list[dict[str, Any]] = []
        for item in items:
            variant_id = self._as_uuid(item["variant_id"])
            qty = int(item["qty"])
            if qty <= 0:
                raise ValueError(f"qty must be positive, got {qty}")

            from_city = self._as_uuid(from_city)
            to_city = self._as_uuid(to_city)

            from_city_obj = await self._session.get(City, from_city)
            if from_city_obj is None:
                raise NotFound("city", str(from_city))
            to_city_obj = await self._session.get(City, to_city)
            if to_city_obj is None:
                raise NotFound("city", str(to_city))

            # Снять со склада источника: резерв + подтверждение (on_hand -= qty).
            from_warehouse = await self._select_warehouse(from_city, variant_id, qty)
            await self._inventory.reserve(from_warehouse, variant_id, qty)
            await self._inventory.commit(from_warehouse, variant_id, qty)

            # Пополнить склад назначения (on_hand += qty).
            to_warehouse = await self._select_any_warehouse(to_city, variant_id)
            await self._receive(to_warehouse, variant_id, qty)

            await self._emit_outbox(
                "stock_level",
                from_warehouse,
                "transfer_out",
                {
                    "variant_id": str(variant_id),
                    "from_city": str(from_city),
                    "to_city": str(to_city),
                    "from_warehouse": str(from_warehouse),
                    "to_warehouse": str(to_warehouse),
                    "qty": qty,
                },
            )
            await self._emit_outbox(
                "stock_level",
                to_warehouse,
                "transfer_in",
                {
                    "variant_id": str(variant_id),
                    "from_city": str(from_city),
                    "to_city": str(to_city),
                    "from_warehouse": str(from_warehouse),
                    "to_warehouse": str(to_warehouse),
                    "qty": qty,
                },
            )
            processed.append(
                {
                    "variant_id": variant_id,
                    "qty": qty,
                    "from_city": from_city,
                    "to_city": to_city,
                    "from_warehouse": from_warehouse,
                    "to_warehouse": to_warehouse,
                }
            )
        return processed

    # ---------- истечение резервов ----------

    async def expire_reservations(self) -> list[InventoryReservation]:
        """Пометить истёкшие активные резервы как expired и вернуть товар на склад.

        Возвращает список истёкших резервов.
        """
        now = datetime.now(UTC)
        result = await self._session.execute(
            select(InventoryReservation).where(
                InventoryReservation.status == "active",
                InventoryReservation.expires_at.is_not(None),
                InventoryReservation.expires_at < now,
            )
        )
        reservations = list(result.scalars().all())
        for reservation in reservations:
            await self._inventory.release(
                reservation.warehouse_id, reservation.variant_id, reservation.qty
            )
            reservation.status = "expired"
            await self._session.flush()

            await self._emit_outbox(
                "inventory_reservation",
                reservation.id,
                "expired",
                {
                    "order_id": str(reservation.order_id),
                    "variant_id": str(reservation.variant_id),
                    "city_id": str(reservation.city_id),
                    "warehouse_id": str(reservation.warehouse_id),
                    "qty": reservation.qty,
                },
            )
        return reservations

    # ---------- сверка ----------

    async def reconcile(self) -> list[dict[str, Any]]:
        """Сверка фактических резервов (stock_levels.reserved) с суммой активных
        inventory_reservations по городу+варианту. Возвращает расхождения."""
        # Резерв, зафиксированный в stock_levels, сгруппированный по городу+варианту.
        stock_stmt = (
            select(
                Warehouse.city_id.label("city_id"),
                StockLevel.variant_id.label("variant_id"),
                func.sum(StockLevel.reserved).label("stock_reserved"),
            )
            .select_from(StockLevel)
            .join(Warehouse, Warehouse.id == StockLevel.warehouse_id)
            .group_by(Warehouse.city_id, StockLevel.variant_id)
        )
        stock_rows = (await self._session.execute(stock_stmt)).all()
        stock_reserved: dict[tuple[uuid.UUID, uuid.UUID], int] = {
            (row.city_id, row.variant_id): int(row.stock_reserved or 0)
            for row in stock_rows
        }

        # Сумма активных резервов, сгруппированная по городу+варианту.
        res_stmt = (
            select(
                InventoryReservation.city_id,
                InventoryReservation.variant_id,
                func.sum(InventoryReservation.qty).label("reservation_qty"),
            )
            .where(InventoryReservation.status == "active")
            .group_by(InventoryReservation.city_id, InventoryReservation.variant_id)
        )
        res_rows = (await self._session.execute(res_stmt)).all()
        reservation_qty: dict[tuple[uuid.UUID, uuid.UUID], int] = {
            (row.city_id, row.variant_id): int(row.reservation_qty or 0)
            for row in res_rows
        }

        discrepancies: list[dict[str, Any]] = []
        all_keys = set(stock_reserved) | set(reservation_qty)
        for key in all_keys:
            city_id, variant_id = key
            sr = stock_reserved.get(key, 0)
            rq = reservation_qty.get(key, 0)
            if sr != rq:
                discrepancies.append(
                    {
                        "city_id": city_id,
                        "variant_id": variant_id,
                        "stock_reserved": sr,
                        "reservation_qty": rq,
                        "difference": sr - rq,
                    }
                )
        return discrepancies

    # ---------- вспомогательное ----------

    async def _select_any_warehouse(
        self, city_id: uuid.UUID, variant_id: uuid.UUID
    ) -> uuid.UUID:
        """Любой активный склад города с остатком варианта (или первый активный склад города)."""
        result = await self._session.execute(
            select(Warehouse.id)
            .join(StockLevel, StockLevel.warehouse_id == Warehouse.id)
            .where(Warehouse.city_id == city_id, StockLevel.variant_id == variant_id)
            .order_by(Warehouse.id)
            .limit(1)
        )
        row = result.first()
        if row is not None:
            return row[0]
        # Нет склада с остатком варианта — взять первый активный склад города.
        result = await self._session.execute(
            select(Warehouse.id)
            .where(Warehouse.city_id == city_id, Warehouse.is_active.is_(True))
            .order_by(Warehouse.id)
            .limit(1)
        )
        row = result.first()
        if row is None:
            raise NotFound("warehouse", f"city={city_id}")
        return row[0]

    async def _receive(self, warehouse_id: uuid.UUID, variant_id: uuid.UUID, qty: int) -> None:
        """Пополнить остаток на складе (on_hand += qty)."""
        result = await self._session.execute(
            select(StockLevel).where(
                StockLevel.warehouse_id == warehouse_id,
                StockLevel.variant_id == variant_id,
            )
        )
        level = result.scalar_one_or_none()
        if level is None:
            level = StockLevel(
                warehouse_id=warehouse_id,
                variant_id=variant_id,
                on_hand=qty,
                reserved=0,
            )
            self._session.add(level)
            await self._session.flush()
        else:
            level.on_hand = level.on_hand + qty
            await self._session.flush()

    async def _emit_outbox(
        self,
        aggregate_type: str,
        aggregate_id: uuid.UUID,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        self._session.add(
            Outbox(
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                event_type=event_type,
                payload=payload,
            )
        )
