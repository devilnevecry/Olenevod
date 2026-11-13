"""ORM-модели доставки: delivery_zones, delivery_tariffs."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from olenevod.infrastructure.db import Base


class DeliveryZone(Base):
    """Зона доставки города: базовая плата, плата за кг, порог бесплатной доставки."""

    __tablename__ = "delivery_zones"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("cities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        unique=True,
    )
    zone_name: Mapped[str] = mapped_column(String(255), nullable=False)
    base_fee: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    per_kg_fee: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    free_from_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint("base_fee >= 0", name="ck_delivery_zones_base_fee_nonneg"),
        CheckConstraint("per_kg_fee >= 0", name="ck_delivery_zones_per_kg_fee_nonneg"),
        CheckConstraint(
            "free_from_amount IS NULL OR free_from_amount >= 0",
            name="ck_delivery_zones_free_from_amount_nonneg",
        ),
    )


class DeliveryTariff(Base):
    """Тариф доставки зоны: название и оценочный срок в днях."""

    __tablename__ = "delivery_tariffs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    zone_id: Mapped[uuid.UUID] = mapped_column(
        postgresql.UUID(as_uuid=True),
        ForeignKey("delivery_zones.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        unique=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    estimated_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(server_default="true", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "estimated_days IS NULL OR estimated_days >= 0",
            name="ck_delivery_tariffs_estimated_days_nonneg",
        ),
    )
