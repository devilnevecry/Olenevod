"""Настройки приложения Olenevod (pydantic-settings).

Все значения берутся из переменных окружения. Значения по умолчанию —
разработческие, приложение импортируется и запускается даже без реальных
секретов (готность к продакшену проверяется `make release-check`).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_mode: str = "demo"

    database_url: str = "postgresql+asyncpg://olenevod:olenevod_dev@localhost:5432/olenevod"
    redis_url: str = "redis://localhost:6379/0"

    secret_key: str = "dev-secret-change-me-in-production"

    bot_token_telegram: str | None = None
    bot_token_vk: str | None = None
    bot_token_max: str | None = None

    smtp_host: str = "localhost"
    smtp_port: int = 25
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "noreply@olenevod.local"

    payment_provider: str = "yukassa"
    payment_provider_secret_key: str | None = None
    payment_provider_shop_id: str | None = None

    yandex_metrika_id: str | None = None

    api_port: int = 8000
    web_port: int = 3000
    admin_port: int = 5173


settings = Settings()
