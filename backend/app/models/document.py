import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("family_members.member_id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    document_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    facility_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    doctor_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    has_text_layer: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    processing_status: Mapped[str] = mapped_column(String(30), default="QUEUED", index=True)
    extraction_library: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    extracted_raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extraction_attempts: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    member: Mapped["FamilyMember"] = relationship("FamilyMember", back_populates="documents")  # noqa: F821
    medications: Mapped[list] = relationship("Medication", back_populates="document")
    lab_results: Mapped[list] = relationship("LabResult", back_populates="document")
    diagnoses: Mapped[list] = relationship("Diagnosis", back_populates="document")
    allergies: Mapped[list] = relationship("Allergy", back_populates="document")
    vitals: Mapped[list] = relationship("Vital", back_populates="document")
    doctors: Mapped[list] = relationship("Doctor", back_populates="document")
    procedures: Mapped[list] = relationship("Procedure", back_populates="document")
