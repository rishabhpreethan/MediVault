import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Vital(Base):
    __tablename__ = "vitals"

    vital_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("family_members.member_id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.document_id", ondelete="SET NULL"), nullable=True
    )
    vital_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    recorded_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    confidence_score: Mapped[str] = mapped_column(String(10), default="MEDIUM")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    member: Mapped["FamilyMember"] = relationship("FamilyMember", back_populates="vitals")  # noqa: F821
    document: Mapped[Optional["Document"]] = relationship("Document", back_populates="vitals")  # noqa: F821
