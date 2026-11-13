"""Уведомления: таблицы notification_log и notification_dead_letter.

Revision ID: 0007_notifications
Revises: 0006_auth
Create Date: 2026-11-13 17:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0007_notifications"
down_revision: str | None = "0006_auth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notification_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("recipient", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_notification_log"),
        sa.CheckConstraint(
            "status IN ('pending', 'sent', 'failed')",
            name="ck_notification_log_status_valid",
        ),
        sa.CheckConstraint("attempts >= 0", name="ck_notification_log_attempts_nonneg"),
    )
    op.create_index("ix_notification_log_recipient", "notification_log", ["recipient"], unique=False)
    op.create_index("ix_notification_log_status", "notification_log", ["status"], unique=False)

    op.create_table(
        "notification_dead_letter",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("log_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("recipient", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "failed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_notification_dead_letter"),
        sa.CheckConstraint("attempts >= 0", name="ck_notification_dead_letter_attempts_nonneg"),
    )
    op.create_index(
        "ix_notification_dead_letter_log_id",
        "notification_dead_letter",
        ["log_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_notification_dead_letter_log_id", table_name="notification_dead_letter")
    op.drop_table("notification_dead_letter")
    op.drop_index("ix_notification_log_status", table_name="notification_log")
    op.drop_index("ix_notification_log_recipient", table_name="notification_log")
    op.drop_table("notification_log")
