"""ORM-Ð¼Ð¾Ð´ÐµÐ»Ð¸ ÐºÐ°Ñ‚Ð°Ð»Ð¾Ð³Ð°: categories, products, product_variants, nutrition, product_media, files, product_certificates."""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from olenevod.infrastructure.db import Base, JsonDict


class Category(Base):
    """ÐšÐ°Ñ‚ÐµÐ³Ð¾Ñ€Ð¸Ñ Ñ‚Ð¾Ð²Ð°Ñ€Ð¾Ð² (Ð¸ÐµÑ€Ð°Ñ€Ñ…Ð¸Ñ Ñ‡ÐµÑ€ÐµÐ· parent_id, Ð¼ÑÐ³ÐºÐ¾Ðµ ÑƒÐ´Ð°Ð»ÐµÐ½Ð¸Ðµ)."""

    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_published: Mapped[bool] = mapped_column(default=True, nullable=False)
    seo_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("files.id", ondelete="SET NULL"), nullable=True
    )
    is_demo: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("char_length(slug) > 0", name="ck_categories_slug_nonempty"),
    )


class Product(Base):
    """Ð¢Ð¾Ð²Ð°Ñ€ (Ð¿Ñ€Ð¸Ð²ÑÐ·Ð°Ð½ Ðº ÐºÐ°Ñ‚ÐµÐ³Ð¾Ñ€Ð¸Ð¸, Ð¼ÑÐ³ÐºÐ¾Ðµ ÑƒÐ´Ð°Ð»ÐµÐ½Ð¸Ðµ)."""

    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    composition: Mapped[str | None] = mapped_column(Text, nullable=True)
    storage_conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    shelf_life_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    origin_note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_published: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_demo: Mapped[bool] = mapped_column(default=False, nullable=False)
    seo_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("char_length(slug) > 0", name="ck_products_slug_nonempty"),
        Index(
            "ix_products_search_gin",
            func.to_tsvector(
                "russian",
                func.concat(
                    func.coalesce(name, ""),
                    " ",
                    func.coalesce(short_description, ""),
                    " ",
                    func.coalesce(description, ""),
                ),
            ),
            postgresql_using="gin",
        ),
        Index(
            "ix_products_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )


class ProductVariant(Base):
    """Ð’Ð°Ñ€Ð¸Ð°Ð½Ñ‚ Ñ‚Ð¾Ð²Ð°Ñ€Ð° (SKU, ÐµÐ´Ð¸Ð½Ð¸Ñ†Ð° Ð¸Ð·Ð¼ÐµÑ€ÐµÐ½Ð¸Ñ, Ð°Ñ‚Ñ€Ð¸Ð±ÑƒÑ‚Ñ‹)."""

    __tablename__ = "product_variants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_type: Mapped[str] = mapped_column(
        Enum("piece", "weight", name="product_variant_unit_type"), nullable=False
    )
    pack_weight_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    barcode: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    attributes: Mapped[JsonDict | None] = mapped_column(postgresql.JSONB(astext_type=Text()), nullable=True)  # type: ignore[no-untyped-call,unused-ignore]
    is_demo: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("char_length(sku) > 0", name="ck_product_variants_sku_nonempty"),
    )


class Nutrition(Base):
    """ÐšÐ‘Ð–Ð£ Ð½Ð° 100 Ð³ Ð²Ð°Ñ€Ð¸Ð°Ð½Ñ‚Ð° (Ð¿ÑƒÐ±Ð»Ð¸ÐºÑƒÐµÑ‚ÑÑ Ñ‚Ð¾Ð»ÑŒÐºÐ¾ Ð¿Ñ€Ð¸ verified = true)."""

    __tablename__ = "nutrition"

    variant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_variants.id", ondelete="CASCADE"), primary_key=True
    )
    per_100g: Mapped[JsonDict | None] = mapped_column(postgresql.JSONB(astext_type=Text()), nullable=True)  # type: ignore[no-untyped-call,unused-ignore]
    verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    verified_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ProductMedia(Base):
    """ÐœÐµÐ´Ð¸Ð°-Ñ„Ð°Ð¹Ð» Ñ‚Ð¾Ð²Ð°Ñ€Ð° (ÑÑÑ‹Ð»ÐºÐ° Ð½Ð° files)."""

    __tablename__ = "product_media"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("files.id", ondelete="RESTRICT"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    alt: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_demo: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class File(Base):
    """Ð¥Ñ€Ð°Ð½Ð¸Ð¼Ñ‹Ð¹ Ñ„Ð°Ð¹Ð» (Ð¼ÐµÐ´Ð¸Ð°, ÑÐµÑ€Ñ‚Ð¸Ñ„Ð¸ÐºÐ°Ñ‚, Ð¿Ñ€Ð¾Ñ‡ÐµÐµ)."""

    __tablename__ = "files"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    storage_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    mime: Mapped[str] = mapped_column(String(100), nullable=False)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    license_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ProductCertificate(Base):
    """Ð¡ÐµÑ€Ñ‚Ð¸Ñ„Ð¸ÐºÐ°Ñ‚ Ñ‚Ð¾Ð²Ð°Ñ€Ð° Ð¸Ð»Ð¸ Ð²Ð°Ñ€Ð¸Ð°Ð½Ñ‚Ð° (ÑÑÑ‹Ð»ÐºÐ° Ð½Ð° Ñ„Ð°Ð¹Ð», ÑÑ€Ð¾Ðº Ð´ÐµÐ¹ÑÑ‚Ð²Ð¸Ñ)."""

    __tablename__ = "product_certificates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True
    )
    variant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("files.id", ondelete="RESTRICT"), nullable=False
    )
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "product_id IS NOT NULL OR variant_id IS NOT NULL",
            name="ck_product_certificates_product_or_variant",
        ),
    )

