import os
import uuid
from pathlib import Path

import pytest

# Provide required settings env vars before any app imports
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/testdb")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("MINIO_ACCESS_KEY", "minioadmin")
os.environ.setdefault("MINIO_SECRET_KEY", "minioadmin")
os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("MINIO_BUCKET", "medivault")
os.environ.setdefault("AUTH0_DOMAIN", "test.auth0.com")
os.environ.setdefault("AUTH0_AUDIENCE", "https://api.medivault.test")
os.environ.setdefault("ENCRYPTION_KEY", "dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdGtleXQ=")
os.environ.setdefault("ENVIRONMENT", "test")

# ---------------------------------------------------------------------------
# Minimal valid PDF bytes (no PHI — synthetic content only)
# Compatible with pdfminer.six for extraction tests.
# ---------------------------------------------------------------------------
MINIMAL_PDF_BYTES = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
    b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
    b"4 0 obj<</Length 44>>stream\n"
    b"BT /F1 12 Tf 100 700 Td (Hello World) Tj ET\n"
    b"endstream\nendobj\n"
    b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"xref\n0 6\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"0000000274 00000 n \n"
    b"0000000370 00000 n \n"
    b"trailer<</Size 6/Root 1 0 R>>\n"
    b"startxref\n441\n%%EOF"
)


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Return bytes of a minimal valid PDF with no PHI."""
    return MINIMAL_PDF_BYTES


@pytest.fixture
def sample_pdf_file(tmp_path: Path, sample_pdf_bytes: bytes) -> Path:
    """Write the minimal PDF to a temp file and return its Path."""
    p = tmp_path / "test_report.pdf"
    p.write_bytes(sample_pdf_bytes)
    return p


# ---------------------------------------------------------------------------
# Model factory fixtures — produce unsaved ORM instances with fake data.
# All names/emails are obviously synthetic (no PHI).
# ---------------------------------------------------------------------------

from app.models.user import User  # noqa: E402  (must be after env vars are set)
from app.models.family_member import FamilyMember  # noqa: E402
from app.models.document import Document  # noqa: E402


@pytest.fixture
def make_user():
    """Factory fixture that returns a callable producing unsaved User instances."""
    def _make(auth0_sub=None, email=None):
        return User(
            user_id=uuid.uuid4(),
            auth0_sub=auth0_sub or f"auth0|test_{uuid.uuid4().hex[:8]}",
            email=email or f"test_{uuid.uuid4().hex[:8]}@example.com",
        )
    return _make


@pytest.fixture
def make_family_member():
    """Factory fixture that returns a callable producing unsaved FamilyMember instances."""
    def _make(user_id, full_name="Test User", relationship="SELF", is_self=True):
        return FamilyMember(
            member_id=uuid.uuid4(),
            user_id=user_id,
            full_name=full_name,
            relationship=relationship,
            is_self=is_self,
        )
    return _make


@pytest.fixture
def make_document():
    """Factory fixture that returns a callable producing unsaved Document instances."""
    def _make(member_id, user_id, document_type="LAB_REPORT", storage_path=None):
        return Document(
            document_id=uuid.uuid4(),
            member_id=member_id,
            user_id=user_id,
            document_type=document_type,
            storage_path=storage_path or f"test/{uuid.uuid4().hex}.pdf",
        )
    return _make
