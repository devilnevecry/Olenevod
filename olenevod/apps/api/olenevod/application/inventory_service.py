"""Ð¡ÐµÑ€Ð²Ð¸Ñ Ð¾ÑÑ‚Ð°Ñ‚ÐºÐ¾Ð²: Ñ€ÐµÐ·ÐµÑ€Ð², Ð¿Ð¾Ð´Ñ‚Ð²ÐµÑ€Ð¶Ð´ÐµÐ½Ð¸Ðµ, Ð¾ÑÐ²Ð¾Ð±Ð¾Ð¶Ð´ÐµÐ½Ð¸Ðµ, Ð²Ð¾Ð·Ð²Ñ€Ð°Ñ‚, Ð¿ÐµÑ€ÐµÐ¼ÐµÑ‰ÐµÐ½Ð¸Ðµ, Ð¸ÑÑ‚ÐµÑ‡ÐµÐ½Ð¸Ðµ, ÑÐ²ÐµÑ€ÐºÐ°.

Ð’ÑÐµ Ð¸Ð·Ð¼ÐµÐ½ÐµÐ½Ð¸Ñ Ð¾ÑÑ‚Ð°Ñ‚ÐºÐ¾Ð² Ð²Ñ‹Ð¿Ð¾Ð»Ð½ÑÑŽÑ‚ÑÑ Ñ‡ÐµÑ€ÐµÐ· ``InventoryRepository`` (Ð°Ñ‚Ð¾Ð¼Ð°Ñ€Ð½Ñ‹Ðµ
``UPDATE ... WHERE``). Ð¡ÐµÑ€Ð²Ð¸Ñ Ð½Ðµ Ð´ÐµÐ»Ð°ÐµÑ‚ read-modify-write Ð² Ð¿Ñ€Ð¸Ð»Ð¾Ð¶ÐµÐ½Ð¸Ð¸.
Ð¡Ð¾Ð±Ñ‹Ñ‚Ð¸Ñ Ð¸Ð·Ð¼ÐµÐ½ÐµÐ½Ð¸Ñ Ð¾ÑÑ‚Ð°Ñ‚ÐºÐ¾Ð² Ð¿Ð¸ÑˆÑƒÑ‚ÑÑ Ð² outbox Ð² Ñ‚Ð¾Ð¹ Ð¶Ðµ Ñ‚Ñ€Ð°Ð½Ð·Ð°ÐºÑ†Ð¸Ð¸.
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
    """Ð£Ð¿Ñ€Ð°Ð²Ð»ÐµÐ½Ð¸Ðµ Ð¾ÑÑ‚Ð°Ñ‚ÐºÐ°Ð¼Ð¸ Ñ‚Ð¾Ð²Ð°Ñ€Ð° Ð¿Ð¾ Ð³Ð¾Ñ€Ð¾Ð´Ð°Ð¼/ÑÐºÐ»Ð°Ð´Ð°Ð¼."""

    RESERVATION_TTL_MINUTES = 30

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._inventory = InventoryRepository(session)

    # ---------- Ñ€ÐµÐ·ÐµÑ€Ð² ----------

    async def reserve(
        self,
        order_id: uuid.UUID,
        items: list[dict[str, Any]],
        *,
        idempotency_key: str | None = None,
        ttl_minutes: int | None = None,
    ) -> list[InventoryReservation]:
        """Ð—Ð°Ñ€ÐµÐ·ÐµÑ€Ð²Ð¸Ñ€Ð¾Ð²Ð°Ñ‚ÑŒ Ð¾ÑÑ‚Ð°Ñ‚Ð¾Ðº Ð¿Ð¾Ð´ Ð·Ð°ÐºÐ°Ð·.

        items â€” ÑÐ¿Ð¸ÑÐ¾Ðº ``{variant_id, city_id, qty}``.
        ``idempotency_key`` â€” Ð¿Ñ€Ð¸ Ð¿Ð¾Ð²Ñ‚Ð¾Ñ€Ð½Ð¾Ð¼ Ð²Ñ‹Ð·Ð¾Ð²Ðµ Ñ Ñ‚ÐµÐ¼ Ð¶Ðµ ÐºÐ»ÑŽÑ‡Ð¾Ð¼ Ð²Ð¾Ð·Ð²Ñ€Ð°Ñ‰Ð°ÑŽÑ‚ÑÑ
        ÑƒÐ¶Ðµ ÑÐ¾Ð·Ð´Ð°Ð½Ð½Ñ‹Ðµ Ñ€ÐµÐ·ÐµÑ€Ð²Ñ‹ (Ð¿Ñ€Ð¾Ð²ÐµÑ€ÐºÐ° Ð²Ñ‹Ð¿Ð¾Ð»Ð½ÑÐµÑ‚ÑÑ Ð¿ÐµÑ€ÐµÐ´ Ð²Ñ‹Ð¿Ð¾Ð»Ð½ÐµÐ½Ð¸ÐµÐ¼).
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
        """Ð¡ÐºÐ»Ð°Ð´ Ð³Ð¾Ñ€Ð¾Ð´Ð° Ñ Ð½Ð°Ð¸Ð±Ð¾Ð»ÑŒÑˆÐ¸Ð¼ Ð´Ð¾ÑÑ‚ÑƒÐ¿Ð½Ñ‹Ð¼ Ð¾ÑÑ‚Ð°Ñ‚ÐºÐ¾Ð¼ Ð²Ð°Ñ€Ð¸Ð°Ð½Ñ‚Ð°, Ð·Ð°ÐºÑ€Ñ‹Ð²Ð°ÑŽÑ‰Ð¸Ð¹ qty."""
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

    # ---------- Ð¿Ð¾Ð´Ñ‚Ð²ÐµÑ€Ð¶Ð´ÐµÐ½Ð¸Ðµ / Ð¾ÑÐ²Ð¾Ð±Ð¾Ð¶Ð´ÐµÐ½Ð¸Ðµ ----------

    async def commit(self, reservation_id: uuid.UUID) -> InventoryReservation | None:
        """ÐŸÐ¾Ð´Ñ‚Ð²ÐµÑ€Ð´Ð¸Ñ‚ÑŒ Ñ€ÐµÐ·ÐµÑ€Ð²: ÑÐ¿Ð¸ÑÐ°Ñ‚ÑŒ ÑÐ¾ ÑÐºÐ»Ð°Ð´Ð° (on_hand -= qty, reserved -= qty).

        Ð’Ð¾Ð·Ð²Ñ€Ð°Ñ‰Ð°ÐµÑ‚ Ñ€ÐµÐ·ÐµÑ€Ð²Ð°Ñ†Ð¸ÑŽ Ð¸Ð»Ð¸ None, ÐµÑÐ»Ð¸ Ð½Ðµ Ð½Ð°Ð¹Ð´ÐµÐ½Ð°.
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
        """ÐžÑÐ²Ð¾Ð±Ð¾Ð´Ð¸Ñ‚ÑŒ Ñ€ÐµÐ·ÐµÑ€Ð² (reserved -= qty, ÑÑ‚Ð°Ñ‚ÑƒÑ released)."""
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

    # ---------- Ð²Ð¾Ð·Ð²Ñ€Ð°Ñ‚ Ð½Ð° ÑÐºÐ»Ð°Ð´ ----------

    async def return_items(
        self, items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Ð’ÐµÑ€Ð½ÑƒÑ‚ÑŒ Ñ‚Ð¾Ð²Ð°Ñ€ Ð½Ð° ÑÐºÐ»Ð°Ð´ (on_hand += qty).

        items â€” ÑÐ¿Ð¸ÑÐ¾Ðº ``{variant_id, city_id, qty}``. Ð’Ð¾Ð·Ð²Ñ€Ð°Ñ‰Ð°ÐµÑ‚ Ð¾Ð±Ñ€Ð°Ð±Ð¾Ñ‚Ð°Ð½Ð½Ñ‹Ðµ
        Ð¿Ð¾Ð·Ð¸Ñ†Ð¸Ð¸ Ñ warehouse_id.
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

    # ---------- Ð¿ÐµÑ€ÐµÐ¼ÐµÑ‰ÐµÐ½Ð¸Ðµ Ð¼ÐµÐ¶Ð´Ñƒ Ð³Ð¾Ñ€Ð¾Ð´Ð°Ð¼Ð¸ ----------

    async def transfer(
        self, from_city: uuid.UUID, to_city: uuid.UUID, items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """ÐŸÐµÑ€ÐµÐ¼ÐµÑÑ‚Ð¸Ñ‚ÑŒ Ñ‚Ð¾Ð²Ð°Ñ€ Ð¼ÐµÐ¶Ð´Ñƒ Ð³Ð¾Ñ€Ð¾Ð´Ð°Ð¼Ð¸.

        items â€” ÑÐ¿Ð¸ÑÐ¾Ðº ``{variant_id, qty}``. Ð¡Ð½Ð¸Ð¼Ð°ÐµÑ‚ Ð¾ÑÑ‚Ð°Ñ‚Ð¾Ðº Ð² from_city Ð¸
        Ð¿Ð¾Ð¿Ð¾Ð»Ð½ÑÐµÑ‚ Ð² to_city. Ð’Ð¾Ð·Ð²Ñ€Ð°Ñ‰Ð°ÐµÑ‚ Ð¾Ð±Ñ€Ð°Ð±Ð¾Ñ‚Ð°Ð½Ð½Ñ‹Ðµ Ð¿Ð¾Ð·Ð¸Ñ†Ð¸Ð¸.
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

            # Ð¡Ð½ÑÑ‚ÑŒ ÑÐ¾ ÑÐºÐ»Ð°Ð´Ð° Ð¸ÑÑ‚Ð¾Ñ‡Ð½Ð¸ÐºÐ°: Ñ€ÐµÐ·ÐµÑ€Ð² + Ð¿Ð¾Ð´Ñ‚Ð²ÐµÑ€Ð¶Ð´ÐµÐ½Ð¸Ðµ (on_hand -= qty).
            from_warehouse = await self._select_warehouse(from_city, variant_id, qty)
            await self._inventory.reserve(from_warehouse, variant_id, qty)
            await self._inventory.commit(from_warehouse, variant_id, qty)

            # ÐŸÐ¾Ð¿Ð¾Ð»Ð½Ð¸Ñ‚ÑŒ ÑÐºÐ»Ð°Ð´ Ð½Ð°Ð·Ð½Ð°Ñ‡ÐµÐ½Ð¸Ñ (on_hand += qty).
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

    # ---------- Ð¸ÑÑ‚ÐµÑ‡ÐµÐ½Ð¸Ðµ Ñ€ÐµÐ·ÐµÑ€Ð²Ð¾Ð² ----------

    async def expire_reservations(self) -> list[InventoryReservation]:
        """ÐŸÐ¾Ð¼ÐµÑ‚Ð¸Ñ‚ÑŒ Ð¸ÑÑ‚Ñ‘ÐºÑˆÐ¸Ðµ Ð°ÐºÑ‚Ð¸Ð²Ð½Ñ‹Ðµ Ñ€ÐµÐ·ÐµÑ€Ð²Ñ‹ ÐºÐ°Ðº expired Ð¸ Ð²ÐµÑ€Ð½ÑƒÑ‚ÑŒ Ñ‚Ð¾Ð²Ð°Ñ€ Ð½Ð° ÑÐºÐ»Ð°Ð´.

        Ð’Ð¾Ð·Ð²Ñ€Ð°Ñ‰Ð°ÐµÑ‚ ÑÐ¿Ð¸ÑÐ¾Ðº Ð¸ÑÑ‚Ñ‘ÐºÑˆÐ¸Ñ… Ñ€ÐµÐ·ÐµÑ€Ð²Ð¾Ð².
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

    # ---------- ÑÐ²ÐµÑ€ÐºÐ° ----------

    async def reconcile(self) -> list[dict[str, Any]]:
        """Ð¡Ð²ÐµÑ€ÐºÐ° Ñ„Ð°ÐºÑ‚Ð¸Ñ‡ÐµÑÐºÐ¸Ñ… Ñ€ÐµÐ·ÐµÑ€Ð²Ð¾Ð² (stock_levels.reserved) Ñ ÑÑƒÐ¼Ð¼Ð¾Ð¹ Ð°ÐºÑ‚Ð¸Ð²Ð½Ñ‹Ñ…
        inventory_reservations Ð¿Ð¾ Ð³Ð¾Ñ€Ð¾Ð´Ñƒ+Ð²Ð°Ñ€Ð¸Ð°Ð½Ñ‚Ñƒ. Ð’Ð¾Ð·Ð²Ñ€Ð°Ñ‰Ð°ÐµÑ‚ Ñ€Ð°ÑÑ…Ð¾Ð¶Ð´ÐµÐ½Ð¸Ñ."""
        # Ð ÐµÐ·ÐµÑ€Ð², Ð·Ð°Ñ„Ð¸ÐºÑÐ¸Ñ€Ð¾Ð²Ð°Ð½Ð½Ñ‹Ð¹ Ð² stock_levels, ÑÐ³Ñ€ÑƒÐ¿Ð¿Ð¸Ñ€Ð¾Ð²Ð°Ð½Ð½Ñ‹Ð¹ Ð¿Ð¾ Ð³Ð¾Ñ€Ð¾Ð´Ñƒ+Ð²Ð°Ñ€Ð¸Ð°Ð½Ñ‚Ñƒ.
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

        # Ð¡ÑƒÐ¼Ð¼Ð° Ð°ÐºÑ‚Ð¸Ð²Ð½Ñ‹Ñ… Ñ€ÐµÐ·ÐµÑ€Ð²Ð¾Ð², ÑÐ³Ñ€ÑƒÐ¿Ð¿Ð¸Ñ€Ð¾Ð²Ð°Ð½Ð½Ð°Ñ Ð¿Ð¾ Ð³Ð¾Ñ€Ð¾Ð´Ñƒ+Ð²Ð°Ñ€Ð¸Ð°Ð½Ñ‚Ñƒ.
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

    # ---------- Ð²ÑÐ¿Ð¾Ð¼Ð¾Ð³Ð°Ñ‚ÐµÐ»ÑŒÐ½Ð¾Ðµ ----------

    async def _select_any_warehouse(
        self, city_id: uuid.UUID, variant_id: uuid.UUID
    ) -> uuid.UUID:
        """Ð›ÑŽÐ±Ð¾Ð¹ Ð°ÐºÑ‚Ð¸Ð²Ð½Ñ‹Ð¹ ÑÐºÐ»Ð°Ð´ Ð³Ð¾Ñ€Ð¾Ð´Ð° Ñ Ð¾ÑÑ‚Ð°Ñ‚ÐºÐ¾Ð¼ Ð²Ð°Ñ€Ð¸Ð°Ð½Ñ‚Ð° (Ð¸Ð»Ð¸ Ð¿ÐµÑ€Ð²Ñ‹Ð¹ Ð°ÐºÑ‚Ð¸Ð²Ð½Ñ‹Ð¹ ÑÐºÐ»Ð°Ð´ Ð³Ð¾Ñ€Ð¾Ð´Ð°)."""
        result = await self._session.execute(
            select(Warehouse.id)
            .join(StockLevel, StockLevel.warehouse_id == Warehouse.id)
            .where(Warehouse.city_id == city_id, StockLevel.variant_id == variant_id)
            .order_by(Warehouse.id)
            .limit(1)
        )
        row = result.first()
        if row is not None:
            return uuid.UUID(str(row[0]))
        # ÐÐµÑ‚ ÑÐºÐ»Ð°Ð´Ð° Ñ Ð¾ÑÑ‚Ð°Ñ‚ÐºÐ¾Ð¼ Ð²Ð°Ñ€Ð¸Ð°Ð½Ñ‚Ð° â€” Ð²Ð·ÑÑ‚ÑŒ Ð¿ÐµÑ€Ð²Ñ‹Ð¹ Ð°ÐºÑ‚Ð¸Ð²Ð½Ñ‹Ð¹ ÑÐºÐ»Ð°Ð´ Ð³Ð¾Ñ€Ð¾Ð´Ð°.
        result = await self._session.execute(
            select(Warehouse.id)
            .where(Warehouse.city_id == city_id, Warehouse.is_active.is_(True))
            .order_by(Warehouse.id)
            .limit(1)
        )
        row = result.first()
        if row is None:
            raise NotFound("warehouse", f"city={city_id}")
        return uuid.UUID(str(row[0]))

    async def _receive(self, warehouse_id: uuid.UUID, variant_id: uuid.UUID, qty: int) -> None:
        """ÐŸÐ¾Ð¿Ð¾Ð»Ð½Ð¸Ñ‚ÑŒ Ð¾ÑÑ‚Ð°Ñ‚Ð¾Ðº Ð½Ð° ÑÐºÐ»Ð°Ð´Ðµ (on_hand += qty)."""
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

