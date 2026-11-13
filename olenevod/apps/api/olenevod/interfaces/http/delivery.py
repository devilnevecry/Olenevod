"""HTTP-роуты доставки: расчёт стоимости (quote).

Бизнес-логика Delegates to DeliveryService (этап 9); HTTP-слой только
сериализует запрос/ответ и транслирует NotFound в 404.
"""

import uuid
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from olenevod.application.delivery_service import DeliveryService
from olenevod.domain.exceptions import NotFound
from olenevod.infrastructure.db import async_session

router = APIRouter(tags=["delivery"])


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Сессия SQLAlchemy на время одного HTTP-запроса (только чтение)."""
    async with async_session() as session:
        yield session


# ---------- схемы ответа ----------

class DeliveryQuoteOut(BaseModel):
    city_id: uuid.UUID
    zone: str
    fee: int
    free_delivery: bool
    estimated_days: int | None = None


# ---------- роуты ----------

@router.get(
    "/delivery/quote",
    response_model=DeliveryQuoteOut,
    summary="Расчёт стоимости доставки для города",
)
async def delivery_quote(
    city_id: uuid.UUID,
    items: list[uuid.UUID] = Query([], description="Идентификаторы вариантов товара (повторяемый параметр)"),
    total_amount: int = Query(0, ge=0, description="Сумма корзины в копейках для проверки порога бесплатной доставки"),
    session: AsyncSession = Depends(get_session),
) -> DeliveryQuoteOut:
    service = DeliveryService(session)
    try:
        result: dict[str, Any] = await service.calculate_delivery(
            city_id,
            [{"variant_id": variant_id, "qty": 1} for variant_id in items],
            total_amount,
        )
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc
    return DeliveryQuoteOut(
        city_id=city_id,
        zone=result["zone"],
        fee=result["fee"],
        free_delivery=result["free_delivery"],
        estimated_days=result["estimated_days"],
    )
