import asyncio
import pytest
import pytest_asyncio
from tortoise import Tortoise
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.config import settings
from app.db.database import init_db, close_db
from app.scheduler.scheduler import scheduler
from main import app


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an instance of the default event loop for the test session.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def initialize_db():
    """
    Initialize test database with in-memory SQLite.
    """
    # Use in-memory SQLite for testing
    test_db_url = "sqlite://:memory:"

    await Tortoise.init(
        db_url=test_db_url,
        modules={"models": ["app.models.task", "app.models.log"]}
    )

    # Generate the schema
    await Tortoise.generate_schemas()

    yield

    # Cleanup
    await Tortoise.close_connections()


@pytest_asyncio.fixture(scope="module")
async def async_client():
    """
    Create an async test client for FastAPI.
    """
    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", follow_redirects=True) as client:
        yield client


@pytest.fixture(scope="module")
def client():
    """
    Create a synchronous test client for FastAPI.
    """
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clean_db():
    """
    Clean database before each test.
    """
    # Clean up all data before each test
    conn = Tortoise.get_connection("default")
    await conn.execute_query("DELETE FROM task_logs")
    await conn.execute_query("DELETE FROM tasks")
    await conn.execute_query("DELETE FROM sqlite_sequence")

    # Reset scheduler
    if scheduler.scheduler.running:
        scheduler.scheduler.shutdown()

    yield