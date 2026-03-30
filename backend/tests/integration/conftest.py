"""
Integration tests require a running PostgreSQL.
Run with: docker-compose -f docker-compose.test.yml up -d
Then: pytest tests/integration/ -v

The TEST_DATABASE_URL env var must be set for integration tests to run.
When using docker-compose.test.yml the postgres-test service listens on
localhost:5433 with db/user/password all set to 'medivault_test'.

Example:
    export TEST_DATABASE_URL=postgresql+asyncpg://medivault_test:medivault_test@localhost:5433/medivault_test
    pytest tests/integration/ -v
"""
import os

import pytest

# Integration tests are skipped unless TEST_DATABASE_URL is set
# (set by docker-compose.test.yml or CI environment)
SKIP_INTEGRATION = not os.environ.get("TEST_DATABASE_URL")

skip_if_no_db = pytest.mark.skipif(
    SKIP_INTEGRATION,
    reason="Integration tests require TEST_DATABASE_URL env var (run with docker-compose.test.yml)",
)
