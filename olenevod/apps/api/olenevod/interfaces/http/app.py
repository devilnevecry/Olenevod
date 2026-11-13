"""Сборка FastAPI-приложения."""

from fastapi import FastAPI

from olenevod.interfaces.http.health import router as health_router

app = FastAPI(
    title="Olenevod API",
    version="0.1.0",
    description="Ядро платформы Olenevod (каталог, заказы, остатки, боты, админка).",
)

app.include_router(health_router)

__all__ = ["app"]
