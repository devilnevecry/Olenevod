"""Сервис проверки готовности системы (liveness / readiness)."""

from collections.abc import Awaitable, Callable

from olenevod.domain.health import ComponentHealth, HealthStatus, SystemHealth

# Проверка компоненты имеет сигнатуру () -> Awaitable[(ok: bool, detail: str | None)].
type ComponentCheck = Callable[[], Awaitable[tuple[bool, str | None]]]


class HealthService:
    """Сервис проверки готовности. Не знает о HTTP и фреймворке."""

    def __init__(
        self,
        db_check: ComponentCheck,
        redis_check: ComponentCheck,
        migrations_check: ComponentCheck,
    ) -> None:
        self._db_check = db_check
        self._redis_check = redis_check
        self._migrations_check = migrations_check

    async def check_liveness(self) -> SystemHealth:
        """Liveness: процесс жив, внешних зависимостей нет."""
        return SystemHealth(status=HealthStatus.ok, components={})

    async def check_readiness(self) -> SystemHealth:
        """Readiness: БД, Redis и применённые миграции."""
        components: dict[str, ComponentHealth] = {}
        overall: HealthStatus = HealthStatus.ok

        for name, check in (
            ("db", self._db_check),
            ("redis", self._redis_check),
            ("migrations", self._migrations_check),
        ):
            ok, detail = await check()
            components[name] = ComponentHealth(
                status=HealthStatus.ok if ok else HealthStatus.error,
                detail=detail,
            )
            if not ok:
                overall = HealthStatus.error

        return SystemHealth(status=overall, components=components)
