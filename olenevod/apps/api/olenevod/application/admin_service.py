"""Сервис админ-панели: универсальный CRUD над справочниками, остатками и заказами.

Все изменения выполняются в рамках переданной ``AsyncSession`` (одна транзакция на
HTTP-запрос, коммит — на уровне HTTP-слоя). Мягкое удаление через ``deleted_at``
там, где колонка есть в модели; иначе — hard delete.

Моделей ``routes`` и ``carriers`` в ORM пока нет (вне моих путей); когда они
появляются, достаточно добавить их сюда по тому же шаблону.
"""

import uuid
from datetime import UTC, datetime
from typing import Any, TypeVar, cast

from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from olenevod.application.auth_service import User
from olenevod.infrastructure.models import (
    City,
    CityOffer,
    Order,
    Product,
    ProductVariant,
    StockLevel,
    StockTransfer,
    StockTransferItem,
    Warehouse,
)

T = TypeVar("T")


def _pk_columns(model: type[Any]) -> list[str]:
    """Имена первичных ключей модели (для композитных — все колонки PK)."""
    mapper = inspect(model)
    return [column.name for column in mapper.primary_key]


def _has_deleted_at(model: type[Any]) -> bool:
    return hasattr(model, "deleted_at")


def uuid_id(value: str) -> Any:
    """Преобразовать строковый идентификатор в UUID."""
    return uuid.UUID(value)


