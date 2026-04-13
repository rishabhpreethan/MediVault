"""Add correction_audit table for manual field corrections

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-10
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    table_exists = conn.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
            "WHERE table_name = 'correction_audit')"
        )
    ).scalar()

    if not table_exists:
        op.create_table(
            "correction_audit",
            sa.Column(
                "audit_id",
                postgresql.UUID(as_uuid=True),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("entity_type", sa.String(50), nullable=False),
            sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("field_name", sa.String(100), nullable=False),
            sa.Column("old_value", sa.Text, nullable=True),
            sa.Column("new_value", sa.Text, nullable=True),
            sa.Column(
                "corrected_by",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.user_id"),
                nullable=True,
            ),
            sa.Column(
                "corrected_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
            ),
        )

    index_exists = conn.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM pg_indexes "
            "WHERE indexname = 'idx_correction_audit_entity')"
        )
    ).scalar()

    if not index_exists:
        op.create_index(
            "idx_correction_audit_entity",
            "correction_audit",
            ["entity_type", "entity_id"],
        )


def downgrade() -> None:
    op.drop_index("idx_correction_audit_entity", table_name="correction_audit")
    op.drop_table("correction_audit")
