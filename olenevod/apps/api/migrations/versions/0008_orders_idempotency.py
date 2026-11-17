"""Заказы: колонка idempotency_key с уникальным ограничением.

Revision ID: 0008_orders_idempotency
Revises: 0007_notifications
Create Date: 2026-11-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0008_orders_idempotency"
down_revision: Union[str, None] = "0007_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column("idempotency_key", sa.String(length=200), nullable=True),
    )
    op.create_unique_constraint(
        "uq_orders_idempotency_key", "orders", ["idempotency_key"]
    )
    op.create_index(
        "ix_orders_idempotency_key", "orders", ["idempotency_key"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_orders_idempotency_key", table_name="orders")
    op.drop_constraint("uq_orders_idempotency_key", "orders", type_="unique")
    op.drop_column("orders", "idempotency_key")
