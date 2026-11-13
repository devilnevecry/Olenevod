"""ORM-модели остатков и городов: cities, warehouses, city_offers, stock_levels,
stock_movements, reservations, stock_transfers, stock_transfer_items, audit_log."""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from olenevod.infrastructure.db import Base, JsonDict


class City(Base):
    """Город — точка продаж со своими ценами, остатками и доступностью."""

    __tablename__ = "cities"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    region: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timezone: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_default_for_russia: Mapped[bool] = mapped_column(default=False, nullable=False)
    lat: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    lon: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    pickup_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    courier_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    carrier_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    order_cutoff_time: Mapped[str | None] = mapped_column(String(8), nullable=True)
    prep_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    seo_intro: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Warehouse(Base):
    """Склад внутри города."""

    __tablename__ = "warehouses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CityOffer(Base):
    """Предложение города: вариант товара x город с ценой и доступностью."""

    __tablename__ = "city_offers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    price_kop: Mapped[int] = mapped_column(Integer, nullable=False)
    old_price_kop: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_published: Mapped[bool] = mapped_column(default=True, nullable=False)
    min_qty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    step_qty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_qty_per_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_city_offers_city_id_is_published", "city_id", "is_published"),
        Index("ix_city_offers_variant_id", "variant_id"),
        CheckConstraint("price_kop >= 0", name="ck_city_offers_price_nonneg"),
        CheckConstraint("old_price_kop IS NULL OR old_price_kop >= 0", name="ck_city_offers_old_price_nonneg"),
        CheckConstraint("min_qty >= 1", name="ck_city_offers_min_qty_positive"),
        CheckConstraint("step_qty >= 1", name="ck_city_offers_step_qty_positive"),
    )


class StockLevel(Base):
    """Остаток варианта на складе: on_hand, reserved, доступно = on_hand - reserved."""

    __tablename__ = "stock_levels"

    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("warehouses.id", ondelete="CASCADE"), primary_key=True
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_variants.id", ondelete="CASCADE"), primary_key=True
    )
    on_hand: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("on_hand >= 0", name="ck_stock_levels_on_hand_nonneg"),
        CheckConstraint("reserved >= 0", name="ck_stock_levels_reserved_nonneg"),
        CheckConstraint("reserved <= on_hand", name="ck_stock_levels_reserved_le_on_hand"),
        Index("ix_stock_levels_variant_id", "variant_id"),
    )


class StockMovement(Base):
    """Неизменяемая запись движения остатка (append-only: запрет UPDATE/DELETE)."""

    __tablename__ = "stock_movements"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(
        Enum(
            "receipt",
            "adjustment",
            "reserve",
            "release",
            "commit",
            "return_in",
            "writeoff",
            "transfer_out",
            "transfer_in",
            "inventory_correction",
            name="stock_movement_type",
        ),
        nullable=False,
    )
    qty_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    on_hand_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved_after: Mapped[int] = mapped_column(Integer, nullable=False)
    order_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    transfer_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    __table_args__ = (
        CheckConstraint("on_hand_after >= 0", name="ck_stock_movements_on_hand_after_nonneg"),
        CheckConstraint("reserved_after >= 0", name="ck_stock_movements_reserved_after_nonneg"),
        Index("ix_stock_movements_warehouse_variant_created", "warehouse_id", "variant_id", "created_at"),
    )


class Reservation(Base):
    """Резерв остатка под заказ."""

    __tablename__ = "reservations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("active", "committed", "released", "expired", name="reservation_status"),
        nullable=False,
        default="active",
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("qty > 0", name="ck_reservations_qty_positive"),
    )


class StockTransfer(Base):
    """Перемещение товара между складами (черновик -> в пути -> получено)."""

    __tablename__ = "stock_transfers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    from_warehouse_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    to_warehouse_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        Enum("draft", "in_transit", "received", "cancelled", name="stock_transfer_status"),
        nullable=False,
        default="draft",
    )
    route_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    planned_departure: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    eta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    carrier_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class StockTransferItem(Base):
    """Позиция перемещения: вариант + количество."""

    __tablename__ = "stock_transfer_items"

    transfer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("stock_transfers.id", ondelete="CASCADE"), primary_key=True
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_variants.id", ondelete="RESTRICT"), primary_key=True
    )
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    received_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        CheckConstraint("qty > 0", name="ck_stock_transfer_items_qty_positive"),
    )


class InventoryReservation(Base):
    """Резерв остатка под заказ (городской уровень, привязка к складу фиксируется при создании)."""

    __tablename__ = "inventory_reservations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    city_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cities.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(
            "active",
            "committed",
            "released",
            "expired",
            name="inventory_reservation_status",
        ),
        nullable=False,
        default="active",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    idempotency_key: Mapped[str | None] = mapped_column(
        String(200), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint("qty > 0", name="ck_inventory_reservations_qty_positive"),
    )


class Outbox(Base):
    """Событийная очередь (outbox) для событий изменения остатков."""

    __tablename__ = "outbox"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    aggregate_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    aggregate_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[JsonDict | None] = mapped_column(postgresql.JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AuditLog(Base):
    """Аудит изменений (append-only: запрет UPDATE/DELETE)."""

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    city_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    before: Mapped[JsonDict | None] = mapped_column(postgresql.JSONB, nullable=True)
    after: Mapped[JsonDict | None] = mapped_column(postgresql.JSONB, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
