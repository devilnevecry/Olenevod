"""Initial schema: каталог, города, склады, предложения, остатки, движения, аудит.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Имена PostgreSQL-ENUM типов, создаваемых инлайново в колонках.
ENUM_TYPES = (
    "product_variant_unit_type",
    "stock_movement_type",
    "reservation_status",
    "stock_transfer_status",
)


def upgrade() -> None:
    # pg_trgm нужен для триграммного индекса на products.name.
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ---------- catalog ----------
    op.create_table(
        "files",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("mime", sa.String(length=100), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("bytes", sa.Integer(), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("license_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_files"),
        sa.UniqueConstraint("storage_key", name="uq_files_storage_key"),
    )

    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "parent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_published", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("seo_title", sa.String(length=255), nullable=True),
        sa.Column("seo_description", sa.Text(), nullable=True),
        sa.Column(
            "image_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("files.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_demo", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_categories"),
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"], name="fk_categories_parent_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["image_id"], ["files.id"], name="fk_categories_image_id", ondelete="SET NULL"),
        sa.CheckConstraint("char_length(slug) > 0", name="ck_categories_slug_nonempty"),
        sa.UniqueConstraint("slug", name="uq_categories_slug"),
    )
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"], unique=False)

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("short_description", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("composition", sa.Text(), nullable=True),
        sa.Column("storage_conditions", sa.Text(), nullable=True),
        sa.Column("shelf_life_days", sa.Integer(), nullable=True),
        sa.Column("origin_note", sa.String(length=255), nullable=True),
        sa.Column("is_published", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_demo", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("seo_title", sa.String(length=255), nullable=True),
        sa.Column("seo_description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_products"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], name="fk_products_category_id", ondelete="RESTRICT"),
        sa.CheckConstraint("char_length(slug) > 0", name="ck_products_slug_nonempty"),
        sa.UniqueConstraint("slug", name="uq_products_slug"),
    )
    op.create_index("ix_products_category_id", "products", ["category_id"], unique=False)
    op.create_index(
        "ix_products_search_gin",
        "products",
        [sa.text("to_tsvector('russian', coalesce(name, '') || ' ' || coalesce(short_description, '') || ' ' || coalesce(description, ''))")],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_products_name_trgm",
        "products",
        ["name"],
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )

    op.create_table(
        "product_variants",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sku", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "unit_type",
            sa.Enum("piece", "weight", name="product_variant_unit_type"),
            nullable=False,
        ),
        sa.Column("pack_weight_g", sa.Integer(), nullable=True),
        sa.Column("barcode", sa.String(length=100), nullable=True),
        sa.Column("attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_demo", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_product_variants"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name="fk_product_variants_product_id", ondelete="CASCADE"),
        sa.CheckConstraint("char_length(sku) > 0", name="ck_product_variants_sku_nonempty"),
        sa.UniqueConstraint("sku", name="uq_product_variants_sku"),
    )
    op.create_index("ix_product_variants_product_id", "product_variants", ["product_id"], unique=False)
    op.create_index("ix_product_variants_barcode", "product_variants", ["barcode"], unique=False)

    op.create_table(
        "nutrition",
        sa.Column(
            "variant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_variants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("per_100g", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("verified", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("verified_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("variant_id", name="pk_nutrition"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], name="fk_nutrition_variant_id", ondelete="CASCADE"),
    )

    op.create_table(
        "product_media",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "file_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("files.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("alt", sa.String(length=255), nullable=True),
        sa.Column("sort", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_demo", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_product_media"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name="fk_product_media_product_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], name="fk_product_media_file_id", ondelete="RESTRICT"),
    )
    op.create_index("ix_product_media_product_id", "product_media", ["product_id"], unique=False)

    op.create_table(
        "product_certificates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "variant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_variants.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column(
            "file_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("files.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_product_certificates"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], name="fk_product_certificates_product_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], name="fk_product_certificates_variant_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], name="fk_product_certificates_file_id", ondelete="RESTRICT"),
        sa.CheckConstraint("product_id IS NOT NULL OR variant_id IS NOT NULL", name="ck_product_certificates_product_or_variant"),
    )
    op.create_index("ix_product_certificates_product_id", "product_certificates", ["product_id"], unique=False)
    op.create_index("ix_product_certificates_variant_id", "product_certificates", ["variant_id"], unique=False)

    # ---------- cities / warehouses / offers / stock ----------
    op.create_table(
        "cities",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("region", sa.String(length=255), nullable=True),
        sa.Column("timezone", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_default_for_russia", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("lat", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("lon", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("pickup_enabled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("courier_enabled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("carrier_enabled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("order_cutoff_time", sa.String(length=8), nullable=True),
        sa.Column("prep_hours", sa.Integer(), nullable=True),
        sa.Column("seo_intro", sa.Text(), nullable=True),
        sa.Column("is_demo", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_cities"),
        sa.UniqueConstraint("slug", name="uq_cities_slug"),
    )

    op.create_table(
        "warehouses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "city_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_warehouses"),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], name="fk_warehouses_city_id", ondelete="CASCADE"),
    )
    op.create_index("ix_warehouses_city_id", "warehouses", ["city_id"], unique=False)

    op.create_table(
        "city_offers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "city_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "variant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_variants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("price_kop", sa.Integer(), nullable=False),
        sa.Column("old_price_kop", sa.Integer(), nullable=True),
        sa.Column("is_published", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("min_qty", sa.Integer(), server_default="1", nullable=False),
        sa.Column("step_qty", sa.Integer(), server_default="1", nullable=False),
        sa.Column("max_qty_per_order", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_city_offers"),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], name="fk_city_offers_city_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], name="fk_city_offers_variant_id", ondelete="CASCADE"),
        sa.CheckConstraint("price_kop >= 0", name="ck_city_offers_price_nonneg"),
        sa.CheckConstraint("old_price_kop IS NULL OR old_price_kop >= 0", name="ck_city_offers_old_price_nonneg"),
        sa.CheckConstraint("min_qty >= 1", name="ck_city_offers_min_qty_positive"),
        sa.CheckConstraint("step_qty >= 1", name="ck_city_offers_step_qty_positive"),
        sa.UniqueConstraint("city_id", "variant_id", name="uq_city_offers_city_variant"),
    )
    op.create_index("ix_city_offers_city_id_is_published", "city_offers", ["city_id", "is_published"], unique=False)
    op.create_index("ix_city_offers_variant_id", "city_offers", ["variant_id"], unique=False)

    op.create_table(
        "stock_levels",
        sa.Column(
            "warehouse_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("warehouses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "variant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_variants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("on_hand", sa.Integer(), server_default="0", nullable=False),
        sa.Column("reserved", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("warehouse_id", "variant_id", name="pk_stock_levels"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], name="fk_stock_levels_warehouse_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], name="fk_stock_levels_variant_id", ondelete="CASCADE"),
        sa.CheckConstraint("on_hand >= 0", name="ck_stock_levels_on_hand_nonneg"),
        sa.CheckConstraint("reserved >= 0", name="ck_stock_levels_reserved_nonneg"),
        sa.CheckConstraint("reserved <= on_hand", name="ck_stock_levels_reserved_le_on_hand"),
    )
    op.create_index("ix_stock_levels_variant_id", "stock_levels", ["variant_id"], unique=False)

    op.create_table(
        "stock_movements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "warehouse_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("warehouses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "variant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_variants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "type",
            sa.Enum(
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
        ),
        sa.Column("qty_delta", sa.Integer(), nullable=False),
        sa.Column("on_hand_after", sa.Integer(), nullable=False),
        sa.Column("reserved_after", sa.Integer(), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("transfer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("actor_type", sa.String(length=50), nullable=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("idempotency_key", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_stock_movements"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], name="fk_stock_movements_warehouse_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], name="fk_stock_movements_variant_id", ondelete="RESTRICT"),
        sa.CheckConstraint("on_hand_after >= 0", name="ck_stock_movements_on_hand_after_nonneg"),
        sa.CheckConstraint("reserved_after >= 0", name="ck_stock_movements_reserved_after_nonneg"),
    )
    op.create_index("ix_stock_movements_warehouse_id", "stock_movements", ["warehouse_id"], unique=False)
    op.create_index("ix_stock_movements_variant_id", "stock_movements", ["variant_id"], unique=False)
    op.create_index(
        "ix_stock_movements_warehouse_variant_created",
        "stock_movements",
        ["warehouse_id", "variant_id", "created_at"],
        unique=False,
    )
    op.create_index("ix_stock_movements_order_id", "stock_movements", ["order_id"], unique=False)
    op.create_index("ix_stock_movements_transfer_id", "stock_movements", ["transfer_id"], unique=False)
    op.create_index("ix_stock_movements_idempotency_key", "stock_movements", ["idempotency_key"], unique=False)
    op.create_index("ix_stock_movements_created_at", "stock_movements", ["created_at"], unique=False)

    # ---------- reservations / transfers ----------
    op.create_table(
        "reservations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "warehouse_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("warehouses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "variant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_variants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("qty", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "committed", "released", "expired", name="reservation_status"),
            server_default="active",
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_reservations"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], name="fk_reservations_warehouse_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], name="fk_reservations_variant_id", ondelete="RESTRICT"),
        sa.CheckConstraint("qty > 0", name="ck_reservations_qty_positive"),
    )
    op.create_index("ix_reservations_order_id", "reservations", ["order_id"], unique=False)
    op.create_index("ix_reservations_warehouse_id", "reservations", ["warehouse_id"], unique=False)
    op.create_index("ix_reservations_variant_id", "reservations", ["variant_id"], unique=False)
    op.create_index("ix_reservations_expires_at", "reservations", ["expires_at"], unique=False)

    op.create_table(
        "stock_transfers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "from_warehouse_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("warehouses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "to_warehouse_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("warehouses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("draft", "in_transit", "received", "cancelled", name="stock_transfer_status"),
            server_default="draft",
            nullable=False,
        ),
        sa.Column("route_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("planned_departure", sa.DateTime(timezone=True), nullable=True),
        sa.Column("eta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("carrier_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_stock_transfers"),
        sa.ForeignKeyConstraint(["from_warehouse_id"], ["warehouses.id"], name="fk_stock_transfers_from_warehouse_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["to_warehouse_id"], ["warehouses.id"], name="fk_stock_transfers_to_warehouse_id", ondelete="RESTRICT"),
    )
    op.create_index("ix_stock_transfers_from_warehouse_id", "stock_transfers", ["from_warehouse_id"], unique=False)
    op.create_index("ix_stock_transfers_to_warehouse_id", "stock_transfers", ["to_warehouse_id"], unique=False)
    op.create_index("ix_stock_transfers_route_id", "stock_transfers", ["route_id"], unique=False)
    op.create_index("ix_stock_transfers_carrier_id", "stock_transfers", ["carrier_id"], unique=False)

    op.create_table(
        "stock_transfer_items",
        sa.Column(
            "transfer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("stock_transfers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "variant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_variants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("qty", sa.Integer(), nullable=False),
        sa.Column("received_qty", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("transfer_id", "variant_id", name="pk_stock_transfer_items"),
        sa.ForeignKeyConstraint(["transfer_id"], ["stock_transfers.id"], name="fk_stock_transfer_items_transfer_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], name="fk_stock_transfer_items_variant_id", ondelete="RESTRICT"),
        sa.CheckConstraint("qty > 0", name="ck_stock_transfer_items_qty_positive"),
    )

    # ---------- audit_log ----------
    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity", sa.String(length=100), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("city_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("before", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_log"),
    )
    op.create_index("ix_audit_log_actor_id", "audit_log", ["actor_id"], unique=False)
    op.create_index("ix_audit_log_action", "audit_log", ["action"], unique=False)
    op.create_index("ix_audit_log_entity", "audit_log", ["entity"], unique=False)
    op.create_index("ix_audit_log_entity_id", "audit_log", ["entity_id"], unique=False)
    op.create_index("ix_audit_log_city_id", "audit_log", ["city_id"], unique=False)
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"], unique=False)

    # ---------- append-only триггеры ----------
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_update_delete()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'append-only table: UPDATE/DELETE forbidden';
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER stock_movements_append_only
        BEFORE UPDATE OR DELETE ON stock_movements
        FOR EACH ROW
        EXECUTE FUNCTION prevent_update_delete();
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_log_append_only
        BEFORE UPDATE OR DELETE ON audit_log
        FOR EACH ROW
        EXECUTE FUNCTION prevent_update_delete();
        """
    )


def downgrade() -> None:
    # Триггеры и функция.
    op.execute("DROP TRIGGER IF EXISTS stock_movements_append_only ON stock_movements")
    op.execute("DROP TRIGGER IF EXISTS audit_log_append_only ON audit_log")
    op.execute("DROP FUNCTION IF EXISTS prevent_update_delete()")

    # Таблицы (обратный порядок создания, из-за внешних ключей).
    op.drop_table("stock_transfer_items")
    op.drop_table("audit_log")
    op.drop_table("stock_transfers")
    op.drop_table("reservations")
    op.drop_table("stock_movements")
    op.drop_table("stock_levels")
    op.drop_table("city_offers")
    op.drop_table("warehouses")
    op.drop_table("cities")
    op.drop_table("product_certificates")
    op.drop_table("product_media")
    op.drop_table("nutrition")
    op.drop_table("product_variants")
    op.drop_table("products")
    op.drop_table("categories")
    op.drop_table("files")

    # Расширение pg_trgm (зависимость от триграммного индекса удалена вместе с таблицей products).
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")

    # ENUM-типы (не удаляются автоматически с таблицами).
    for enum_type in ENUM_TYPES:
        op.execute(f'DROP TYPE IF EXISTS "{enum_type}"')
