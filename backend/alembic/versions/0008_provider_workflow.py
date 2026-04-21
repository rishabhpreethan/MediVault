"""Create provider_access_requests and medical_encounters tables (MV-155)

Revision ID: 0008
Revises: 0007
Create Date: 2026-04-21
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- provider_access_requests -------------------------------------------
    op.create_table(
        "provider_access_requests",
        sa.Column(
            "request_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "provider_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "patient_member_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("family_members.member_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "passport_id_used",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("shared_passports.passport_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "notification_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("notifications.notification_id", ondelete="SET NULL"),
            nullable=True,
        ),
        # PENDING | ACCEPTED | DECLINED | EXPIRED
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "idx_provider_access_requests_provider",
        "provider_access_requests",
        ["provider_user_id"],
    )
    op.create_index(
        "idx_provider_access_requests_patient",
        "provider_access_requests",
        ["patient_member_id"],
    )
    op.create_index(
        "idx_provider_access_requests_status",
        "provider_access_requests",
        ["status"],
    )

    # -- medical_encounters --------------------------------------------------
    op.create_table(
        "medical_encounters",
        sa.Column(
            "encounter_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "provider_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "patient_member_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("family_members.member_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "access_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("provider_access_requests.request_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("encounter_date", sa.Date(), nullable=False),
        sa.Column("chief_complaint", sa.Text(), nullable=True),
        sa.Column("diagnosis_notes", sa.Text(), nullable=True),
        sa.Column("prescriptions_note", sa.Text(), nullable=True),
        sa.Column("follow_up_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "idx_medical_encounters_provider",
        "medical_encounters",
        ["provider_user_id"],
    )
    op.create_index(
        "idx_medical_encounters_patient",
        "medical_encounters",
        ["patient_member_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_medical_encounters_patient", table_name="medical_encounters")
    op.drop_index("idx_medical_encounters_provider", table_name="medical_encounters")
    op.drop_table("medical_encounters")
    op.drop_index("idx_provider_access_requests_status", table_name="provider_access_requests")
    op.drop_index("idx_provider_access_requests_patient", table_name="provider_access_requests")
    op.drop_index("idx_provider_access_requests_provider", table_name="provider_access_requests")
    op.drop_table("provider_access_requests")
