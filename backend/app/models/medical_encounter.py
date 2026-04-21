"""ORM model for MedicalEncounter."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MedicalEncounter(Base):
    __tablename__ = "medical_encounters"

    encounter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    provider_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("family_members.member_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    access_request_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("provider_access_requests.request_id", ondelete="SET NULL"),
        nullable=True,
    )
    encounter_date: Mapped[date] = mapped_column(Date(), nullable=False)
    chief_complaint: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    diagnosis_notes: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    prescriptions_note: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    follow_up_date: Mapped[Optional[date]] = mapped_column(Date(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    provider: Mapped["User"] = relationship("User", foreign_keys=[provider_user_id])  # noqa: F821
    patient_member: Mapped["FamilyMember"] = relationship("FamilyMember", foreign_keys=[patient_member_id])  # noqa: F821
    access_request: Mapped[Optional["ProviderAccessRequest"]] = relationship(  # noqa: F821
        "ProviderAccessRequest", back_populates="encounters"
    )
