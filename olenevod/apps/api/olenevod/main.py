"""Точка входа API-сервиса (uvicorn olenevod.main:app)."""

from olenevod.interfaces.http.app import app
from olenevod.interfaces.http.catalog import router as catalog_router
from olenevod.interfaces.http.orders import router as orders_router
from olenevod.interfaces.http.payments import router as payments_router

app.include_router(catalog_router)
app.include_router(orders_router)
app.include_router(payments_router)

__all__ = ["app"]
