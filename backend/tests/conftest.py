"""Pytest configuration and shared fixtures."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from app.api.app import app
from app.config import Config, get_config
from app.infra.database.db import Database


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an event loop for the test session.

    This fixture ensures we have a consistent event loop throughout the test session.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config() -> Config:
    """
    Get test configuration.

    Override with test-specific settings if needed.
    """
    config = get_config()

    # Override database for testing (you may want to use a separate test database)
    # config.DATABASE.NAME = "app_db_test"

    return config


@pytest.fixture(scope="session")
async def test_db_engine(test_config: Config) -> AsyncGenerator[Any, None]:
    """
    Create a test database engine.

    Uses NullPool to avoid connection pooling in tests.
    """
    engine = create_async_engine(
        test_config.DATABASE.url,
        echo=test_config.DATABASE.ECHO,
        poolclass=NullPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_db_engine: Any) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a database session for a test.

    Each test gets a fresh transaction that is rolled back after the test.
    """
    async with AsyncSession(test_db_engine, expire_on_commit=False) as session:
        await session.begin()

        yield session

        await session.rollback()
        await session.close()


@pytest.fixture
async def db_manager(test_config: Config, test_db_engine: Any) -> Database:
    """
    Create a database manager for tests.

    Uses the test database engine.
    """
    manager = Database(test_config.DATABASE)
    manager._engine = test_db_engine
    return manager


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP client for testing API endpoints.

    Uses ASGI transport to directly call the FastAPI app without network overhead.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client


@pytest.fixture
def test_user_data() -> dict[str, Any]:
    """Example user data for testing."""
    return {
        "email": "test@example.com",
        "name": "Test User",
    }


@pytest.fixture
def test_organization_data() -> dict[str, Any]:
    """Example organization data for testing."""
    return {
        "name": "Test Organization",
        "slug": "test-org",
    }


# Marker for different test types
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.e2e = pytest.mark.e2e
pytest.mark.smoke = pytest.mark.smoke
