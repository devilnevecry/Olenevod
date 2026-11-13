"""Доставка: таблицы delivery_zones и delivery_tariffs.

Revision ID: 0005_delivery
Revises: 0004_inventory
Create Date: 2026-11-13 15:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0005_delivery"
down_revision: str | None = "0004_inventory"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "delivery_zones",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "city_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cities.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("zone_name", sa.String(length=255), nullable=False),
        sa.Column("base_fee", sa.Integer(), server_default="0", nullable=False),
        sa.Column("per_kg_fee", sa.Integer(), server_default="0", nullable=False),
        sa.Column("free_from_amount", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_delivery_zones"),
        sa.ForeignKeyConstraint(
            ["city_id"],
            ["cities.id"],
            name="fk_delivery_zones_city_id",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("city_id", name="uq_delivery_zones_city_id"),
        sa.CheckConstraint("base_fee >= 0", name="ck_delivery_zones_base_fee_nonneg"),
        sa.CheckConstraint("per_kg_fee >= 0", name="ck_delivery_zones_per_kg_fee_nonneg"),
        sa.CheckConstraint(
            "free_from_amount IS NULL OR free_from_amount >= 0",
            name="ck_delivery_zones_free_from_amount_nonneg",
        ),
    )
    op.create_index("ix_delivery_zones_city_id", "delivery_zones", ["city_id"], unique=False)

    op.create_table(
        "delivery_tariffs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "zone_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("delivery_zones.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("estimated_days", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_delivery_tariffs"),
        sa.ForeignKeyConstraint(
            ["zone_id"],
            ["delivery_zones.id"],
            name="fk_delivery_tariffs_zone_id",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("zone_id", name="uq_delivery_tariffs_zone_id"),
        sa.CheckConstraint(
            "estimated_days IS NULL OR estimated_days >= 0",
            name="ck_delivery_tariffs_estimated_days_nonneg",
        ),
    )
    op.create_index("ix_delivery_tariffs_zone_id", "delivery_tariffs", ["zone_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_delivery_tariffs_zone_id", table_name="delivery_tariffs")
    op.drop_table("delivery_tariffs")
    op.drop_index("ix_delivery_zones_city_id", table_name="delivery_zones")
    op.drop_table("delivery_zones")
