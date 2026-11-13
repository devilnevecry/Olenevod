"""Зависимости HTTP-слоя: сборка прикладных сервисов."""

from olenevod.application.health import HealthService
from olenevod.infrastructure.db import check_db
from olenevod.infrastructure.migrations import check_migrations
from olenevod.infrastructure.redis import check_redis


def get_health_service() -> HealthService:
    return HealthService(
        db_check=check_db,
        redis_check=check_redis,
        migrations_check=check_migrations,
    )
