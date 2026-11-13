"""Платёжный сервис: создание платежа (симуляция) и обработка вебхука.

PaymentService не вызывает реального провайдера (VERIFIED_SIMULATED,
токен владельца не придумывается). Смена статуса заказа pending_payment -> new
выполняется через OrderService.
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from olenevod.application.order_service import OrderRepository
from olenevod.infrastructure.models import Order, Payment


class PaymentService:
    """Платежи: создание симулированного платежа и обработка вебхука провайдера."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._orders = OrderRepository(session)

    async def create_payment(self, order: Order) -> str:
        """Создать платёж в статусе pending и вернуть внешнюю URL оплаты (симуляция).

        Платеж фиксируется в БД (коммит внутри сервиса), чтобы вебхук
        из другого HTTP-запроса (другая сессия) мог его найти.
        """
        payment = Payment(
            order_id=order.id,
            provider="yukassa",
            amount=order.total_amount,
            status="pending",
            external_id=None,
        )
        self._session.add(payment)
        await self._session.flush()
        await self._session.commit()
        return (
            f"https://pay.olenevod.local/pay/{payment.id}"
            f"?provider=yukassa&amount={order.total_amount}"
        )

    async def handle_webhook(self, provider: str, payload: dict[str, Any]) -> Order | None:
        """Обработать вебхук провайдера.

        При оплате платежа — сменить статус заказа pending_payment -> new
        через OrderService. Вернуть обновлённый заказ или None, если
        платёж/заказ не найден.
        """
        raw_order_id = payload.get("order_id")
        if raw_order_id is None:
            return None
        order_id = uuid.UUID(str(raw_order_id))

        result = await self._session.execute(
            select(Payment).where(
                Payment.order_id == order_id, Payment.provider == provider
            )
        )
        payment = result.scalar_one_or_none()
        if payment is None:
            return None

        payment.status = "paid"
        await self._session.flush()

        order = await self._orders.change_status(order_id, "new")
        if order is None:
            return None

        await self._session.commit()
        return order
