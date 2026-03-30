import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Allergy(Base):
    __tablename__ = "allergies"

    allergy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("family_members.member_id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.document_id", ondelete="SET NULL"), nullable=True
    )
    allergen_name: Mapped[str] = mapped_column(String(255), nullable=False)
    reaction_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    confidence_score: Mapped[str] = mapped_column(String(10), default="MEDIUM")
    is_manual_entry: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    member: Mapped["FamilyMember"] = relationship("FamilyMember", back_populates="allergies")  # noqa: F821
    document: Mapped[Optional["Document"]] = relationship("Document", back_populates="allergies")  # noqa: F821
