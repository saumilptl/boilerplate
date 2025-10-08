"""Tests for health check endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient) -> None:
    """
    Test the health check endpoint returns 200 OK.

    This is a smoke test to verify the API is running.
    """
    response = await async_client.get("/api/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert "service" in data
    assert "timestamp" in data


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_health_check_database(async_client: AsyncClient) -> None:
    """
    Test the health check endpoint includes database status.

    Verifies database connectivity is working.
    """
    response = await async_client.get("/api/health")

    assert response.status_code == 200
    data = response.json()

    assert "database" in data
    assert data["database"]["status"] == "connected"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_structure(async_client: AsyncClient) -> None:
    """
    Test the health check response has the expected structure.

    Validates the response schema.
    """
    response = await async_client.get("/api/health")

    assert response.status_code == 200
    data = response.json()

    # Required fields
    assert "status" in data
    assert "service" in data
    assert "timestamp" in data
    assert "database" in data

    # Status should be a string
    assert isinstance(data["status"], str)

    # Service info should be a dict
    assert isinstance(data["service"], dict)
    assert "name" in data["service"]

    # Timestamp should be a string (ISO format)
    assert isinstance(data["timestamp"], str)

    # Database should have status
    assert isinstance(data["database"], dict)
    assert "status" in data["database"]
