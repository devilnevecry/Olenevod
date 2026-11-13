"""Тесты аутентификации (этап 10) на реальной тестовой PostgreSQL.

БД: TEST_DATABASE_URL (postgres:postgres@localhost:5432/olenevod_test).
Зависимость сессии переопределяется на тестовую БД; данные создаются через API,
код верификации читается из БД напрямую (SMTP не используется — simulated).
Каждый тест — sync-функция с anyio.run + httpx.ASGITransport, поэтому сессии
SQLAlchemy и asyncpg-соединения никогда не переплетаются между циклами.
"""

import uuid

import anyio
import asyncpg
import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from olenevod.interfaces.http.auth import get_session as auth_get_session
from olenevod.main import app

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/olenevod_test"

TEST_EMAIL_BASE = "auth-test-{suffix}@example.com"
TEST_NAME = "Тестовый Пользователь"
TEST_PASSWORD = "test-password-123"
WRONG_PASSWORD = "wrong-password-456"

_test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
_test_session_factory = async_sessionmaker(_test_engine, expire_on_commit=False)


async def _override_get_session():
    async with _test_session_factory() as session:
        yield session


app.dependency_overrides[auth_get_session] = _override_get_session


async def _get_latest_code(email: str) -> str | None:
    """Прочитать последний неиспользованный код верификации из БД."""
    conn = await asyncpg.connect(TEST_DATABASE_URL.replace("+asyncpg", ""))
    try:
        row = await conn.fetchrow(
            """
            SELECT code FROM email_verification_codes
            WHERE email = $1 AND used_at IS NULL
            ORDER BY created_at DESC LIMIT 1
            """,
            email,
        )
        return row["code"] if row is not None else None
    finally:
        await conn.close()


async def _user_is_verified(email: str) -> bool:
    conn = await asyncpg.connect(TEST_DATABASE_URL.replace("+asyncpg", ""))
    try:
        row = await conn.fetchrow(
            "SELECT is_verified FROM users WHERE email = $1", email
        )
        return bool(row["is_verified"]) if row is not None else False
    finally:
        await conn.close()


def _unique_email(suffix: str) -> str:
    return TEST_EMAIL_BASE.format(suffix=suffix)


def _request(method: str, path: str, json: dict | None = None) -> httpx.Response:
    async def _run() -> httpx.Response:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            return await client.request(method, path, json=json)

    return anyio.run(_run)


@pytest.fixture(autouse=True)
def _seed_db(alembic_upgrade_head: None) -> None:
    """Применить миграции (alembic upgrade head) перед каждым тестом."""
    pass


def test_register_creates_user_and_code_sent() -> None:
    email = _unique_email(uuid.uuid4().hex[:8])
    response = _request(
        "POST",
        "/auth/register",
        json={"email": email, "name": TEST_NAME, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["email"] == email
    assert body["is_verified"] is False
    assert "simulated" in body["message"]

    # Код должен присутствовать в БД (simulated SMTP)
    code = anyio.run(_get_latest_code, email)
    assert code is not None
    assert len(code) == 6
    assert code.isdigit()


def test_verify_code_success_marks_user_verified() -> None:
    email = _unique_email(uuid.uuid4().hex[:8])
    _request(
        "POST",
        "/auth/register",
        json={"email": email, "name": TEST_NAME, "password": TEST_PASSWORD},
    )
    code = anyio.run(_get_latest_code, email)
    assert code is not None

    response = _request(
        "POST",
        "/auth/verify-code",
        json={"email": email, "code": code},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["email"] == email
    assert body["is_verified"] is True

    assert anyio.run(_user_is_verified, email) is True


def test_verify_code_wrong_code_returns_400() -> None:
    email = _unique_email(uuid.uuid4().hex[:8])
    _request(
        "POST",
        "/auth/register",
        json={"email": email, "name": TEST_NAME, "password": TEST_PASSWORD},
    )

    response = _request(
        "POST",
        "/auth/verify-code",
        json={"email": email, "code": "000000"},
    )
    assert response.status_code == 400, response.text


def test_login_success_returns_token() -> None:
    email = _unique_email(uuid.uuid4().hex[:8])
    _request(
        "POST",
        "/auth/register",
        json={"email": email, "name": TEST_NAME, "password": TEST_PASSWORD},
    )
    code = anyio.run(_get_latest_code, email)
    assert code is not None
    _request(
        "POST",
        "/auth/verify-code",
        json={"email": email, "code": code},
    )

    response = _request(
        "POST",
        "/auth/login",
        json={"email": email, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password_returns_401() -> None:
    email = _unique_email(uuid.uuid4().hex[:8])
    _request(
        "POST",
        "/auth/register",
        json={"email": email, "name": TEST_NAME, "password": TEST_PASSWORD},
    )
    code = anyio.run(_get_latest_code, email)
    assert code is not None
    _request(
        "POST",
        "/auth/verify-code",
        json={"email": email, "code": code},
    )

    response = _request(
        "POST",
        "/auth/login",
        json={"email": email, "password": WRONG_PASSWORD},
    )
    assert response.status_code == 401, response.text


def test_register_duplicate_email_returns_409() -> None:
    email = _unique_email(uuid.uuid4().hex[:8])
    _request(
        "POST",
        "/auth/register",
        json={"email": email, "name": TEST_NAME, "password": TEST_PASSWORD},
    )

    response = _request(
        "POST",
        "/auth/register",
        json={"email": email, "name": TEST_NAME, "password": TEST_PASSWORD},
    )
    assert response.status_code == 409, response.text
