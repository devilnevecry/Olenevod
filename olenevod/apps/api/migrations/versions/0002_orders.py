"""Заказы: таблицы orders и order_items с индексами.

Revision ID: 0002_orders
Revises: 0001_initial_schema
Create Date: 2026-11-13 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002_orders"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ENUM_TYPES = ("order_status",)


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "city_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cities.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column("customer_phone", sa.String(length=50), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending_payment",
                "new",
                "confirmed",
                "assembling",
                "ready",
                "shipped",
                "delivered",
                "cancelled",
                "returned",
                name="order_status",
            ),
            server_default="pending_payment",
            nullable=False,
        ),
        sa.Column("total_amount", sa.Integer(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name="pk_orders"),
        sa.ForeignKeyConstraint(
            ["city_id"], ["cities.id"], name="fk_orders_city_id", ondelete="RESTRICT"
        ),
        sa.CheckConstraint("total_amount >= 0", name="ck_orders_total_amount_nonneg"),
    )
    op.create_index("ix_orders_city_id_status", "orders", ["city_id", "status"], unique=False)

    op.create_table(
        "order_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_variant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_variants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("qty", sa.Integer(), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_order_items"),
        sa.ForeignKeyConstraint(
            ["order_id"], ["orders.id"], name="fk_order_items_order_id", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["product_variant_id"],
            ["product_variants.id"],
            name="fk_order_items_product_variant_id",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint("qty > 0", name="ck_order_items_qty_positive"),
        sa.CheckConstraint("price >= 0", name="ck_order_items_price_nonneg"),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_order_items_order_id", table_name="order_items")
    op.drop_index("ix_orders_city_id_status", table_name="orders")
    op.drop_table("order_items")
    op.drop_table("orders")

    for enum_type in ENUM_TYPES:
        op.execute(f'DROP TYPE IF EXISTS "{enum_type}"')
