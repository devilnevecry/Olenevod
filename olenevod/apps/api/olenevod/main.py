"""Точка входа API-сервиса (uvicorn olenevod.main:app)."""

from olenevod.interfaces.http.app import app
from olenevod.interfaces.http.catalog import router as catalog_router

app.include_router(catalog_router)

__all__ = ["app"]
