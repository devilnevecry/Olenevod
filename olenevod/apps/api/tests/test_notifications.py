"""Тесты уведомлений (этап 11) на реальной тестовой PostgreSQL.

БД: TEST_DATABASE_URL (postgres:postgres@localhost:5432/olenevod_test).
Сессия переопределяется на тестовую БД (NullPool); данные сидятся прямыми
INSERT'ами — моки не используются, SMTP не задействован (VERIFIED_SIMULATED).
Каждый тест — в своём цикле anyio (httpx.ASGITransport), сессии SQLAlchemy
и asyncpg-соединения никогда не переплетаются между циклами.

arq-задача send_notification_job вызывается напрямую (без Redis-воркера):
ретраи (3 попытки с экспоненциальной задержкой) и dead-letter проверяются
через переключение fail между вызовами.
"""

import uuid

import anyio
import asyncpg
import httpx
import pytest
from alembic import command
from alembic.config import Config
from arq.worker import Retry
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from olenevod.application.notification_service import (
    NotificationLog,
    NotificationService,
    send_notification_job,
)
from olenevod.application.order_service import OrderService
from olenevod.infrastructure.models import Order
from olenevod.interfaces.http.notifications import get_session as notifications_get_session
from olenevod.interfaces.http.orders import get_session as orders_get_session
from olenevod.main import app

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/olenevod_test"

NOTIFY_CITY_ID = uuid.UUID("11111111-1111-1111-1111-111111111005")
NOTIFY_CATEGORY_ID = uuid.UUID("22222222-2222-2222-2222-222222222005")
NOTIFY_PRODUCT_ID = uuid.UUID("33333333-3333-3333-3333-333333333004")
NOTIFY_VARIANT_ID = uuid.UUID("44444444-4444-4444-4444-444444444004")
NOTIFY_WAREHOUSE_ID = uuid.UUID("55555555-5555-5555-5555-555555555006")
NOTIFY_CITY_OFFER_ID = uuid.UUID("66666666-6666-6666-6666-666666666005")

_test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
_test_session_factory = async_sessionmaker(_test_engine, expire_on_commit=False)


async def _override_get_session():
    async with _test_session_factory() as session:
        yield session


app.dependency_overrides[notifications_get_session] = _override_get_session
app.dependency_overrides[orders_get_session] = _override_get_session

SEED_SQL = """
INSERT INTO cities (id, slug, name, region, timezone, is_active) VALUES
  ('11111111-1111-1111-1111-111111111005', 'notify-moscow', 'Москва уведомления', 'Москва', 'Europe/Moscow', true)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO categories (id, parent_id, slug, name, is_published, sort) VALUES
  ('22222222-2222-2222-2222-222222222005', NULL, 'notify-test', 'Тест уведомлений', true, 100)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO products (id, category_id, slug, name, is_published) VALUES
  ('33333333-3333-3333-3333-333333333004', '22222222-2222-2222-2222-222222222005', 'notify-produkt', 'Продукт уведомлений', true)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO product_variants (id, product_id, sku, name, unit_type) VALUES
  ('44444444-4444-4444-4444-444444444004', '33333333-3333-3333-3333-333333333004', 'NOTIFY-001', 'Вариант уведомлений', 'piece')
ON CONFLICT (sku) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO city_offers (id, city_id, variant_id, price_kop, is_published) VALUES
  ('66666666-6666-6666-6666-666666666005', '11111111-1111-1111-1111-111111111005', '44444444-4444-4444-4444-444444444004', 9500, true)
ON CONFLICT (city_id, variant_id) DO UPDATE SET price_kop = EXCLUDED.price_kop;

INSERT INTO warehouses (id, city_id, name, is_active) VALUES
  ('55555555-5555-5555-5555-555555555006', '11111111-1111-1111-1111-111111111005', 'Склад уведомлений', true)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO stock_levels (warehouse_id, variant_id, on_hand, reserved) VALUES
  ('55555555-5555-5555-5555-555555555006', '44444444-4444-4444-4444-444444444004', 100, 0)
ON CONFLICT (warehouse_id, variant_id) DO UPDATE SET on_hand = EXCLUDED.on_hand, reserved = EXCLUDED.reserved;
"""


