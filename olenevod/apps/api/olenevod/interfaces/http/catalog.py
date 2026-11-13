"""HTTP-роуты каталога: города, категории, продукты с наличием, остатки.

Весь бизнес-логика делегируется CatalogService и PricingService (этап 3);
HTTP-слой только сериализует запросы/ответы и разрешает идентификаторы
городов/категорий/товаров в slug-имена, которые требуют сервисы.
"""

import uuid
from collections.abc import AsyncGenerator, Sequence

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from olenevod.application.catalog_service import CatalogService
from olenevod.application.pricing_service import PricingService
from olenevod.infrastructure.db import async_session
from olenevod.infrastructure.models import (
    Category,
    City,
    CityOffer,
    Product,
    ProductVariant,
    StockLevel,
    Warehouse,
)
from olenevod.infrastructure.repositories import CatalogRepository

router = APIRouter(tags=["catalog"])


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Сессия SQLAlchemy на время одного HTTP-запроса (только чтение)."""
    async with async_session() as session:
        yield session


# ---------- схемы ответов ----------

class CityOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    region: str | None = None


class CategoryOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    parent_id: uuid.UUID | None = None
    children: list["CategoryOut"] = []


class ProductItemOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    category_id: uuid.UUID
    variant_id: uuid.UUID
    sku: str
    variant_name: str
    unit_type: str
    price_kop: int
    old_price_kop: int | None = None
    available_qty: int


class CityStockOut(BaseModel):
    city_id: uuid.UUID
    city_name: str
    available_qty: int


class VariantCardOut(BaseModel):
    id: uuid.UUID
    sku: str
    name: str
    unit_type: str
    price_kop: int
    old_price_kop: int | None = None
    available_by_city: list[CityStockOut] = []


class ProductCardOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    description: str | None = None
    variants: list[VariantCardOut]


class StockOut(BaseModel):
    variant_id: uuid.UUID
    city_id: uuid.UUID
    city_name: str
    available_qty: int


CategoryOut.model_rebuild()


# ---------- helpers ----------

async def _require_city(session: AsyncSession, city_id: uuid.UUID) -> City:
    city = await session.get(City, city_id)
    if city is None:
        raise HTTPException(status_code=404, detail="city not found")
    return city


async def _require_category(session: AsyncSession, category_id: uuid.UUID) -> Category:
    category = await session.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="category not found")
    return category


async def _stock_by_city(
    session: AsyncSession, variant_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[CityStockOut]]:
    """Доступно (on_hand - reserved) по городам для вариантов."""
    if not variant_ids:
        return {}
    stmt = (
        select(
            StockLevel.variant_id,
            City.id.label("city_id"),
            City.name.label("city_name"),
            func.coalesce(func.sum(StockLevel.on_hand - StockLevel.reserved), 0).label(
                "available_qty"
            ),
        )
        .join(Warehouse, Warehouse.id == StockLevel.warehouse_id)
        .join(City, City.id == Warehouse.city_id)
        .where(StockLevel.variant_id.in_(variant_ids))
        .where(City.is_active.is_(True))
        .group_by(StockLevel.variant_id, City.id, City.name)
    )
    rows = (await session.execute(stmt)).all()
    result: dict[uuid.UUID, list[CityStockOut]] = {}
    for row in rows:
        result.setdefault(row.variant_id, []).append(
            CityStockOut(
                city_id=row.city_id,
                city_name=row.city_name,
                available_qty=int(row.available_qty),
            )
        )
    return result


# ---------- роуты ----------

@router.get("/cities", response_model=list[CityOut], summary="Список опубликованных городов")
async def list_cities(
    session: AsyncSession = Depends(get_session),
) -> list[CityOut]:
    service = CatalogService(CatalogRepository(session))
    cities: Sequence[City] = await service.list_cities()
    return [CityOut.model_validate(city, from_attributes=True) for city in cities]


@router.get(
    "/categories",
    response_model=list[CategoryOut],
    summary="Дерево опубликованных категорий",
)
async def list_categories(
    session: AsyncSession = Depends(get_session),
) -> list[CategoryOut]:
    service = CatalogService(CatalogRepository(session))
    items: Sequence[Category] = await service.list_categories(published_only=True)
    nodes: dict[uuid.UUID, CategoryOut] = {
        category.id: CategoryOut.model_validate(category, from_attributes=True)
        for category in items
    }
    roots: list[CategoryOut] = []
    for node in nodes.values():
        if node.parent_id is None:
            roots.append(node)
        else:
            parent = nodes.get(node.parent_id)
            if parent is not None:
                parent.children.append(node)
    return roots


@router.get(
    "/products",
    response_model=list[ProductItemOut],
    summary="Продукты города с наличием",
)
async def list_products(
    city_id: uuid.UUID,
    category_id: uuid.UUID | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[ProductItemOut]:
    city = await _require_city(session, city_id)
    category_slug: str | None = None
    if category_id is not None:
        category = await _require_category(session, category_id)
        category_slug = category.slug

    service = CatalogService(CatalogRepository(session))
    page = offset // limit + 1
    items, _total = await service.list_products(
        city.slug,
        category_slug=category_slug,
        q=search,
        page=page,
        page_size=limit,
    )
    return [
        ProductItemOut(
            id=row["product"].id,
            slug=row["product"].slug,
            name=row["product"].name,
            category_id=row["product"].category_id,
            variant_id=row["variant"].id,
            sku=row["variant"].sku,
            variant_name=row["variant"].name,
            unit_type=str(row["variant"].unit_type),
            price_kop=row["offer"].price_kop,
            old_price_kop=row["offer"].old_price_kop,
            available_qty=int(row["available_qty"]),
        )
        for row in items
    ]


@router.get(
    "/products/{product_id}",
    response_model=ProductCardOut,
    summary="Карточка товара с вариантами и наличием по городам",
)
async def get_product(
    product_id: uuid.UUID,
    city_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> ProductCardOut:
    product = await session.get(Product, product_id)
    if product is None or product.deleted_at is not None or not product.is_published:
        raise HTTPException(status_code=404, detail="product not found")
    city = await _require_city(session, city_id)

    service = CatalogService(CatalogRepository(session))
    card = await service.get_product(city.slug, product.slug)
    if card is None:
        raise HTTPException(status_code=404, detail="product not found in city")

    pricing = PricingService(CatalogRepository(session))
    variant_ids = [entry["variant"].id for entry in card["variants"]]
    stock_by_city = await _stock_by_city(session, variant_ids)

    variants: list[VariantCardOut] = []
    for entry in card["variants"]:
        variant: ProductVariant = entry["variant"]
        offer: CityOffer = entry["offer"]
        unit_price = await pricing.unit_price(city.id, variant.id)
        variants.append(
            VariantCardOut(
                id=variant.id,
                sku=variant.sku,
                name=variant.name,
                unit_type=str(variant.unit_type),
                price_kop=unit_price,
                old_price_kop=offer.old_price_kop,
                available_by_city=stock_by_city.get(variant.id, []),
            )
        )
    return ProductCardOut(
        id=product.id,
        slug=product.slug,
        name=product.name,
        description=product.description,
        variants=variants,
    )


@router.get(
    "/stock",
    response_model=list[StockOut],
    summary="Остатки по городам для вариантов",
)
async def stock(
    variant_ids: list[uuid.UUID] = Query([]),
    session: AsyncSession = Depends(get_session),
) -> list[StockOut]:
    by_city = await _stock_by_city(session, list(variant_ids))
    return [
        StockOut(
            variant_id=variant_id,
            city_id=item.city_id,
            city_name=item.city_name,
            available_qty=item.available_qty,
        )
        for variant_id, items in by_city.items()
        for item in items
    ]
