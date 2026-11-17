"""HTTP-роуты аутентификации: регистрация, код верификации, вход.

Бизнес-логика delegated to AuthService (этап 10); HTTP-слой только
сериализует запрос/ответ и транслирует доменные исключения в HTTP-статусы.
"""

import uuid
from collections.abc import AsyncGenerator
from typing import Any

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from olenevod.application.auth_service import AuthService
from olenevod.domain.exceptions import AlreadyExists, DomainError, NotFound
from olenevod.infrastructure.db import async_session
from olenevod.settings import settings

router = APIRouter(tags=["auth"])

# ---------- rate limiting на попытки входа (Redis) ----------

_RATE_LIMIT_REDIS = aioredis.from_url(
    settings.redis_url,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)

RATE_LIMIT_PREFIX = "rate_limit:login:"
RATE_LIMIT_MAX_ATTEMPTS = 5
RATE_LIMIT_TTL_SECONDS = 900  # 15 минут


async def _increment_failed_attempts(email: str) -> None:
    """Инкремент счётчика неудачных попыток входа для email."""
    try:
        pipe = _RATE_LIMIT_REDIS.pipeline()
        pipe.incr(f"{RATE_LIMIT_PREFIX}{email}")
        pipe.expire(f"{RATE_LIMIT_PREFIX}{email}", RATE_LIMIT_TTL_SECONDS)
        await pipe.execute()
    except Exception:
        pass


async def _get_failed_attempts(email: str) -> int:
    """Получение текущего количества неудачных попыток для email."""
    try:
        count = await _RATE_LIMIT_REDIS.get(f"{RATE_LIMIT_PREFIX}{email}")
        return int(count) if count else 0
    except Exception:
        return 0


async def _reset_failed_attempts(email: str) -> None:
    """Сброс счётчика неудачных попыток после успешного входа."""
    try:
        await _RATE_LIMIT_REDIS.delete(f"{RATE_LIMIT_PREFIX}{email}")
    except Exception:
        pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Сессия SQLAlchemy на время одного HTTP-запроса."""
    async with async_session() as session:
        yield session


# ---------- схемы запроса/ответа ----------

class RegisterIn(BaseModel):
    email: str = Field(..., min_length=1, description="E-mail пользователя")
    name: str = Field(..., min_length=1, description="Имя пользователя")
    password: str = Field(..., min_length=1, description="Пароль")


class RegisterOut(BaseModel):
    user_id: uuid.UUID
    email: str
    is_verified: bool
    message: str


class RequestCodeIn(BaseModel):
    email: str = Field(..., min_length=1, description="E-mail пользователя")


class RequestCodeOut(BaseModel):
    email: str
    message: str


class VerifyCodeIn(BaseModel):
    email: str = Field(..., min_length=1, description="E-mail пользователя")
    code: str = Field(..., min_length=1, description="Код верификации")


class VerifyCodeOut(BaseModel):
    email: str
    is_verified: bool
    message: str


class LoginIn(BaseModel):
    email: str = Field(..., min_length=1, description="E-mail пользователя")
    password: str = Field(..., min_length=1, description="Пароль")


class LoginOut(BaseModel):
    access_token: str
    token_type: str
    user_id: uuid.UUID


# ---------- роуты ----------

@router.post(
    "/auth/register",
    response_model=RegisterOut,
    summary="Регистрация пользователя с отправкой кода верификации (simulated)",
)
async def register(
    data: RegisterIn,
    session: AsyncSession = Depends(get_session),
) -> RegisterOut:
    service = AuthService(session)
    try:
        result: dict[str, Any] = await service.register(data.email, data.name, data.password)
    except AlreadyExists as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from exc
    return RegisterOut(
        user_id=result["user_id"],
        email=result["email"],
        is_verified=result["is_verified"],
        message=result["message"],
    )


@router.post(
    "/auth/request-code",
    response_model=RequestCodeOut,
    summary="Запросить повторный код верификации (simulated)",
)
async def request_code(
    data: RequestCodeIn,
    session: AsyncSession = Depends(get_session),
) -> RequestCodeOut:
    service = AuthService(session)
    try:
        result: dict[str, Any] = await service.request_code(data.email)
    except NotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return RequestCodeOut(email=result["email"], message=result["message"])


@router.post(
    "/auth/verify-code",
    response_model=VerifyCodeOut,
    summary="Подтвердить e-mail кодом верификации",
)
async def verify_code(
    data: VerifyCodeIn,
    session: AsyncSession = Depends(get_session),
) -> VerifyCodeOut:
    service = AuthService(session)
    try:
        result: dict[str, Any] = await service.verify_code(data.email, data.code)
    except NotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except DomainError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    return VerifyCodeOut(
        email=result["email"],
        is_verified=result["is_verified"],
        message=result["message"],
    )


@router.post(
    "/auth/login",
    response_model=LoginOut,
    summary="Вход по e-mail и паролю. Возвращает JWT-токен.",
)
async def login(
    data: LoginIn,
    session: AsyncSession = Depends(get_session),
) -> LoginOut:
    service = AuthService(session)
    try:
        result: dict[str, Any] = await service.login(data.email, data.password)
    except DomainError as exc:
        count = await _get_failed_attempts(data.email)
        if count >= RATE_LIMIT_MAX_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Слишком много неудачных попыток входа. Попробуйте позже.",
            ) from exc
        await _increment_failed_attempts(data.email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc
    await _reset_failed_attempts(data.email)
    return LoginOut(
        access_token=result["access_token"],
        token_type=result["token_type"],
        user_id=result["user_id"],
    )
