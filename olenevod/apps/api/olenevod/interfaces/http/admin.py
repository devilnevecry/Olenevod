"""HTTP-роуты админ-панели: CRUD для 11 разделов (cities, warehouses, products,
variants, offers, stock, transfers, routes, carriers, orders, customers).

Строгая авторизация: без валидного JWT — HTTP 401 (флага is_admin нет,
достаточно любого аутентифицированного пользователя, этап 1.k).
Бизнес-логика делегируется AdminService; HTTP-слой только сериализует
запросы/ответы и транслирует ошибки ограничений БД в 400.

Моделей `routes` и `carriers` в ORM пока нет (вне моих путей); их endpoints
на месте, но возвращают 501 до добавления таблиц.
"""

import uuid
from collections.abc import AsyncGenerator
from typing import Any

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from olenevod.application.admin_service import AdminService, uuid_id
from olenevod.application.auth_service import User
from olenevod.infrastructure.db import async_session
from olenevod.settings import settings

router = APIRouter(prefix="/admin", tags=["admin"])


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Сессия SQLAlchemy на время одного HTTP-запроса (чтение и запись)."""
    async with async_session() as session:
        yield session


async def get_admin_user(
    session: AsyncSession = Depends(get_session),
    authorization: str | None = Header(default=None),
) -> User:
    """Текущий пользователь из JWT (строго: без токена/невалидный — HTTP 401).

    Использует сессию запроса админ-роутера, поэтому не тянет за собой
    сессию и базу пользователей из роутов заказов.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="authentication required")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.secret_key, algorithms=["HS256"]
        )
    except Exception:
        raise HTTPException(status_code=401, detail="invalid token") from None
    sub = payload.get("sub")
    if not isinstance(sub, str):
        raise HTTPException(status_code=401, detail="invalid token")
    try:
        user_id = uuid.UUID(sub)
    except ValueError:
        raise HTTPException(status_code=401, detail="invalid token") from None
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="user not found")
    return user


# Моделей routes/carriers пока нет в ORM (миграции до 0007, модели не добавлены — вне моих путей).
# Когда таблицы pojawятся, здесь нужно импортировать модели Route и Carrier:
#   from olenevod.infrastructure.models import Route as _Route, Carrier as _Carrier
# Пока оба раздела возвращают 501.
_Route: Any = None
_Carrier: Any = None


def _require_model(model: Any, name: str) -> Any:
    if model is None:
        raise HTTPException(
            status_code=501, detail=f"table {name} is not available in ORM yet"
        )
    return model


# ---------- схемы ----------

class CityIn(BaseModel):
    slug: str | None = Field(default=None, max_length=100)
    name: str | None = Field(default=None, max_length=255)
    region: str | None = Field(default=None, max_length=255)
    timezone: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None


class CityOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    region: str | None = None
    timezone: str | None = None
    is_active: bool


class WarehouseIn(BaseModel):
    city_id: uuid.UUID | None = None
    name: str | None = Field(default=None, max_length=255)
    address: str | None = None
    is_active: bool | None = None


class WarehouseOut(BaseModel):
    id: uuid.UUID
    city_id: uuid.UUID
    name: str
    address: str | None = None
    is_active: bool


class ProductIn(BaseModel):
    category_id: uuid.UUID | None = None
    slug: str | None = Field(default=None, max_length=200)
    name: str | None = Field(default=None, max_length=255)
    short_description: str | None = None
    description: str | None = None
    is_published: bool | None = None
    is_demo: bool | None = None


