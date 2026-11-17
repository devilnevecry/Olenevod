"""Сборка FastAPI-приложения."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from olenevod.interfaces.http.admin import router as admin_router
from olenevod.interfaces.http.auth import router as auth_router
from olenevod.interfaces.http.catalog import router as catalog_router
from olenevod.interfaces.http.delivery import router as delivery_router
from olenevod.interfaces.http.health import router as health_router
from olenevod.interfaces.http.notifications import router as notifications_router
from olenevod.interfaces.http.orders import router as orders_router
from olenevod.interfaces.http.payments import router as payments_router

app = FastAPI(
    title="Olenevod API",
    version="0.1.0",
    description="Ядро платформы Olenevod (каталог, заказы, остатки, боты, админка).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(catalog_router)
app.include_router(delivery_router)
app.include_router(notifications_router)
app.include_router(orders_router)
app.include_router(payments_router)

__all__ = ["app"]