class AdminService:
    """Универсальный CRUD-сервис для раздела админки.

    ``ident`` — значение PK (или кортеж для композитного PK, например
    ``(warehouse_id, variant_id)`` для ``StockLevel``).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ---------- универсальные методы ----------

    async def _list(
        self,
        model: type[T],
        *,
        offset: int = 0,
        limit: int = 50,
        order_by: Any = None,
    ) -> list[T]:
        stmt = select(model)
        if _has_deleted_at(model):
            deleted_at = getattr(model, "deleted_at")  # type: Any  # noqa: B009
            stmt = stmt.where(deleted_at.is_(None))
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        stmt = stmt.offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return cast(list[T], list(result.scalars().all()))

    async def _get(self, model: type[T], ident: Any) -> T | None:
        pks = _pk_columns(model)
        if isinstance(ident, tuple) and len(pks) > 1:
            stmt = select(model)
            for col, val in zip(pks, ident, strict=True):
                stmt = stmt.where(getattr(model, col) == val)
            if _has_deleted_at(model):
                deleted_at = getattr(model, "deleted_at")  # type: Any  # noqa: B009
                stmt = stmt.where(deleted_at.is_(None))
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        obj = await self._session.get(model, ident)
        return obj

    async def _create(self, model: type[T], data: dict[str, Any]) -> T:
        obj = model()
        for key, value in data.items():
            setattr(obj, key, value)
        self._session.add(obj)
        await self._session.flush()
        return obj

    async def _update(
        self, model: type[T], ident: Any, data: dict[str, Any]
    ) -> T | None:
        obj = await self._get(model, ident)
        if obj is None:
            return None
        for key, value in data.items():
            setattr(obj, key, value)
        await self._session.flush()
        return obj

    async def _delete(self, model: type[Any], ident: Any) -> bool:
        obj = await self._get(model, ident)
        if obj is None:
            return False
        if _has_deleted_at(model):
            obj.deleted_at = datetime.now(UTC)
            await self._session.flush()
        else:
            await self._session.delete(obj)
            await self._session.flush()
        return True

    # ---------- публичные универсальные методы ----------

    async def list_entities(
        self,
        model: type[T],
        *,
        offset: int = 0,
        limit: int = 50,
        order_by: Any = None,
    ) -> list[T]:
        return await self._list(model, offset=offset, limit=limit, order_by=order_by)

    async def get_entity(self, model: type[T], ident: Any) -> T | None:
        return await self._get(model, ident)

    async def create_entity(self, model: type[T], data: dict[str, Any]) -> T:
        return await self._create(model, data)

    async def update_entity(
        self, model: type[T], ident: Any, data: dict[str, Any]
    ) -> T | None:
        return await self._update(model, ident, data)

    async def delete_entity(self, model: type[Any], ident: Any) -> bool:
        return await self._delete(model, ident)

    # ---------- города ----------

    async def list_cities(self, *, offset: int = 0, limit: int = 50) -> list[City]:
        return await self._list(City, offset=offset, limit=limit, order_by=City.name)

    async def get_city(self, city_id: str) -> City | None:
        return await self._get(City, uuid_id(city_id))

    async def create_city(self, data: dict[str, Any]) -> City:
        return await self._create(City, data)

    async def update_city(self, city_id: str, data: dict[str, Any]) -> City | None:
        return await self._update(City, uuid_id(city_id), data)

    async def delete_city(self, city_id: str) -> bool:
        return await self._delete(City, uuid_id(city_id))

    # ---------- склады ----------

    async def list_warehouses(self, *, offset: int = 0, limit: int = 50) -> list[Warehouse]:
        return await self._list(Warehouse, offset=offset, limit=limit, order_by=Warehouse.name)

    async def get_warehouse(self, warehouse_id: str) -> Warehouse | None:
        return await self._get(Warehouse, uuid_id(warehouse_id))

    async def create_warehouse(self, data: dict[str, Any]) -> Warehouse:
        return await self._create(Warehouse, data)

    async def update_warehouse(self, warehouse_id: str, data: dict[str, Any]) -> Warehouse | None:
        return await self._update(Warehouse, uuid_id(warehouse_id), data)

    async def delete_warehouse(self, warehouse_id: str) -> bool:
        return await self._delete(Warehouse, uuid_id(warehouse_id))

    # ---------- товары ----------

    async def list_products(self, *, offset: int = 0, limit: int = 50) -> list[Product]:
        return await self._list(Product, offset=offset, limit=limit, order_by=Product.name)

    async def get_product(self, product_id: str) -> Product | None:
        return await self._get(Product, uuid_id(product_id))

    async def create_product(self, data: dict[str, Any]) -> Product:
        return await self._create(Product, data)

    async def update_product(self, product_id: str, data: dict[str, Any]) -> Product | None:
        return await self._update(Product, uuid_id(product_id), data)

    async def delete_product(self, product_id: str) -> bool:
        return await self._delete(Product, uuid_id(product_id))

    # ---------- варианты ----------

    async def list_variants(self, *, offset: int = 0, limit: int = 50) -> list[ProductVariant]:
        return await self._list(
            ProductVariant, offset=offset, limit=limit, order_by=ProductVariant.name
        )

    async def get_variant(self, variant_id: str) -> ProductVariant | None:
        return await self._get(ProductVariant, uuid_id(variant_id))

    async def create_variant(self, data: dict[str, Any]) -> ProductVariant:
        return await self._create(ProductVariant, data)

    async def update_variant(self, variant_id: str, data: dict[str, Any]) -> ProductVariant | None:
        return await self._update(ProductVariant, uuid_id(variant_id), data)

    async def delete_variant(self, variant_id: str) -> bool:
        return await self._delete(ProductVariant, uuid_id(variant_id))

    # ---------- предложения города ----------

    async def list_offers(self, *, offset: int = 0, limit: int = 50) -> list[CityOffer]:
        return await self._list(CityOffer, offset=offset, limit=limit, order_by=CityOffer.id)

    async def get_offer(self, offer_id: str) -> CityOffer | None:
        return await self._get(CityOffer, uuid_id(offer_id))

    async def create_offer(self, data: dict[str, Any]) -> CityOffer:
        return await self._create(CityOffer, data)

    async def update_offer(self, offer_id: str, data: dict[str, Any]) -> CityOffer | None:
        return await self._update(CityOffer, uuid_id(offer_id), data)

    async def delete_offer(self, offer_id: str) -> bool:
        return await self._delete(CityOffer, uuid_id(offer_id))

    # ---------- остатки ----------

    async def list_stock(self, *, offset: int = 0, limit: int = 50) -> list[StockLevel]:
        return await self._list(
            StockLevel, offset=offset, limit=limit, order_by=StockLevel.warehouse_id
        )

    async def get_stock(self, warehouse_id: str, variant_id: str) -> StockLevel | None:
        return await self._get(StockLevel, (uuid_id(warehouse_id), uuid_id(variant_id)))

    async def create_stock(self, data: dict[str, Any]) -> StockLevel:
        return await self._create(StockLevel, data)

    async def update_stock(
        self, warehouse_id: str, variant_id: str, data: dict[str, Any]
    ) -> StockLevel | None:
        return await self._update(
            StockLevel, (uuid_id(warehouse_id), uuid_id(variant_id)), data
        )

    async def delete_stock(self, warehouse_id: str, variant_id: str) -> bool:
        return await self._delete(
            StockLevel, (uuid_id(warehouse_id), uuid_id(variant_id))
        )

    # ---------- перемещения ----------

    async def list_transfers(self, *, offset: int = 0, limit: int = 50) -> list[StockTransfer]:
        return await self._list(
            StockTransfer, offset=offset, limit=limit, order_by=StockTransfer.created_at.desc()
        )

    async def get_transfer(self, transfer_id: str) -> StockTransfer | None:
        return await self._get(StockTransfer, uuid_id(transfer_id))

    async def create_transfer(self, data: dict[str, Any]) -> StockTransfer:
        return await self._create(StockTransfer, data)

    async def update_transfer(self, transfer_id: str, data: dict[str, Any]) -> StockTransfer | None:
        return await self._update(StockTransfer, uuid_id(transfer_id), data)

    async def delete_transfer(self, transfer_id: str) -> bool:
        return await self._delete(StockTransfer, uuid_id(transfer_id))

    # ---------- позиции перемещения ----------

    async def list_transfer_items(
        self, transfer_id: str, *, offset: int = 0, limit: int = 50
    ) -> list[StockTransferItem]:
        return await self._list(
            StockTransferItem,
            offset=offset,
            limit=limit,
            order_by=StockTransferItem.variant_id,
        )

    async def get_transfer_item(self, transfer_id: str, variant_id: str) -> StockTransferItem | None:
        return await self._get(
            StockTransferItem, (uuid_id(transfer_id), uuid_id(variant_id))
        )

    async def create_transfer_item(self, data: dict[str, Any]) -> StockTransferItem:
        return await self._create(StockTransferItem, data)

    async def update_transfer_item(
        self, transfer_id: str, variant_id: str, data: dict[str, Any]
    ) -> StockTransferItem | None:
        return await self._update(
            StockTransferItem, (uuid_id(transfer_id), uuid_id(variant_id)), data
        )

    async def delete_transfer_item(self, transfer_id: str, variant_id: str) -> bool:
        return await self._delete(
            StockTransferItem, (uuid_id(transfer_id), uuid_id(variant_id))
        )

    # ---------- заказы (чтение + смена статуса) ----------

    async def list_orders(self, *, offset: int = 0, limit: int = 50) -> list[Order]:
        return await self._list(
            Order, offset=offset, limit=limit, order_by=Order.created_at.desc()
        )

    async def get_order(self, order_id: str) -> Order | None:
        return await self._get(Order, uuid_id(order_id))

    async def change_order_status(self, order_id: str, status: str) -> Order | None:
        order = await self._get(Order, uuid_id(order_id))
        if order is None:
            return None
        order.status = status
        await self._session.flush()
        return order

    # ---------- покупатели (пользователи) ----------

    async def list_customers(self, *, offset: int = 0, limit: int = 50) -> list[User]:
        return await self._list(
            User, offset=offset, limit=limit, order_by=User.created_at.desc()
        )

    async def get_customer(self, customer_id: str) -> User | None:
        return await self._get(User, uuid_id(customer_id))

    async def update_customer(self, customer_id: str, data: dict[str, Any]) -> User | None:
        return await self._update(User, uuid_id(customer_id), data)
