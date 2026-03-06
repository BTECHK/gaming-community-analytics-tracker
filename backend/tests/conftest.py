"""Pytest configuration and fixtures for backend tests."""

import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.config import get_settings

from tests.mocks.valkey_mock import MockValkeyJobStore


# Test database URL (uses same DB but could use a separate test DB)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(test_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client with database override."""

    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_topic_data() -> dict:
    """Sample topic data for testing."""
    return {
        "slug": "test-topic",
        "name": "Test Topic",
        "sentiment": {
            "positive": 60.0,
            "neutral": 30.0,
            "negative": 10.0,
        },
        "post_count": 42,
        "source_mix": {"reddit": 20, "youtube": 22},
        "summary": "This is a test topic summary.",
        "quotes": [
            {
                "text": "Test quote 1",
                "platform": "reddit",
                "sentiment": "positive",
            }
        ],
        "period": {
            "start": "2026-01-01T00:00:00Z",
            "end": "2026-01-07T00:00:00Z",
        },
        "confidence": 0.85,
    }


@pytest.fixture
def sample_feedback_data() -> dict:
    """Sample feedback data for testing."""
    return {
        "topic_slug": "test-topic",
        "vote_type": "thumbs_up",
        "session_id": "test-session-123",
    }


@pytest.fixture(autouse=True)
def mock_valkey_store():
    """Automatically mock ValkeyJobStore when VALKEY_URL is not set or is 'mock://'.

    This fixture runs automatically for all tests and patches ValkeyJobStore
    with MockValkeyJobStore to enable testing without a real Redis/Valkey instance.
    """
    valkey_url = os.environ.get("VALKEY_URL", "mock://")

    if valkey_url == "mock://" or not valkey_url:
        # Reset the mock instance before each test
        MockValkeyJobStore.reset()

        with patch(
            "app.nlp.valkey_store.ValkeyJobStore",
            MockValkeyJobStore,
        ):
            yield MockValkeyJobStore
    else:
        # Real Valkey URL provided, don't mock
        yield None


@pytest_asyncio.fixture
async def valkey_mock_instance(mock_valkey_store):
    """Get a MockValkeyJobStore instance for direct testing.

    Use this fixture when you need to interact with the mock store directly
    in your tests.
    """
    if mock_valkey_store is not None:
        instance = await MockValkeyJobStore.get_instance()
        yield instance
        instance.clear_storage()
        MockValkeyJobStore.reset()
    else:
        # When using real Valkey, import and return the real store
        from app.nlp.valkey_store import ValkeyJobStore
        instance = await ValkeyJobStore.get_instance()
        yield instance
