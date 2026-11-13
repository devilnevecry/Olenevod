"""HTTP-роутеры эндпоинтов здоровья: /healthz и /readyz."""

from fastapi import APIRouter, Depends, HTTPException

from olenevod.application.health import HealthService
from olenevod.domain.health import HealthStatus
from olenevod.interfaces.http.deps import get_health_service

router = APIRouter(tags=["health"])


@router.get("/healthz", summary="Liveness — процесс жив")
async def healthz(service: HealthService = Depends(get_health_service)) -> dict:
    """Liveness. Отвечает 200, если процесс работает. Без проверки БД/Redis."""
    health = await service.check_liveness()
    return health.model_dump()


@router.get("/readyz", summary="Readiness — БД, Redis, миграции")
async def readyz(service: HealthService = Depends(get_health_service)) -> dict:
    """Readiness. 200 если БД, Redis и миграции в порядке, иначе 503."""
    health = await service.check_readiness()
    if health.status != HealthStatus.ok:
        raise HTTPException(status_code=503, detail=health.model_dump())
    return health.model_dump()