async def _load_seed() -> None:
    conn = await asyncpg.connect(TEST_DATABASE_URL.replace("+asyncpg", ""))
    try:
        await conn.execute(SEED_SQL)
    finally:
        await conn.close()


async def _fetch_order(order_id: uuid.UUID) -> Order:
    async with _test_session_factory() as session:
        result = await OrderService(session).get_order(order_id)
        assert result is not None, f"order {order_id} not found"
        return result[0]


async def _send_order_created(order: Order) -> NotificationLog:
    async with _test_session_factory() as session:
        return await NotificationService(session).send_order_created(order)


async def _send_payment_confirmed(order: Order) -> NotificationLog:
    async with _test_session_factory() as session:
        return await NotificationService(session).send_payment_confirmed(order)


async def _send_status_changed(
    order: Order, old_status: str, new_status: str
) -> NotificationLog:
    async with _test_session_factory() as session:
        return await NotificationService(session).send_status_changed(
            order, old_status, new_status
        )


async def _set_order_status(order_id: uuid.UUID, status: str) -> None:
    async with _test_session_factory() as session:
        result = await OrderService(session).get_order(order_id)
        assert result is not None, f"order {order_id} not found"
        order, _items = result
        order.status = status
        await session.commit()


async def _insert_pending_log() -> NotificationLog:
    async with _test_session_factory() as session:
        row = NotificationLog(
            event_type="order_created",
            recipient="order-00000000-0000-0000-0000-000000000000@olenevod.test",
            subject="subject",
            body="body",
            status="pending",
            attempts=0,
        )
        session.add(row)
        await session.flush()
        await session.commit()
        return row


async def _get_log_by_id(log_id: uuid.UUID) -> NotificationLog | None:
    async with _test_session_factory() as session:
        return await NotificationService(session).get_log(log_id)


def _run_job(log_id: uuid.UUID, fail: bool = False) -> None:
    async def _run() -> None:
        await send_notification_job(
            {}, log_id, fail=fail, session_factory=_test_session_factory
        )

    anyio.run(_run)


