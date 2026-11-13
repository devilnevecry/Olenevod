"""Catalog service: cities, categories, city products with availability."""

from collections.abc import Sequence
from typing import Any

from olenevod.infrastructure.models import Category, City
from olenevod.infrastructure.repositories import CatalogRepository


class CatalogService:
    """Application use-cases for the catalog. Knows nothing about HTTP or the DB schema directly."""

    def __init__(self, catalog_repo: CatalogRepository) -> None:
        self._repo = catalog_repo

    async def list_cities(self) -> Sequence[City]:
        """List active cities."""
        return await self._repo.list_cities()

    async def get_city(self, slug: str) -> City:
        """City by slug or NotFound."""
        return await self._repo.require_city(slug)

    async def list_categories(self, published_only: bool = True) -> Sequence[Category]:
        """List categories."""
        return await self._repo.list_categories(published_only=published_only)

    async def list_products(
        self,
        city_slug: str,
        *,
        category_slug: str | None = None,
        q: str | None = None,
        in_stock: bool | None = None,
        sort: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """City products with availability: (items, total)."""
        return await self._repo.list_products(
            city_slug,
            category_slug=category_slug,
            q=q,
            in_stock=in_stock,
            sort=sort,
            page=page,
            page_size=page_size,
        )

    async def get_product(self, city_slug: str, product_slug: str) -> dict[str, Any] | None:
        """Product card in a city."""
        return await self._repo.get_product(city_slug, product_slug)
