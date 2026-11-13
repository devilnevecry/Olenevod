"""Платежи: таблица payments.

Revision ID: 0003_payments
Revises: 0002_orders
Create Date: 2026-11-13 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003_payments"
down_revision: Union[str, None] = "0002_orders"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="pending", nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_payments"),
        sa.ForeignKeyConstraint(
            ["order_id"], ["orders.id"], name="fk_payments_order_id", ondelete="CASCADE"
        ),
        sa.CheckConstraint("amount >= 0", name="ck_payments_amount_nonneg"),
    )
    op.create_index("ix_payments_order_id", "payments", ["order_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_payments_order_id", table_name="payments")
    op.drop_table("payments")
