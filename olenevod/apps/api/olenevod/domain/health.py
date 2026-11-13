"""Доменные модели состояния здоровья системы."""

from enum import StrEnum

from pydantic import BaseModel


class HealthStatus(StrEnum):
    ok = "ok"
    error = "error"


class ComponentHealth(BaseModel):
    """Здоровье отдельной компоненты (БД, Redis, миграции)."""

    status: HealthStatus
    detail: str | None = None


class SystemHealth(BaseModel):
    """Здоровье системы в целом."""

    status: HealthStatus
    components: dict[str, ComponentHealth]
