"""HTTP-роуты платежей: статус оплаты заказа и вебхук провайдера.

Бизнес-логика делегируется PaymentService (этап 6); HTTP-слой только
сериализует запросы/ответы и возвращает 404, если платёж/заказ не найден.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from olenevod.application.payment_service import PaymentService
from olenevod.infrastructure.db import async_session
from olenevod.infrastructure.models import Payment

router = APIRouter(tags=["payments"])


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Сессия SQLAlchemy на время одного HTTP-запроса (чтение и запись)."""
    async with async_session() as session:
        yield session


# ---------- схемы ответа ----------

class PaymentOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    provider: str
    amount: int
    status: str
    external_id: str | None = None
    created_at: datetime


# ---------- роуты ----------

@router.get(
    "/payments/{order_id}/status",
    response_model=PaymentOut,
    summary="Статус оплаты заказа",
)
async def payment_status(
    order_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> PaymentOut:
    """Последний платёж заказа и его статус."""
    result = await session.execute(
        select(Payment)
        .where(Payment.order_id == order_id)
        .order_by(Payment.created_at.desc())
    )
    payment = result.scalar_one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail="payment not found")
    return PaymentOut(
        id=payment.id,
        order_id=payment.order_id,
        provider=payment.provider,
        amount=payment.amount,
        status=payment.status,
        external_id=payment.external_id,
        created_at=payment.created_at,
    )


@router.post(
    "/payments/webhook/{provider}",
    summary="Вебхук платёжного провайдера (симуляция)",
)
async def webhook(
    provider: str,
    payload: dict[str, Any],
    session: AsyncSession = Depends(get_session),
) -> dict[str, str | uuid.UUID]:
    """Вебхук провайдера: оплаченный платёж переводит заказ pending_payment -> new."""
    service = PaymentService(session)
    order = await service.handle_webhook(provider, payload)
    if order is None:
        raise HTTPException(status_code=404, detail="payment or order not found")
    return {"order_id": order.id, "status": order.status}
