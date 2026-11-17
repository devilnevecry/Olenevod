"""HTTP-роуты заказов: оформление заказа и карточка заказа.

Бизнес-логика делегируется OrderService (этап 5); HTTP-слой только
сериализует запросы/ответы и транслирует доменные ошибки в HTTP-статусы.
"""

import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from olenevod.application.order_service import OrderService
from olenevod.domain.exceptions import NotFound, OutOfStock
from olenevod.infrastructure.db import async_session

router = APIRouter(tags=["orders"])


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Сессия SQLAlchemy на время одного HTTP-запроса (чтение и запись)."""
    async with async_session() as session:
        yield session


# ---------- схемы запроса/ответа ----------

class OrderItemIn(BaseModel):
    product_variant_id: uuid.UUID
    qty: int = Field(ge=1)


class OrderIn(BaseModel):
    city_id: uuid.UUID
    customer_name: str
    customer_phone: str
    items: list[OrderItemIn]
    idempotency_key: str | None = None


class OrderItemOut(BaseModel):
    id: uuid.UUID
    product_variant_id: uuid.UUID
    qty: int
    price: int


class OrderOut(BaseModel):
    id: uuid.UUID
    city_id: uuid.UUID
    customer_name: str
    customer_phone: str
    status: str
    total_amount: int
    idempotency_key: str | None = None
    items: list[OrderItemOut] = []


# ---------- роуты ----------

@router.post(
    "/orders",
    status_code=201,
    response_model=OrderOut,
    summary="Оформить заказ с атомарным резервом стока",
)
async def create_order(
    data: OrderIn,
    session: AsyncSession = Depends(get_session),
) -> OrderOut:
    service = OrderService(session)
    try:
        order, items_orm = await service.place_order(
            city_id=data.city_id,
            customer_name=data.customer_name,
            customer_phone=data.customer_phone,
            items=[
                {"product_variant_id": item.product_variant_id, "qty": item.qty}
                for item in data.items
            ],
            idempotency_key=data.idempotency_key,
        )
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc
    except OutOfStock as exc:
        raise HTTPException(
            status_code=409,
            detail=f"insufficient stock for variant {exc.extra.get('variant_id')}",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OrderOut(
        id=order.id,
        city_id=order.city_id,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        status=order.status,
        total_amount=order.total_amount,
        idempotency_key=order.idempotency_key,
        items=[
            OrderItemOut(
                id=item.id,
                product_variant_id=item.product_variant_id,
                qty=item.qty,
                price=item.price,
            )
            for item in items_orm
        ],
    )


@router.get(
    "/orders/{order_id}",
    response_model=OrderOut,
    summary="Карточка заказа со статусом и позициями",
)
async def get_order(
    order_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> OrderOut:
    service = OrderService(session)
    result = await service.get_order(order_id)
    if result is None:
        raise HTTPException(status_code=404, detail="order not found")
    order, items_orm = result
    return OrderOut(
        id=order.id,
        city_id=order.city_id,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        status=order.status,
        total_amount=order.total_amount,
        items=[
            OrderItemOut(
                id=item.id,
                product_variant_id=item.product_variant_id,
                qty=item.qty,
                price=item.price,
            )
            for item in items_orm
        ],
    )
