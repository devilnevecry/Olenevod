"""Сервис уведомлений: e-mail при событиях заказов (VERIFIED_SIMULATED).

Письма не отправляются через SMTP: каждое уведомление фиксируется в
notification_log со статусом sent. Фоновая доставка через arq
(send_notification_job) делает до 3 попыток с экспоненциальной задержкой и
переносит исчерпавшую ретраи запись в notification_dead_letter.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from arq.connections import RedisSettings
from arq.worker import Retry
from sqlalchemy import DateTime, Integer, String, Text, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from olenevod.domain.exceptions import DomainError
from olenevod.infrastructure.db import Base, async_session
from olenevod.infrastructure.models import Order


class NotificationLog(Base):
    """Запись об отправленном (или не отправленном) уведомлении."""

    __tablename__ = "notification_log"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False, default=0)


class NotificationDeadLetter(Base):
    """Архив уведомлений, которым не удалось доставить после всех ретраев."""

    __tablename__ = "notification_dead_letter"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    log_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    failed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class NotificationSendError(DomainError):
    """Ошибка доставки уведомления — повторить позже или перенести в dead-letter."""

    code = "notification_send_error"


class NotificationService:
    """Уведомления о событиях заказов.

    send_* Methoden сохраняют уведомление в notification_log со статусом
    sent (реальный SMTP не используется — VERIFIED_SIMULATED).
    send_via_job — одна попытка фоновой доставки arq-задачи с ретраями
    и dead-letter.
    """

    MAX_ATTEMPTS = 3

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ---------- отправка уведомлений о событиях заказов (simulated) ----------

    async def send_order_created(self, order: Order) -> NotificationLog:
        """Уведомление «заказ создан»."""
        return await self._send(
            event_type="order_created",
            recipient=self._recipient_for_order(order.id),
            subject=f"Заказ {order.id} оформлен",
            body=(
                f"Ваш заказ {order.id} на сумму {order.total_amount} kop "
                "принят в обработку (статус: pending_payment)."
            ),
        )

    async def send_payment_confirmed(self, order: Order) -> NotificationLog:
        """Уведомление «оплата подтверждена»."""
        return await self._send(
            event_type="payment_confirmed",
            recipient=self._recipient_for_order(order.id),
            subject=f"Оплата заказа {order.id} подтверждена",
            body=f"Заказ {order.id} оплачен. Статус изменён на new.",
        )

    async def send_status_changed(
        self, order: Order, old_status: str, new_status: str
    ) -> NotificationLog:
        """Уведомление «статус заказа изменён»."""
        return await self._send(
            event_type="status_changed",
            recipient=self._recipient_for_order(order.id),
            subject=f"Статус заказа {order.id} изменён",
            body=f"Статус заказа {order.id} изменён с {old_status} на {new_status}.",
        )

    async def _send(
        self, *, event_type: str, recipient: str, subject: str, body: str
    ) -> NotificationLog:
        """Записать уведомление в лог со статусом sent (SMTP не используется)."""
        row = NotificationLog(
            event_type=event_type,
            recipient=recipient,
            subject=subject,
            body=body,
            status="sent",
            sent_at=datetime.now(UTC),
            attempts=1,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.commit()
        return row

    @staticmethod
    def _recipient_for_order(order_id: uuid.UUID) -> str:
        """Тестовый адрес получателя, производный от заказа (не реальный e-mail)."""
        return f"order-{order_id}@olenevod.test"

    # ---------- чтение ----------

    async def list_for_order(self, order_id: uuid.UUID) -> list[NotificationLog]:
        """Уведомления заказа, найденные по получателю (производному от order_id)."""
        result = await self._session.execute(
            select(NotificationLog)
            .where(NotificationLog.recipient == self._recipient_for_order(order_id))
            .order_by(NotificationLog.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_log(self, log_id: uuid.UUID) -> NotificationLog | None:
        """Запись лога по идентификатору."""
        return await self._session.get(NotificationLog, log_id)

    # ---------- arq: фоновая доставка с ретраями и dead-letter ----------

    async def send_via_job(self, log_id: uuid.UUID, *, fail: bool = False) -> str:
        """Одна попытка доставки существующей записи лога.

        Возвращает 'sent' при успешной доставке, 'dead_letter' после
        переноса в таблицу мёртвых писем. При неудаче и неисчерпанных
        ретраях возбуждает arq.Retry с экспоненциальной задержкой, чтобы
        arq-воркер повторил задачу.
        """
        row = await self._session.get(NotificationLog, log_id)
        if row is None:
            return "dead_letter"
        if row.status == "sent":
            return "sent"

        try:
            if fail:
                raise NotificationSendError("simulated delivery failure")
            row.status = "sent"
            row.sent_at = datetime.now(UTC)
            row.attempts += 1
            await self._session.commit()
            return "sent"
        except NotificationSendError as exc:
            row.attempts += 1
            await self._session.flush()
            if row.attempts >= self.MAX_ATTEMPTS:
                dead = NotificationDeadLetter(
                    log_id=row.id,
                    event_type=row.event_type,
                    recipient=row.recipient,
                    subject=row.subject,
                    body=row.body,
                    attempts=row.attempts,
                    last_error=str(exc),
                )
                self._session.add(dead)
                await self._session.delete(row)
                await self._session.commit()
                return "dead_letter"
            await self._session.commit()
            raise Retry(defer=float(2 ** (row.attempts - 1))) from exc


async def send_notification_job(
    ctx: Any,
    log_id: uuid.UUID,
    fail: bool = False,
    session_factory: async_sessionmaker[AsyncSession] = async_session,
) -> None:
    """arq-задача: доставить уведомление (ретраи и dead-letter внутри сервиса)."""
    async with session_factory() as session:
        service = NotificationService(session)
        await service.send_via_job(log_id, fail=fail)


class WorkerSettings:
    """Настройка arq-воркера уведомлений.

    Запуск: `arq olenevod.application.notification_service:WorkerSettings`
    (требует Redis, не используется в тестах — задачи вызываются напрямую).
    """

    functions = [send_notification_job]
    redis_settings = RedisSettings(host="localhost", port=6379, database=0)
    max_tries: int = 3
