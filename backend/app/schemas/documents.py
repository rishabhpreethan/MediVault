"""Pydantic schemas for the documents API."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    document_id: str
    member_id: str
    document_type: str
    document_date: Optional[date]
    original_filename: str
    file_size_bytes: int
    processing_status: str
    has_text_layer: Optional[bool]
    extraction_library: Optional[str]
    uploaded_at: datetime
    processed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int
