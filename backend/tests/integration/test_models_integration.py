"""
Integration tests for SQLAlchemy models against a real PostgreSQL database.

These tests are skipped by default — they require a running PostgreSQL instance.
To run them:

    docker-compose -f docker-compose.test.yml up -d
    export TEST_DATABASE_URL=postgresql+asyncpg://medivault_test:medivault_test@localhost:5433/medivault_test
    pytest tests/integration/ -v

Full implementation is tracked in MV-122.
"""
import pytest

from tests.integration.conftest import skip_if_no_db


@skip_if_no_db
class TestUserModelIntegration:
    async def test_create_user(self, db_session, make_user):
        # Placeholder — full implementation in MV-122
        pass

    async def test_user_unique_auth0_sub(self, db_session, make_user):
        # Placeholder — full implementation in MV-122
        pass


@skip_if_no_db
class TestFamilyMemberModelIntegration:
    async def test_create_family_member(self, db_session, make_user, make_family_member):
        # Placeholder — full implementation in MV-122
        pass

    async def test_cascade_delete_with_user(self, db_session, make_user, make_family_member):
        # Placeholder — full implementation in MV-122
        pass


@skip_if_no_db
class TestDocumentModelIntegration:
    async def test_create_document(self, db_session, make_user, make_family_member, make_document):
        # Placeholder — full implementation in MV-122
        pass

    async def test_document_processing_status_default(self, db_session, make_user, make_family_member, make_document):
        # Placeholder — full implementation in MV-122
        pass
