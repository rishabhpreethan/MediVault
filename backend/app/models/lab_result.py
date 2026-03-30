import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LabResult(Base):
    __tablename__ = "lab_results"

    result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("family_members.member_id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.document_id", ondelete="SET NULL"), nullable=True
    )
    test_name: Mapped[str] = mapped_column(String(255), nullable=False)
    test_name_normalized: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    value_text: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reference_low: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    reference_high: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    flag: Mapped[str] = mapped_column(String(20), default="NORMAL")
    test_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    confidence_score: Mapped[str] = mapped_column(String(10), default="MEDIUM")
    is_manual_entry: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    member: Mapped["FamilyMember"] = relationship("FamilyMember", back_populates="lab_results")  # noqa: F821
    document: Mapped[Optional["Document"]] = relationship("Document", back_populates="lab_results")  # noqa: F821
