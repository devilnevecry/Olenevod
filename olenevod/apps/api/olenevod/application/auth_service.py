"""Сервис аутентификации: регистрация, код верификации e-mail, вход.

Пароли хешируются PBKDF2-HMAC-SHA256 (стандартная библиотека, без внешних зависимостей).
Токены — JWT (PyJWT, HS256, ключ из settings.secret_key).
Отправка кода на e-mail — VERIFIED_SIMULATED (код только сохраняется в БД, SMTP не используется).
ORM-модели User и EmailVerificationCode определены в этом модуле, т.к. этап 10
отвечает только за свои файлы; таблицы создаются миграцией 0006_auth.
"""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from sqlalchemy import DateTime, String, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from olenevod.domain.exceptions import AlreadyExists, DomainError, NotFound
from olenevod.infrastructure.db import Base
from olenevod.settings import settings


class User(Base):
    """Пользователь платформы Olenevod."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class EmailVerificationCode(Base):
    """Одноразовый код верификации e-mail."""

    __tablename__ = "email_verification_codes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AuthService:
    """Аутентификация и верификация пользователей по e-mail коду."""

    CODE_TTL_MINUTES = 10
    CODE_LENGTH = 6
    TOKEN_EXPIRE_HOURS = 24

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ---------- пароли ----------

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), b"olenevod-auth-salt", 100_000
        ).hex()

    @staticmethod
    def _verify_password(password: str, hashed: str) -> bool:
        return (
            hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), b"olenevod-auth-salt", 100_000
            ).hex()
            == hashed
        )

    # ---------- коды верификации ----------

    @staticmethod
    def _generate_code() -> str:
        return f"{secrets.randbelow(10**AuthService.CODE_LENGTH):0{AuthService.CODE_LENGTH}d}"

    async def _invalidate_old_codes(self, email: str) -> None:
        """Пометить все неиспользованные неистёкшие коды для email как использованные."""
        now = datetime.now(UTC)
        result = await self._session.execute(
            select(EmailVerificationCode).where(
                EmailVerificationCode.email == email,
                EmailVerificationCode.used_at.is_(None),
                EmailVerificationCode.expires_at > now,
            )
        )
        for row in result.scalars().all():
            row.used_at = now

    async def _create_verification_code(self, email: str, code: str) -> EmailVerificationCode:
        expires_at = datetime.now(UTC) + timedelta(minutes=self.CODE_TTL_MINUTES)
        row = EmailVerificationCode(
            email=email,
            code=code,
            expires_at=expires_at,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    # ---------- токены ----------

    def _create_token(self, user_id: uuid.UUID) -> str:
        now = datetime.now(UTC)
        payload: dict[str, Any] = {
            "sub": str(user_id),
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=self.TOKEN_EXPIRE_HOURS)).timestamp()),
        }
        return jwt.encode(payload, settings.secret_key, algorithm="HS256")

    # ---------- публичные методы ----------

    async def register(
        self, email: str, name: str, password: str
    ) -> dict[str, Any]:
        """Зарегистрировать пользователя и отправить код верификации (simulated).

        Создаёт запись пользователя с is_verified=false, хеширует пароль,
        генерирует одноразовый код и помечает его в БД. Реальный SMTP не используется.
        """
        existing = await self._session.scalar(select(User).where(User.email == email))
        if existing is not None:
            raise AlreadyExists("user", email)

        user = User(
            email=email,
            name=name,
            hashed_password=self._hash_password(password),
            is_verified=False,
        )
        self._session.add(user)
        await self._session.flush()

        await self._invalidate_old_codes(email)
        code = self._generate_code()
        await self._create_verification_code(email, code)
        await self._session.commit()

        # VERIFIED_SIMULATED: код не отправляется по SMTP, только сохраняется в БД.
        # В продакшене здесь должна быть отправка письма через SMTP.
        return {
            "user_id": user.id,
            "email": user.email,
            "is_verified": user.is_verified,
            "message": "Код верификации отправлен на e-mail (simulated)",
        }

    async def request_code(self, email: str) -> dict[str, Any]:
        """Запросить новый код верификации для существующего пользователя (simulated)."""
        user = await self._session.scalar(select(User).where(User.email == email))
        if user is None:
            raise NotFound("user", email)

        await self._invalidate_old_codes(email)
        code = self._generate_code()
        await self._create_verification_code(email, code)
        await self._session.commit()

        return {"email": email, "message": "Код верификации отправлен (simulated)"}

    async def verify_code(self, email: str, code: str) -> dict[str, Any]:
        """Проверить код верификации и подтвердить e-mail пользователя."""
        now = datetime.now(UTC)
        result = await self._session.execute(
            select(EmailVerificationCode).where(
                EmailVerificationCode.email == email,
                EmailVerificationCode.code == code,
                EmailVerificationCode.used_at.is_(None),
                EmailVerificationCode.expires_at > now,
            )
        )
        code_row = result.scalar_one_or_none()
        if code_row is None:
            raise DomainError(
                "Неверный или истёкший код верификации",
                code="invalid_verification_code",
            )

        code_row.used_at = now
        await self._session.flush()

        user = await self._session.scalar(select(User).where(User.email == email))
        if user is None:
            raise NotFound("user", email)
        user.is_verified = True
        await self._session.commit()

        return {"email": email, "is_verified": True, "message": "E-mail подтверждён"}

    async def login(self, email: str, password: str) -> dict[str, Any]:
        """Войти по e-mail + паролю. Возвращает JWT-токен."""
        user = await self._session.scalar(select(User).where(User.email == email))
        if user is None or not self._verify_password(password, user.hashed_password):
            raise DomainError("Неверный e-mail или пароль", code="invalid_credentials")

        if not user.is_verified:
            raise DomainError("E-mail не подтверждён", code="email_not_verified")

        token = self._create_token(user.id)
        return {"access_token": token, "token_type": "bearer", "user_id": user.id}
