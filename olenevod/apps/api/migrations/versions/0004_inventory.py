"""Инвентарь: таблицы inventory_reservations и outbox.

Revision ID: 0004_inventory
Revises: 0003_payments
Create Date: 2026-11-13 14:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0004_inventory"
down_revision: str | None = "0003_payments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ENUM_TYPES = ("inventory_reservation_status",)


def upgrade() -> None:
    op.create_table(
        "inventory_reservations",
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
        sa.Column(
            "city_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cities.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("qty", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "active",
                "committed",
                "released",
                "expired",
                name="inventory_reservation_status",
            ),
            server_default="active",
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("idempotency_key", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_inventory_reservations"),
        sa.ForeignKeyConstraint(
            ["warehouse_id"],
            ["warehouses.id"],
            name="fk_inventory_reservations_warehouse_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["variant_id"],
            ["product_variants.id"],
            name="fk_inventory_reservations_variant_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["city_id"],
            ["cities.id"],
            name="fk_inventory_reservations_city_id",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("qty > 0", name="ck_inventory_reservations_qty_positive"),
    )
    op.create_index("ix_inventory_reservations_order_id", "inventory_reservations", ["order_id"], unique=False)
    op.create_index("ix_inventory_reservations_warehouse_id", "inventory_reservations", ["warehouse_id"], unique=False)
    op.create_index("ix_inventory_reservations_variant_id", "inventory_reservations", ["variant_id"], unique=False)
    op.create_index("ix_inventory_reservations_city_id", "inventory_reservations", ["city_id"], unique=False)
    op.create_index("ix_inventory_reservations_expires_at", "inventory_reservations", ["expires_at"], unique=False)
    op.create_index("ix_inventory_reservations_idempotency_key", "inventory_reservations", ["idempotency_key"], unique=False)

    op.create_table(
        "outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("aggregate_type", sa.String(length=100), nullable=False),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_outbox"),
    )
    op.create_index("ix_outbox_aggregate_type", "outbox", ["aggregate_type"], unique=False)
    op.create_index("ix_outbox_aggregate_id", "outbox", ["aggregate_id"], unique=False)
    op.create_index("ix_outbox_event_type", "outbox", ["event_type"], unique=False)
    op.create_index("ix_outbox_created_at", "outbox", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_outbox_created_at", table_name="outbox")
    op.drop_index("ix_outbox_event_type", table_name="outbox")
    op.drop_index("ix_outbox_aggregate_id", table_name="outbox")
    op.drop_index("ix_outbox_aggregate_type", table_name="outbox")
    op.drop_table("outbox")

    op.drop_index("ix_inventory_reservations_idempotency_key", table_name="inventory_reservations")
    op.drop_index("ix_inventory_reservations_expires_at", table_name="inventory_reservations")
    op.drop_index("ix_inventory_reservations_city_id", table_name="inventory_reservations")
    op.drop_index("ix_inventory_reservations_variant_id", table_name="inventory_reservations")
    op.drop_index("ix_inventory_reservations_warehouse_id", table_name="inventory_reservations")
    op.drop_index("ix_inventory_reservations_order_id", table_name="inventory_reservations")
    op.drop_table("inventory_reservations")

    for enum_type in ENUM_TYPES:
        op.execute(f'DROP TYPE IF EXISTS "{enum_type}"')
