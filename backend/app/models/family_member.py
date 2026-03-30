import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship as sa_relationship

from app.database import Base


class FamilyMember(Base):
    __tablename__ = "family_members"

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    relationship: Mapped[str] = mapped_column(String(50), nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    blood_group: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    is_self: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = sa_relationship("User", back_populates="family_members")  # noqa: F821
    documents: Mapped[list] = sa_relationship(
        "Document", back_populates="member", cascade="all, delete-orphan"
    )
    medications: Mapped[list] = sa_relationship(
        "Medication", back_populates="member", cascade="all, delete-orphan"
    )
    lab_results: Mapped[list] = sa_relationship(
        "LabResult", back_populates="member", cascade="all, delete-orphan"
    )
    diagnoses: Mapped[list] = sa_relationship(
        "Diagnosis", back_populates="member", cascade="all, delete-orphan"
    )
    allergies: Mapped[list] = sa_relationship(
        "Allergy", back_populates="member", cascade="all, delete-orphan"
    )
    vitals: Mapped[list] = sa_relationship(
        "Vital", back_populates="member", cascade="all, delete-orphan"
    )
    doctors: Mapped[list] = sa_relationship(
        "Doctor", back_populates="member", cascade="all, delete-orphan"
    )
    procedures: Mapped[list] = sa_relationship(
        "Procedure", back_populates="member", cascade="all, delete-orphan"
    )
    passports: Mapped[list] = sa_relationship(
        "SharedPassport", back_populates="member", cascade="all, delete-orphan"
    )
