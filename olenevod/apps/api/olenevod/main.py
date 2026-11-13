"""Точка входа API-сервиса (uvicorn olenevod.main:app)."""

from olenevod.interfaces.http.app import app

__all__ = ["app"]
