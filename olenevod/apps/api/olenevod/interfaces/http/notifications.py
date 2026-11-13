"""HTTP-роуты уведомлений: список уведомлений заказа.

Бизнес-логика делегируется NotificationService (этап 11); HTTP-слой только
сериализует ответ.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from olenevod.application.notification_service import NotificationService
from olenevod.infrastructure.db import async_session

router = APIRouter(tags=["notifications"])


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Сессия SQLAlchemy на время одного HTTP-запроса (чтение и запись)."""
    async with async_session() as session:
        yield session


# ---------- схемы ответа ----------

class NotificationOut(BaseModel):
    id: uuid.UUID
    event_type: str
    recipient: str
    subject: str
    body: str
    status: str
    created_at: datetime
    sent_at: datetime | None
    attempts: int


# ---------- роуты ----------

@router.get(
    "/notifications/{order_id}",
    response_model=list[NotificationOut],
    summary="Список уведомлений заказа (e-mail simulated)",
)
async def list_notifications(
    order_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> list[NotificationOut]:
    """Все уведомления заказа (ищут по получателю, производному от order_id)."""
    service = NotificationService(session)
    logs = await service.list_for_order(order_id)
    return [
        NotificationOut(
            id=row.id,
            event_type=row.event_type,
            recipient=row.recipient,
            subject=row.subject,
            body=row.body,
            status=row.status,
            created_at=row.created_at,
            sent_at=row.sent_at,
            attempts=row.attempts,
        )
        for row in logs
    ]
