"""Initial schema — all core tables

Revision ID: 0001
Revises:
Create Date: 2026-03-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("auth0_sub", sa.String(128), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone_number", sa.String(20), nullable=True),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("auth0_sub", name="uq_users_auth0_sub"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("idx_users_auth0_sub", "users", ["auth0_sub"])

    # ── family_members ─────────────────────────────────────────────────────────
    op.create_table(
        "family_members",
        sa.Column("member_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("relationship", sa.String(50), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("blood_group", sa.String(10), nullable=True),
        sa.Column("is_self", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_family_members_user_id", "family_members", ["user_id"])

    # ── documents ─────────────────────────────────────────────────────────────
    op.create_table(
        "documents",
        sa.Column("document_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "member_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("family_members.member_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("document_date", sa.Date(), nullable=True),
        sa.Column("facility_name", sa.String(255), nullable=True),
        sa.Column("doctor_name", sa.String(255), nullable=True),
        sa.Column("storage_path", sa.String(512), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("has_text_layer", sa.Boolean(), nullable=True),
        sa.Column("processing_status", sa.String(30), nullable=False, server_default="QUEUED"),
        sa.Column("extraction_library", sa.String(50), nullable=True),
        sa.Column("extracted_raw_text", sa.Text(), nullable=True),
        sa.Column("extraction_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_documents_member_id", "documents", ["member_id"])
    op.create_index("idx_documents_processing_status", "documents", ["processing_status"])

    # ── medications ────────────────────────────────────────────────────────────
    op.create_table(
        "medications",
        sa.Column("medication_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "member_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("family_members.member_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.document_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("drug_name", sa.String(255), nullable=False),
        sa.Column("drug_name_normalized", sa.String(255), nullable=True),
        sa.Column("dosage", sa.String(100), nullable=True),
        sa.Column("frequency", sa.String(100), nullable=True),
        sa.Column("route", sa.String(50), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("confidence_score", sa.String(10), nullable=False, server_default="MEDIUM"),
        sa.Column("is_manual_entry", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_medications_member_id", "medications", ["member_id"])
    op.create_index("idx_medications_is_active", "medications", ["is_active"])

    # ── lab_results ────────────────────────────────────────────────────────────
    op.create_table(
        "lab_results",
        sa.Column("result_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "member_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("family_members.member_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.document_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("test_name", sa.String(255), nullable=False),
        sa.Column("test_name_normalized", sa.String(255), nullable=True),
        sa.Column("value", sa.Numeric(12, 4), nullable=True),
        sa.Column("value_text", sa.String(100), nullable=True),
        sa.Column("unit", sa.String(50), nullable=True),
        sa.Column("reference_low", sa.Numeric(12, 4), nullable=True),
        sa.Column("reference_high", sa.Numeric(12, 4), nullable=True),
        sa.Column("flag", sa.String(20), nullable=False, server_default="NORMAL"),
        sa.Column("test_date", sa.Date(), nullable=True),
        sa.Column("confidence_score", sa.String(10), nullable=False, server_default="MEDIUM"),
        sa.Column("is_manual_entry", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_lab_results_member_id", "lab_results", ["member_id"])
    op.create_index("idx_lab_results_test_name_normalized", "lab_results", ["test_name_normalized"])
    op.create_index("idx_lab_results_test_date", "lab_results", ["test_date"])

    # ── diagnoses ─────────────────────────────────────────────────────────────
    op.create_table(
        "diagnoses",
        sa.Column("diagnosis_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "member_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("family_members.member_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.document_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("condition_name", sa.String(255), nullable=False),
        sa.Column("condition_normalized", sa.String(255), nullable=True),
        sa.Column("icd10_code", sa.String(20), nullable=True),
        sa.Column("diagnosed_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="UNKNOWN"),
        sa.Column("confidence_score", sa.String(10), nullable=False, server_default="MEDIUM"),
        sa.Column("is_manual_entry", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_diagnoses_member_id", "diagnoses", ["member_id"])
    op.create_index("idx_diagnoses_status", "diagnoses", ["status"])

    # ── allergies ─────────────────────────────────────────────────────────────
    op.create_table(
        "allergies",
        sa.Column("allergy_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "member_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("family_members.member_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.document_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("allergen_name", sa.String(255), nullable=False),
        sa.Column("reaction_type", sa.String(255), nullable=True),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("confidence_score", sa.String(10), nullable=False, server_default="MEDIUM"),
        sa.Column("is_manual_entry", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_allergies_member_id", "allergies", ["member_id"])

    # ── vitals ────────────────────────────────────────────────────────────────
    op.create_table(
        "vitals",
        sa.Column("vital_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "member_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("family_members.member_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.document_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("vital_type", sa.String(50), nullable=False),
        sa.Column("value", sa.Numeric(8, 2), nullable=False),
        sa.Column("unit", sa.String(30), nullable=True),
        sa.Column("recorded_date", sa.Date(), nullable=True),
        sa.Column("confidence_score", sa.String(10), nullable=False, server_default="MEDIUM"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_vitals_member_id", "vitals", ["member_id"])
    op.create_index("idx_vitals_type_date", "vitals", ["vital_type", "recorded_date"])

    # ── doctors ────────────────────────────────────────────────────────────────
    op.create_table(
        "doctors",
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "member_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("family_members.member_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.document_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("doctor_name", sa.String(255), nullable=True),
        sa.Column("specialization", sa.String(255), nullable=True),
        sa.Column("facility_name", sa.String(255), nullable=True),
        sa.Column("visit_date", sa.Date(), nullable=True),
        sa.Column("confidence_score", sa.String(10), nullable=False, server_default="MEDIUM"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_doctors_member_id", "doctors", ["member_id"])

    # ── procedures ────────────────────────────────────────────────────────────
    op.create_table(
        "procedures",
        sa.Column("procedure_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "member_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("family_members.member_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.document_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("procedure_name", sa.String(255), nullable=False),
        sa.Column("procedure_date", sa.Date(), nullable=True),
        sa.Column("outcome", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.String(10), nullable=False, server_default="MEDIUM"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_procedures_member_id", "procedures", ["member_id"])

    # ── shared_passports ───────────────────────────────────────────────────────
    op.create_table(
        "shared_passports",
        sa.Column("passport_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "member_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("family_members.member_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "visible_sections",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default='["conditions","medications","allergies","labs","vitals","last_visit"]',
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("access_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("idx_passports_member_id", "shared_passports", ["member_id"])
    op.create_index("idx_passports_is_active", "shared_passports", ["is_active"])

    # ── passport_access_log ────────────────────────────────────────────────────
    op.create_table(
        "passport_access_log",
        sa.Column("log_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "passport_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("shared_passports.passport_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("accessed_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("ip_hash", sa.String(64), nullable=True),
    )
    op.create_index("idx_passport_access_passport_id", "passport_access_log", ["passport_id"])

    # ── correction_audit ───────────────────────────────────────────────────────
    op.create_table(
        "correction_audit",
        sa.Column("audit_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column(
            "corrected_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id"),
            nullable=True,
        ),
        sa.Column("corrected_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("correction_audit")
    op.drop_table("passport_access_log")
    op.drop_table("shared_passports")
    op.drop_table("procedures")
    op.drop_table("doctors")
    op.drop_table("vitals")
    op.drop_table("allergies")
    op.drop_table("diagnoses")
    op.drop_table("lab_results")
    op.drop_table("medications")
    op.drop_table("documents")
    op.drop_table("family_members")
    op.drop_table("users")
