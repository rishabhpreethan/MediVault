"""Add onboarding fields: role + onboarding_completed on users,
height_cm + weight_kg on family_members, new provider_profiles table (MV-150)

Revision ID: 0007
Revises: 0006
Create Date: 2026-04-20
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- users: role + onboarding_completed ---------------------------------
    op.add_column(
        "users",
        sa.Column("role", sa.String(20), nullable=False, server_default="PATIENT"),
    )
    op.add_column(
        "users",
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default="false"),
    )

    # -- family_members: height + weight ------------------------------------
    op.add_column(
        "family_members",
        sa.Column("height_cm", sa.Float(), nullable=True),
    )
    op.add_column(
        "family_members",
        sa.Column("weight_kg", sa.Float(), nullable=True),
    )

    # -- provider_profiles --------------------------------------------------
    op.create_table(
        "provider_profiles",
        sa.Column(
            "profile_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("licence_number", sa.String(50), nullable=True),
        sa.Column("registration_council", sa.String(100), nullable=True),
        sa.Column("licence_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("verification_status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("idx_provider_profiles_user_id", "provider_profiles", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_provider_profiles_user_id", table_name="provider_profiles")
    op.drop_table("provider_profiles")
    op.drop_column("family_members", "weight_kg")
    op.drop_column("family_members", "height_cm")
    op.drop_column("users", "onboarding_completed")
    op.drop_column("users", "role")
