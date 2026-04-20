import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProviderProfile(Base):
    __tablename__ = "provider_profiles"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    licence_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    registration_council: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    licence_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # PENDING | VERIFIED | FAILED
    verification_status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship("User")  # noqa: F821