class ProductOut(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID
    slug: str
    name: str
    short_description: str | None = None
    description: str | None = None
    is_published: bool
    is_demo: bool


class VariantIn(BaseModel):
    product_id: uuid.UUID | None = None
    sku: str | None = Field(default=None, max_length=100)
    name: str | None = Field(default=None, max_length=255)
    unit_type: str | None = Field(default=None, max_length=32)
    pack_weight_g: int | None = None
    barcode: str | None = Field(default=None, max_length=100)


class VariantOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    sku: str
    name: str
    unit_type: str
    pack_weight_g: int | None = None
    barcode: str | None = None


class OfferIn(BaseModel):
    city_id: uuid.UUID | None = None
    variant_id: uuid.UUID | None = None
    price_kop: int | None = None
    old_price_kop: int | None = None
    is_published: bool | None = None
    min_qty: int | None = None
    step_qty: int | None = None
    max_qty_per_order: int | None = None


class OfferOut(BaseModel):
    id: uuid.UUID
    city_id: uuid.UUID
    variant_id: uuid.UUID
    price_kop: int
    old_price_kop: int | None = None
    is_published: bool
    min_qty: int
    step_qty: int
    max_qty_per_order: int | None = None


class StockIn(BaseModel):
    on_hand: int | None = None
    reserved: int | None = None


class StockOut(BaseModel):
    warehouse_id: uuid.UUID
    variant_id: uuid.UUID
    on_hand: int
    reserved: int


class TransferIn(BaseModel):
    from_warehouse_id: uuid.UUID | None = None
    to_warehouse_id: uuid.UUID | None = None
    status: str | None = Field(default=None, max_length=32)
    route_id: uuid.UUID | None = None
    carrier_id: uuid.UUID | None = None


class TransferOut(BaseModel):
    id: uuid.UUID
    from_warehouse_id: uuid.UUID
    to_warehouse_id: uuid.UUID
    status: str
    route_id: uuid.UUID | None = None
    carrier_id: uuid.UUID | None = None


class TransferItemIn(BaseModel):
    variant_id: uuid.UUID | None = None
    qty: int | None = None
    received_qty: int | None = None


class TransferItemOut(BaseModel):
    transfer_id: uuid.UUID
    variant_id: uuid.UUID
    qty: int
    received_qty: int | None = None


class RouteIn(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    carrier_id: uuid.UUID | None = None
    from_city_id: uuid.UUID | None = None
    to_city_id: uuid.UUID | None = None
    duration_hours: int | None = None
    price_kop: int | None = None
    is_active: bool | None = None


class RouteOut(BaseModel):
    id: uuid.UUID
    name: str | None = None
    carrier_id: uuid.UUID | None = None
    from_city_id: uuid.UUID | None = None
    to_city_id: uuid.UUID | None = None
    duration_hours: int | None = None
    price_kop: int | None = None
    is_active: bool


class CarrierIn(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=254)
    is_active: bool | None = None


class CarrierOut(BaseModel):
    id: uuid.UUID
    name: str
    phone: str | None = None
    email: str | None = None
    is_active: bool


class OrderStatusIn(BaseModel):
    status: str = Field(max_length=64)


class OrderOut(BaseModel):
    id: uuid.UUID
    city_id: uuid.UUID
    customer_name: str
    customer_phone: str
    status: str
    total_amount: int


class CustomerIn(BaseModel):
    phone: str | None = Field(default=None, max_length=32)
    name: str | None = Field(default=None, max_length=255)


class CustomerOut(BaseModel):
    id: uuid.UUID
    email: str
    phone: str | None = None
    name: str
    is_verified: bool


# ---------- города ----------

@router.get(
    "/cities",
    response_model=list[CityOut],
    summary="Список городов",
)
async def list_cities(
    offset: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> list[CityOut]:
    service = AdminService(session)
    rows = await service.list_cities(offset=offset, limit=limit)
    return [CityOut.model_validate(row, from_attributes=True) for row in rows]


@router.get(
    "/cities/{city_id}",
    response_model=CityOut,
    summary="Карточка города",
)
async def get_city(
    city_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> CityOut:
    service = AdminService(session)
    row = await service.get_city(str(city_id))
    if row is None:
        raise HTTPException(status_code=404, detail="city not found")
    return CityOut.model_validate(row, from_attributes=True)


@router.post(
    "/cities",
    status_code=201,
    response_model=CityOut,
    summary="Создать город",
)
async def create_city(
    data: CityIn,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> CityOut:
    service = AdminService(session)
    try:
        row = await service.create_city(data.model_dump(exclude_unset=True))
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    return CityOut.model_validate(row, from_attributes=True)


@router.patch(
    "/cities/{city_id}",
    response_model=CityOut,
    summary="Обновить город",
)
async def update_city(
    city_id: uuid.UUID,
    data: CityIn,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> CityOut:
    service = AdminService(session)
    try:
        row = await service.update_city(str(city_id), data.model_dump(exclude_unset=True))
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    if row is None:
        raise HTTPException(status_code=404, detail="city not found")
    return CityOut.model_validate(row, from_attributes=True)


@router.delete(
    "/cities/{city_id}",
    summary="Удалить город",
)
async def delete_city(
    city_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> dict[str, bool]:
    service = AdminService(session)
    try:
        ok = await service.delete_city(str(city_id))
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    if not ok:
        raise HTTPException(status_code=404, detail="city not found")
    return {"deleted": True}


# ---------- склады ----------

@router.get(
    "/warehouses",
    response_model=list[WarehouseOut],
    summary="Список складов",
)
async def list_warehouses(
    offset: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> list[WarehouseOut]:
    service = AdminService(session)
    rows = await service.list_warehouses(offset=offset, limit=limit)
    return [WarehouseOut.model_validate(row, from_attributes=True) for row in rows]


@router.get(
    "/warehouses/{warehouse_id}",
    response_model=WarehouseOut,
    summary="Карточка склада",
)
async def get_warehouse(
    warehouse_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> WarehouseOut:
    service = AdminService(session)
    row = await service.get_warehouse(str(warehouse_id))
    if row is None:
        raise HTTPException(status_code=404, detail="warehouse not found")
    return WarehouseOut.model_validate(row, from_attributes=True)


@router.post(
    "/warehouses",
    status_code=201,
    response_model=WarehouseOut,
    summary="Создать склад",
)
async def create_warehouse(
    data: WarehouseIn,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> WarehouseOut:
    service = AdminService(session)
    try:
        row = await service.create_warehouse(data.model_dump(exclude_unset=True))
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    return WarehouseOut.model_validate(row, from_attributes=True)


@router.patch(
    "/warehouses/{warehouse_id}",
    response_model=WarehouseOut,
    summary="Обновить склад",
)
async def update_warehouse(
    warehouse_id: uuid.UUID,
    data: WarehouseIn,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> WarehouseOut:
    service = AdminService(session)
    try:
        row = await service.update_warehouse(
            str(warehouse_id), data.model_dump(exclude_unset=True)
        )
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    if row is None:
        raise HTTPException(status_code=404, detail="warehouse not found")
    return WarehouseOut.model_validate(row, from_attributes=True)


@router.delete(
    "/warehouses/{warehouse_id}",
    summary="Удалить склад",
)
async def delete_warehouse(
    warehouse_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> dict[str, bool]:
    service = AdminService(session)
    try:
        ok = await service.delete_warehouse(str(warehouse_id))
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    if not ok:
        raise HTTPException(status_code=404, detail="warehouse not found")
    return {"deleted": True}


# ---------- товары ----------

@router.get(
    "/products",
    response_model=list[ProductOut],
    summary="Список товаров",
)
async def list_products(
    offset: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> list[ProductOut]:
    service = AdminService(session)
    rows = await service.list_products(offset=offset, limit=limit)
    return [ProductOut.model_validate(row, from_attributes=True) for row in rows]


@router.get(
    "/products/{product_id}",
    response_model=ProductOut,
    summary="Карточка товара",
)
async def get_product(
    product_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> ProductOut:
    service = AdminService(session)
    row = await service.get_product(str(product_id))
    if row is None:
        raise HTTPException(status_code=404, detail="product not found")
    return ProductOut.model_validate(row, from_attributes=True)


@router.post(
    "/products",
    status_code=201,
    response_model=ProductOut,
    summary="Создать товар",
)
async def create_product(
    data: ProductIn,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> ProductOut:
    service = AdminService(session)
    try:
        row = await service.create_product(data.model_dump(exclude_unset=True))
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    return ProductOut.model_validate(row, from_attributes=True)


@router.patch(
    "/products/{product_id}",
    response_model=ProductOut,
    summary="Обновить товар",
)
async def update_product(
    product_id: uuid.UUID,
    data: ProductIn,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> ProductOut:
    service = AdminService(session)
    try:
        row = await service.update_product(
            str(product_id), data.model_dump(exclude_unset=True)
        )
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    if row is None:
        raise HTTPException(status_code=404, detail="product not found")
    return ProductOut.model_validate(row, from_attributes=True)


@router.delete(
    "/products/{product_id}",
    summary="Удалить товар",
)
async def delete_product(
    product_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> dict[str, bool]:
    service = AdminService(session)
    try:
        ok = await service.delete_product(str(product_id))
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    if not ok:
        raise HTTPException(status_code=404, detail="product not found")
    return {"deleted": True}


# ---------- варианты ----------

@router.get(
    "/variants",
    response_model=list[VariantOut],
    summary="Список вариантов товара",
)
async def list_variants(
    offset: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> list[VariantOut]:
    service = AdminService(session)
    rows = await service.list_variants(offset=offset, limit=limit)
    return [VariantOut.model_validate(row, from_attributes=True) for row in rows]


@router.get(
    "/variants/{variant_id}",
    response_model=VariantOut,
    summary="Карточка варианта",
)
async def get_variant(
    variant_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> VariantOut:
    service = AdminService(session)
    row = await service.get_variant(str(variant_id))
    if row is None:
        raise HTTPException(status_code=404, detail="variant not found")
    return VariantOut.model_validate(row, from_attributes=True)


@router.post(
    "/variants",
    status_code=201,
    response_model=VariantOut,
    summary="Создать вариант",
)
async def create_variant(
    data: VariantIn,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> VariantOut:
    service = AdminService(session)
    try:
        row = await service.create_variant(data.model_dump(exclude_unset=True))
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    return VariantOut.model_validate(row, from_attributes=True)


@router.patch(
    "/variants/{variant_id}",
    response_model=VariantOut,
    summary="Обновить вариант",
)
async def update_variant(
    variant_id: uuid.UUID,
    data: VariantIn,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> VariantOut:
    service = AdminService(session)
    try:
        row = await service.update_variant(
            str(variant_id), data.model_dump(exclude_unset=True)
        )
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    if row is None:
        raise HTTPException(status_code=404, detail="variant not found")
    return VariantOut.model_validate(row, from_attributes=True)


@router.delete(
    "/variants/{variant_id}",
    summary="Удалить вариант",
)
async def delete_variant(
    variant_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> dict[str, bool]:
    service = AdminService(session)
    try:
        ok = await service.delete_variant(str(variant_id))
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    if not ok:
        raise HTTPException(status_code=404, detail="variant not found")
    return {"deleted": True}


# ---------- предложения города ----------

@router.get(
    "/offers",
    response_model=list[OfferOut],
    summary="Список предложений города",
)
async def list_offers(
    offset: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> list[OfferOut]:
    service = AdminService(session)
    rows = await service.list_offers(offset=offset, limit=limit)
    return [OfferOut.model_validate(row, from_attributes=True) for row in rows]


@router.get(
    "/offers/{offer_id}",
    response_model=OfferOut,
    summary="Карточка предложения города",
)
async def get_offer(
    offer_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> OfferOut:
    service = AdminService(session)
    row = await service.get_offer(str(offer_id))
    if row is None:
        raise HTTPException(status_code=404, detail="offer not found")
    return OfferOut.model_validate(row, from_attributes=True)


@router.post(
    "/offers",
    status_code=201,
    response_model=OfferOut,
    summary="Создать предложение города",
)
async def create_offer(
    data: OfferIn,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> OfferOut:
    service = AdminService(session)
    try:
        row = await service.create_offer(data.model_dump(exclude_unset=True))
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    return OfferOut.model_validate(row, from_attributes=True)


@router.patch(
    "/offers/{offer_id}",
    response_model=OfferOut,
    summary="Обновить предложение города",
)
async def update_offer(
    offer_id: uuid.UUID,
    data: OfferIn,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> OfferOut:
    service = AdminService(session)
    try:
        row = await service.update_offer(
            str(offer_id), data.model_dump(exclude_unset=True)
        )
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    if row is None:
        raise HTTPException(status_code=404, detail="offer not found")
    return OfferOut.model_validate(row, from_attributes=True)


@router.delete(
    "/offers/{offer_id}",
    summary="Удалить предложение города",
)
async def delete_offer(
    offer_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> dict[str, bool]:
    service = AdminService(session)
    try:
        ok = await service.delete_offer(str(offer_id))
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    if not ok:
        raise HTTPException(status_code=404, detail="offer not found")
    return {"deleted": True}


# ---------- остатки ----------

@router.get(
    "/stock",
    response_model=list[StockOut],
    summary="Список остатков",
)
async def list_stock(
    offset: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> list[StockOut]:
    service = AdminService(session)
    rows = await service.list_stock(offset=offset, limit=limit)
    return [StockOut.model_validate(row, from_attributes=True) for row in rows]


@router.get(
    "/stock/{warehouse_id}/{variant_id}",
    response_model=StockOut,
    summary="Карточка остатка",
)
async def get_stock(
    warehouse_id: uuid.UUID,
    variant_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> StockOut:
    service = AdminService(session)
    row = await service.get_stock(str(warehouse_id), str(variant_id))
    if row is None:
        raise HTTPException(status_code=404, detail="stock not found")
    return StockOut.model_validate(row, from_attributes=True)


@router.post(
    "/stock",
    status_code=201,
    response_model=StockOut,
    summary="Создать остаток",
)
async def create_stock(
    data: StockIn,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> StockOut:
    service = AdminService(session)
    try:
        row = await service.create_stock(data.model_dump(exclude_unset=True))
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    return StockOut.model_validate(row, from_attributes=True)


@router.patch(
    "/stock/{warehouse_id}/{variant_id}",
    response_model=StockOut,
    summary="Обновить остаток",
)
async def update_stock(
    warehouse_id: uuid.UUID,
    variant_id: uuid.UUID,
    data: StockIn,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> StockOut:
    service = AdminService(session)
    try:
        row = await service.update_stock(
            str(warehouse_id), str(variant_id), data.model_dump(exclude_unset=True)
        )
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    if row is None:
        raise HTTPException(status_code=404, detail="stock not found")
    return StockOut.model_validate(row, from_attributes=True)


@router.delete(
    "/stock/{warehouse_id}/{variant_id}",
    summary="Удалить остаток",
)
async def delete_stock(
    warehouse_id: uuid.UUID,
    variant_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> dict[str, bool]:
    service = AdminService(session)
    try:
        ok = await service.delete_stock(str(warehouse_id), str(variant_id))
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    if not ok:
        raise HTTPException(status_code=404, detail="stock not found")
    return {"deleted": True}


# ---------- перемещения ----------

@router.get(
    "/transfers",
    response_model=list[TransferOut],
    summary="Список перемещений стока",
)
async def list_transfers(
    offset: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> list[TransferOut]:
    service = AdminService(session)
    rows = await service.list_transfers(offset=offset, limit=limit)
    return [TransferOut.model_validate(row, from_attributes=True) for row in rows]


@router.get(
    "/transfers/{transfer_id}",
    response_model=TransferOut,
    summary="Карточка перемещения",
)
async def get_transfer(
    transfer_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> TransferOut:
    service = AdminService(session)
    row = await service.get_transfer(str(transfer_id))
    if row is None:
        raise HTTPException(status_code=404, detail="transfer not found")
    return TransferOut.model_validate(row, from_attributes=True)


@router.post(
    "/transfers",
    status_code=201,
    response_model=TransferOut,
    summary="Создать перемещение",
)
async def create_transfer(
    data: TransferIn,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> TransferOut:
    service = AdminService(session)
    try:
        row = await service.create_transfer(data.model_dump(exclude_unset=True))
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    return TransferOut.model_validate(row, from_attributes=True)


@router.patch(
    "/transfers/{transfer_id}",
    response_model=TransferOut,
    summary="Обновить перемещение",
)
async def update_transfer(
    transfer_id: uuid.UUID,
    data: TransferIn,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> TransferOut:
    service = AdminService(session)
    try:
        row = await service.update_transfer(
            str(transfer_id), data.model_dump(exclude_unset=True)
        )
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    if row is None:
        raise HTTPException(status_code=404, detail="transfer not found")
    return TransferOut.model_validate(row, from_attributes=True)


@router.delete(
    "/transfers/{transfer_id}",
    summary="Удалить перемещение",
)
async def delete_transfer(
    transfer_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> dict[str, bool]:
    service = AdminService(session)
    try:
        ok = await service.delete_transfer(str(transfer_id))
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    if not ok:
        raise HTTPException(status_code=404, detail="transfer not found")
    return {"deleted": True}


# ---------- позиции перемещения ----------

@router.get(
    "/transfers/{transfer_id}/items",
    response_model=list[TransferItemOut],
    summary="Позиции перемещения",
)
async def list_transfer_items(
    transfer_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> list[TransferItemOut]:
    service = AdminService(session)
    rows = await service.list_transfer_items(str(transfer_id))
    return [TransferItemOut.model_validate(row, from_attributes=True) for row in rows]


@router.post(
    "/transfers/{transfer_id}/items",
    status_code=201,
    response_model=TransferItemOut,
    summary="Добавить позицию перемещения",
)
async def create_transfer_item(
    transfer_id: uuid.UUID,
    data: TransferItemIn,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> TransferItemOut:
    service = AdminService(session)
    payload = {"transfer_id": uuid_id(str(transfer_id)), **data.model_dump(exclude_unset=True)}
    try:
        row = await service.create_transfer_item(payload)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    return TransferItemOut.model_validate(row, from_attributes=True)


@router.patch(
    "/transfers/{transfer_id}/items/{variant_id}",
    response_model=TransferItemOut,
    summary="Обновить позицию перемещения",
)
async def update_transfer_item(
    transfer_id: uuid.UUID,
    variant_id: uuid.UUID,
    data: TransferItemIn,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> TransferItemOut:
    service = AdminService(session)
    try:
        row = await service.update_transfer_item(
            str(transfer_id), str(variant_id), data.model_dump(exclude_unset=True)
        )
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    if row is None:
        raise HTTPException(status_code=404, detail="transfer item not found")
    return TransferItemOut.model_validate(row, from_attributes=True)


@router.delete(
    "/transfers/{transfer_id}/items/{variant_id}",
    summary="Удалить позицию перемещения",
)
async def delete_transfer_item(
    transfer_id: uuid.UUID,
    variant_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> dict[str, bool]:
    service = AdminService(session)
    try:
        ok = await service.delete_transfer_item(str(transfer_id), str(variant_id))
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    if not ok:
        raise HTTPException(status_code=404, detail="transfer item not found")
    return {"deleted": True}


# ---------- маршруты (pending ORM-модель) ----------

@router.get("/routes", response_model=list[RouteOut], summary="Список маршрутов")
async def list_routes(
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> list[RouteOut]:
    _RouteModel = _require_model(_Route, "routes")
    service = AdminService(session)
    rows = await service.list_entities(_RouteModel)
    return [RouteOut.model_validate(row, from_attributes=True) for row in rows]


@router.get("/routes/{route_id}", response_model=RouteOut, summary="Карточка маршрута")
async def get_route(
    route_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> RouteOut:
    _RouteModel = _require_model(_Route, "routes")
    service = AdminService(session)
    row = await service.get_entity(_RouteModel, str(route_id))
    if row is None:
        raise HTTPException(status_code=404, detail="route not found")
    return RouteOut.model_validate(row, from_attributes=True)


@router.post("/routes", status_code=201, response_model=RouteOut, summary="Создать маршрут")
async def create_route(
    data: RouteIn,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> RouteOut:
    _RouteModel = _require_model(_Route, "routes")
    service = AdminService(session)
    try:
        row = await service.create_entity(_RouteModel, data.model_dump(exclude_unset=True))
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    return RouteOut.model_validate(row, from_attributes=True)


@router.patch("/routes/{route_id}", response_model=RouteOut, summary="Обновить маршрут")
async def update_route(
    route_id: uuid.UUID,
    data: RouteIn,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> RouteOut:
    _RouteModel = _require_model(_Route, "routes")
    service = AdminService(session)
    try:
        row = await service.update_entity(
            _RouteModel, str(route_id), data.model_dump(exclude_unset=True)
        )
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    if row is None:
        raise HTTPException(status_code=404, detail="route not found")
    return RouteOut.model_validate(row, from_attributes=True)


@router.delete("/routes/{route_id}", summary="Удалить маршрут")
async def delete_route(
    route_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> dict[str, bool]:
    _RouteModel = _require_model(_Route, "routes")
    service = AdminService(session)
    try:
        ok = await service.delete_entity(_RouteModel, str(route_id))
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    if not ok:
        raise HTTPException(status_code=404, detail="route not found")
    return {"deleted": True}


# ---------- перевозчики (pending ORM-модель) ----------

@router.get("/carriers", response_model=list[CarrierOut], summary="Список перевозчиков")
async def list_carriers(
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> list[CarrierOut]:
    _CarrierModel = _require_model(_Carrier, "carriers")
    service = AdminService(session)
    rows = await service.list_entities(_CarrierModel)
    return [CarrierOut.model_validate(row, from_attributes=True) for row in rows]


@router.get("/carriers/{carrier_id}", response_model=CarrierOut, summary="Карточка перевозчика")
async def get_carrier(
    carrier_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> CarrierOut:
    _CarrierModel = _require_model(_Carrier, "carriers")
    service = AdminService(session)
    row = await service.get_entity(_CarrierModel, str(carrier_id))
    if row is None:
        raise HTTPException(status_code=404, detail="carrier not found")
    return CarrierOut.model_validate(row, from_attributes=True)


@router.post("/carriers", status_code=201, response_model=CarrierOut, summary="Создать перевозчика")
async def create_carrier(
    data: CarrierIn,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> CarrierOut:
    _CarrierModel = _require_model(_Carrier, "carriers")
    service = AdminService(session)
    try:
        row = await service.create_entity(_CarrierModel, data.model_dump(exclude_unset=True))
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    return CarrierOut.model_validate(row, from_attributes=True)


@router.patch("/carriers/{carrier_id}", response_model=CarrierOut, summary="Обновить перевозчика")
async def update_carrier(
    carrier_id: uuid.UUID,
    data: CarrierIn,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> CarrierOut:
    _CarrierModel = _require_model(_Carrier, "carriers")
    service = AdminService(session)
    try:
        row = await service.update_entity(
            _CarrierModel, str(carrier_id), data.model_dump(exclude_unset=True)
        )
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    if row is None:
        raise HTTPException(status_code=404, detail="carrier not found")
    return CarrierOut.model_validate(row, from_attributes=True)


@router.delete("/carriers/{carrier_id}", summary="Удалить перевозчика")
async def delete_carrier(
    carrier_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> dict[str, bool]:
    _CarrierModel = _require_model(_Carrier, "carriers")
    service = AdminService(session)
    try:
        ok = await service.delete_entity(_CarrierModel, str(carrier_id))
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    if not ok:
        raise HTTPException(status_code=404, detail="carrier not found")
    return {"deleted": True}


# ---------- заказы (чтение + смена статуса) ----------

@router.get(
    "/orders",
    response_model=list[OrderOut],
    summary="Список заказов",
)
async def admin_list_orders(
    offset: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> list[OrderOut]:
    service = AdminService(session)
    rows = await service.list_orders(offset=offset, limit=limit)
    return [OrderOut.model_validate(row, from_attributes=True) for row in rows]


@router.get(
    "/orders/{order_id}",
    response_model=OrderOut,
    summary="Карточка заказа",
)
async def admin_get_order(
    order_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> OrderOut:
    service = AdminService(session)
    row = await service.get_order(str(order_id))
    if row is None:
        raise HTTPException(status_code=404, detail="order not found")
    return OrderOut.model_validate(row, from_attributes=True)


@router.patch(
    "/orders/{order_id}/status",
    response_model=OrderOut,
    summary="Сменить статус заказа",
)
async def admin_change_order_status(
    order_id: uuid.UUID,
    data: OrderStatusIn,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> OrderOut:
    service = AdminService(session)
    try:
        row = await service.change_order_status(str(order_id), data.status)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    if row is None:
        raise HTTPException(status_code=404, detail="order not found")
    return OrderOut.model_validate(row, from_attributes=True)


# ---------- покупатели (пользователи) ----------

@router.get(
    "/customers",
    response_model=list[CustomerOut],
    summary="Список покупателей",
)
async def list_customers(
    offset: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> list[CustomerOut]:
    service = AdminService(session)
    rows = await service.list_customers(offset=offset, limit=limit)
    return [CustomerOut.model_validate(row, from_attributes=True) for row in rows]


@router.get(
    "/customers/{customer_id}",
    response_model=CustomerOut,
    summary="Карточка покупателя",
)
async def get_customer(
    customer_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> CustomerOut:
    service = AdminService(session)
    row = await service.get_customer(str(customer_id))
    if row is None:
        raise HTTPException(status_code=404, detail="customer not found")
    return CustomerOut.model_validate(row, from_attributes=True)


@router.patch(
    "/customers/{customer_id}",
    response_model=CustomerOut,
    summary="Обновить данные покупателя",
)
async def update_customer(
    customer_id: uuid.UUID,
    data: CustomerIn,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_admin_user),
) -> CustomerOut:
    service = AdminService(session)
    try:
        row = await service.update_customer(
            str(customer_id), data.model_dump(exclude_unset=True)
        )
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail="constraint violation") from exc
    if row is None:
        raise HTTPException(status_code=404, detail="customer not found")
    return CustomerOut.model_validate(row, from_attributes=True)
