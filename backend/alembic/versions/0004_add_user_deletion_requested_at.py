"""Add deletion_requested_at column to users table

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-10
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "deletion_requested_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "deletion_requested_at")
