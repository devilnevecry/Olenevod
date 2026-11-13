"""Сервис доставки: расчёт стоимости и сроков доставки заказа по городу.

Расчёт чистый: тариф и срок берутся из таблиц delivery_zones / delivery_tariffs,
вес позиции — из product_variants.pack_weight_g. Никаких внешних вызовов.
"""

import math
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from olenevod.domain.exceptions import NotFound
from olenevod.infrastructure.models import (
    City,
    DeliveryTariff,
    DeliveryZone,
    ProductVariant,
)


class DeliveryService:
    """Расчёт стоимости и условий доставки для города-исполнителя."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def calculate_delivery(
        self,
        city_id: uuid.UUID,
        items: list[dict[str, Any]],
        total_amount: int,
    ) -> dict[str, Any]:
        """Рассчитать доставку.

        Возвращает ``{fee, free_delivery, estimated_days, zone}``:
        - ``fee`` — стоимость доставки в копейках (0 при бесплатной доставке);
        - ``free_delivery`` — доставка бесплатна (сумма корзины >= порога зоны);
        - ``estimated_days`` — оценочный срок доставки в днях или None;
        - ``zone`` — название зоны доставки города.

        items — список ``{variant_id, qty}``. Вес позиции берётся из
        ``product_variants.pack_weight_g`` (граммы); варианты без веса считаются
        как 0 г.
        """
        city = await self._session.get(City, city_id)
        if city is None:
            raise NotFound("city", str(city_id))

        zone = await self._session.scalar(
            select(DeliveryZone).where(DeliveryZone.city_id == city_id)
        )
        if zone is None:
            raise NotFound("delivery_zone", str(city_id))

        tariff = await self._session.scalar(
            select(DeliveryTariff).where(DeliveryTariff.zone_id == zone.id)
        )

        total_weight_g = 0
        for item in items:
            variant_id = item["variant_id"]
            qty = int(item.get("qty", 1))
            if qty <= 0:
                raise ValueError(f"qty must be positive, got {qty}")
            variant = await self._session.get(ProductVariant, variant_id)
            weight_g = int(variant.pack_weight_g or 0) if variant is not None else 0
            total_weight_g += weight_g * qty

        weight_kg = math.ceil(total_weight_g / 1000)
        fee = int(zone.base_fee) + int(zone.per_kg_fee) * weight_kg

        free_delivery = (
            zone.free_from_amount is not None and int(total_amount) >= int(zone.free_from_amount)
        )
        if free_delivery:
            fee = 0

        estimated_days: int | None = None
        if tariff is not None and tariff.estimated_days is not None:
            estimated_days = int(tariff.estimated_days)

        return {
            "fee": fee,
            "free_delivery": free_delivery,
            "estimated_days": estimated_days,
            "zone": zone.zone_name,
        }
