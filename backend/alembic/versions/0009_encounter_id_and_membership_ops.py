"""Add encounter_id FK to diagnoses/medications; vault access request notification support

Revision ID: 0009
Revises: 0008
Create Date: 2026-04-22
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add encounter_id to diagnoses
    op.add_column(
        "diagnoses",
        sa.Column(
            "encounter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("medical_encounters.encounter_id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_diagnoses_encounter_id", "diagnoses", ["encounter_id"])

    # Add encounter_id to medications
    op.add_column(
        "medications",
        sa.Column(
            "encounter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("medical_encounters.encounter_id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_medications_encounter_id", "medications", ["encounter_id"])


def downgrade() -> None:
    op.drop_index("ix_medications_encounter_id", table_name="medications")
    op.drop_column("medications", "encounter_id")
    op.drop_index("ix_diagnoses_encounter_id", table_name="diagnoses")
    op.drop_column("diagnoses", "encounter_id")
