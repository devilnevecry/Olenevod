"""Репозиторий каталога (города, категории, товары с наличием по городу)."""

import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from olenevod.domain.exceptions import NotFound
from olenevod.infrastructure.models import (
    Category,
    City,
    CityOffer,
    Product,
    ProductVariant,
    StockLevel,
)


class CatalogRepository:
    """Чтение каталога. Все запросы scoped к выбранному городу."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_cities(self) -> Sequence[City]:
        """Список активных городов."""
        result = await self._session.execute(
            select(City).where(City.is_active.is_(True)).order_by(asc(City.name))
        )
        return result.scalars().all()

    async def get_city_by_slug(self, slug: str) -> City | None:
        """Город по slug."""
        result = await self._session.execute(select(City).where(City.slug == slug))
        return result.scalars().first()

    async def require_city(self, slug: str) -> City:
        """Город по slug или NotFound."""
        city = await self.get_city_by_slug(slug)
        if city is None:
            raise NotFound("city", slug)
        return city

    async def list_categories(self, published_only: bool = True) -> Sequence[Category]:
        """Список категорий (опционально только опубликованные)."""
        stmt = select(Category).where(
            Category.deleted_at.is_(None)
        ).order_by(asc(Category.sort), asc(Category.name))
        if published_only:
            stmt = stmt.where(Category.is_published.is_(True))
        result = await self._session.execute(stmt)
        return result.scalars().all()

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
        """Товары города с наличием.

        Возвращает (items, total). Каждый item — словарь с полями товара,
        варианта, предложения города и вычисленным available_qty.
        """
        city = await self.require_city(city_slug)

        available_expr = (
            func.coalesce(func.sum(StockLevel.on_hand - StockLevel.reserved), 0)
        ).label("available_qty")

        stmt = (
            select(
                Product,
                ProductVariant,
                CityOffer,
                available_expr,
            )
            .select_from(CityOffer)
            .join(City, City.id == CityOffer.city_id)
            .join(ProductVariant, ProductVariant.id == CityOffer.variant_id)
            .join(Product, Product.id == ProductVariant.product_id)
            .outerjoin(
                StockLevel,
                StockLevel.variant_id == ProductVariant.id,
            )
            .where(City.id == city.id)
            .where(CityOffer.is_published.is_(True))
            .where(Product.deleted_at.is_(None))
            .where(Product.is_published.is_(True))
            .where(ProductVariant.deleted_at.is_(None))
            .group_by(Product.id, ProductVariant.id, CityOffer.id)
        )

        if category_slug:
            stmt = stmt.where(Product.category_id.in_(
                select(Category.id).where(Category.slug == category_slug)
            ))
        if q:
            pattern = f"%{q}%"
            stmt = stmt.where(or_(
                Product.name.ilike(pattern),
                ProductVariant.name.ilike(pattern),
                ProductVariant.sku.ilike(pattern),
            ))
        if in_stock is True:
            stmt = stmt.having(available_expr > 0)
        elif in_stock is False:
            stmt = stmt.having(available_expr <= 0)

        if sort == "price_asc":
            stmt = stmt.order_by(asc(CityOffer.price_kop))
        elif sort == "price_desc":
            stmt = stmt.order_by(desc(CityOffer.price_kop))
        elif sort == "name":
            stmt = stmt.order_by(asc(Product.name))
        else:
            stmt = stmt.order_by(desc(Product.created_at))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self._session.execute(count_stmt)
        total = int(total_result.scalar_one())

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self._session.execute(stmt)
        rows = result.all()

        items: list[dict[str, Any]] = [
            {
                "product": product,
                "variant": variant,
                "offer": offer,
                "available_qty": int(available or 0),
            }
            for product, variant, offer, available in rows
        ]
        return items, total

    async def get_city_offer(
        self, city_id: uuid.UUID, variant_id: uuid.UUID
    ) -> CityOffer | None:
        """Предложение города для варианта (цена, лимиты)."""
        result = await self._session.execute(
            select(CityOffer).where(
                CityOffer.city_id == city_id,
                CityOffer.variant_id == variant_id,
                CityOffer.is_published.is_(True),
            )
        )
        return result.scalars().first()

    async def get_product(self, city_slug: str, product_slug: str) -> dict[str, Any] | None:
        """Карточка товара в городе с наличием вариантов."""
        city = await self.require_city(city_slug)

        stmt = (
            select(Product, ProductVariant, CityOffer)
            .select_from(Product)
            .join(ProductVariant, ProductVariant.product_id == Product.id)
            .join(CityOffer, (CityOffer.variant_id == ProductVariant.id) & (CityOffer.city_id == city.id))
            .where(Product.slug == product_slug)
            .where(Product.deleted_at.is_(None))
            .where(Product.is_published.is_(True))
            .where(CityOffer.is_published.is_(True))
            .where(ProductVariant.deleted_at.is_(None))
            .order_by(ProductVariant.name)
        )
        result = await self._session.execute(stmt)
        rows = result.all()
        if not rows:
            return None
        product = rows[0][0]
        variants: list[dict[str, Any]] = [
            {
                "variant": variant,
                "offer": offer,
                "available_qty": 0,
            }
            for _, variant, offer in rows
        ]
        return {"product": product, "variants": variants}
