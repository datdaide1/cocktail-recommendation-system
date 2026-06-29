import pytest
import asyncio
from app.db.redis import redis_client
from app.db.postgres import engine

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def asyncio_default_test_loop_scope():
    return "session"

@pytest.fixture(scope="session", autouse=True)
def cleanup_resources(event_loop):
    yield
    # Run cleanup synchronously on the session loop
    async def _cleanup():
        try:
            await engine.dispose()
        except Exception:
            pass
        try:
            await redis_client.aclose()
        except Exception:
            pass
    event_loop.run_until_complete(_cleanup())
