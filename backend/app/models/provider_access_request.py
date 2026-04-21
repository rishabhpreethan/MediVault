"""ORM model for ProviderAccessRequest."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProviderAccessRequest(Base):
    __tablename__ = "provider_access_requests"

    request_id: Mapped[uuid.UUID] = mapped_column(
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
    passport_id_used: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shared_passports.passport_id", ondelete="SET NULL"),
        nullable=True,
    )
    notification_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("notifications.notification_id", ondelete="SET NULL"),
        nullable=True,
    )
    # PENDING | ACCEPTED | DECLINED | EXPIRED
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", index=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    provider: Mapped["User"] = relationship("User", foreign_keys=[provider_user_id])  # noqa: F821
    patient_member: Mapped["FamilyMember"] = relationship("FamilyMember", foreign_keys=[patient_member_id])  # noqa: F821
    encounters: Mapped[list["MedicalEncounter"]] = relationship(  # noqa: F821
        "MedicalEncounter", back_populates="access_request", cascade="all, delete-orphan"
    )
