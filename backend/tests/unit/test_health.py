import sys
from types import ModuleType
from unittest.mock import MagicMock

# Stub heavy dependencies before any app imports
if "spacy" not in sys.modules:
    _fake_spacy = ModuleType("spacy")
    _fake_spacy.load = MagicMock()
    sys.modules["spacy"] = _fake_spacy

for _mod in ("boto3", "botocore", "botocore.exceptions"):
    if _mod not in sys.modules:
        _fake = ModuleType(_mod)
        if _mod == "botocore.exceptions":
            _fake.ClientError = Exception
        sys.modules[_mod] = _fake

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock

from app.main import app
from app.database import get_db


async def _mock_get_db():
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=AsyncMock())
    yield mock_session


@pytest.mark.asyncio
async def test_health_check_ok():
    app.dependency_overrides[get_db] = _mock_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "services" in data