async def _log_rows_for_order(order_id: uuid.UUID) -> list[dict]:
    recipient = f"order-{order_id}@olenevod.test"
    conn = await asyncpg.connect(TEST_DATABASE_URL.replace("+asyncpg", ""))
    try:
        rows = await conn.fetch(
            "SELECT event_type, status FROM notification_log WHERE recipient = $1",
            recipient,
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()


async def _dead_letter_rows_for_log(log_id: uuid.UUID) -> list[dict]:
    conn = await asyncpg.connect(TEST_DATABASE_URL.replace("+asyncpg", ""))
    try:
        rows = await conn.fetch(
            "SELECT attempts, last_error FROM notification_dead_letter WHERE log_id = $1",
            log_id,
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()


@pytest.fixture(autouse=True)
def _seed_db(alembic_config: Config, db_available: bool) -> None:
    """Применить миграции и загрузить демо-данные в тестовую БД."""

    def runner() -> None:
        command.upgrade(alembic_config, "head")

    if not db_available:
        pytest.skip("Тестовая PostgreSQL-БД недоступна (нужен локальный postgres/Docker)")
    runner()
    anyio.run(_load_seed)


def _request(
    method: str,
    path: str,
    params: dict | None = None,
    json_body: dict | None = None,
) -> httpx.Response:
    async def _run() -> httpx.Response:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            return await client.request(method, path, params=params, json=json_body)

    return anyio.run(_run)


NOTIFY_ITEMS = [{"product_variant_id": str(NOTIFY_VARIANT_ID), "qty": 3}]


def test_notification_created_on_order_is_sent() -> None:
    """При создании заказа уведомление order_created появляется в notification_log со статусом sent."""
    response = _request(
        "POST",
        "/orders",
        json_body={
            "city_id": str(NOTIFY_CITY_ID),
            "customer_name": "Покупатель Уведомлений",
            "customer_phone": "+79000000000",
            "items": NOTIFY_ITEMS,
        },
    )
    assert response.status_code == 201, response.text
    order_id = response.json()["id"]

    order = anyio.run(_fetch_order, order_id)
    log = anyio.run(_send_order_created, order)
    assert log.status == "sent"
    assert log.event_type == "order_created"
    assert log.sent_at is not None
    assert log.attempts == 1
    assert log.recipient == f"order-{order_id}@olenevod.test"

    # То же уведомление видно через HTTP-роутер.
    list_response = _request("GET", f"/notifications/{order_id}")
    assert list_response.status_code == 200, list_response.text
    body = list_response.json()
    assert len(body) == 1
    assert body[0]["event_type"] == "order_created"
    assert body[0]["status"] == "sent"
    assert body[0]["recipient"] == log.recipient


def test_payment_confirmed_notification_is_sent() -> None:
    """Уведомление payment_confirmed сохраняется в лог со статусом sent."""
    response = _request(
        "POST",
        "/orders",
        json_body={
            "city_id": str(NOTIFY_CITY_ID),
            "customer_name": "Покупатель Уведомлений",
            "customer_phone": "+79000000000",
            "items": NOTIFY_ITEMS,
        },
    )
    assert response.status_code == 201, response.text
    order_id = response.json()["id"]

    order = anyio.run(_fetch_order, order_id)
    log = anyio.run(_send_payment_confirmed, order)
    assert log.status == "sent"
    assert log.event_type == "payment_confirmed"
    assert log.recipient == f"order-{order_id}@olenevod.test"


def test_status_changed_notification_is_sent() -> None:
    """При смене статуса заказа создаётся уведомление status_changed со статусом sent."""
    response = _request(
        "POST",
        "/orders",
        json_body={
            "city_id": str(NOTIFY_CITY_ID),
            "customer_name": "Покупатель Уведомлений",
            "customer_phone": "+79000000000",
            "items": NOTIFY_ITEMS,
        },
    )
    assert response.status_code == 201, response.text
    order_id = response.json()["id"]

    anyio.run(_set_order_status, order_id, "new")
    order = anyio.run(_fetch_order, order_id)
    log = anyio.run(_send_status_changed, order, "pending_payment", "new")
    assert log.status == "sent"
    assert log.event_type == "status_changed"

    rows = anyio.run(_log_rows_for_order, order_id)
    assert len(rows) == 1
    assert rows[0]["event_type"] == "status_changed"
    assert rows[0]["status"] == "sent"

    list_response = _request("GET", f"/notifications/{order_id}")
    assert list_response.status_code == 200, list_response.text
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["event_type"] == "status_changed"


def test_notifications_unknown_order_returns_empty_list() -> None:
    response = _request("GET", f"/notifications/{uuid.uuid4()}")
    assert response.status_code == 200
    assert response.json() == []


def test_arq_job_retries_then_delivers() -> None:
    """arq-задача повторяется после неудачи и доставляет с третьей попытки."""
    log = anyio.run(_insert_pending_log)
    assert log.status == "pending"
    assert log.attempts == 0

    with pytest.raises(Retry):
        _run_job(log.id, fail=True)
    row = anyio.run(_get_log_by_id, log.id)
    assert row is not None
    assert row.attempts == 1
    assert row.status != "sent"

    with pytest.raises(Retry):
        _run_job(log.id, fail=True)
    row = anyio.run(_get_log_by_id, log.id)
    assert row is not None
    assert row.attempts == 2
    assert row.status != "sent"

    _run_job(log.id, fail=False)
    row = anyio.run(_get_log_by_id, log.id)
    assert row is not None
    assert row.status == "sent"
    assert row.sent_at is not None
    assert row.attempts == 3


def test_arq_job_moves_to_dead_letter_after_max_attempts() -> None:
    """После исчерпания ретраев запись переносится в notification_dead_letter."""
    log = anyio.run(_insert_pending_log)

    with pytest.raises(Retry):
        _run_job(log.id, fail=True)
    with pytest.raises(Retry):
        _run_job(log.id, fail=True)
    _run_job(log.id, fail=True)  # третья неудача — dead-letter, без исключения

    assert anyio.run(_get_log_by_id, log.id) is None
    dead = anyio.run(_dead_letter_rows_for_log, log.id)
    assert len(dead) == 1
    assert dead[0]["attempts"] == 3
    assert dead[0]["last_error"] is not None
    assert "simulated delivery failure" in dead[0]["last_error"]
