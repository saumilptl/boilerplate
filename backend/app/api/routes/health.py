"""Health check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database.db import get_session

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@router.get("/ready")
async def readiness_check(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    """
    Readiness check with database connectivity.

    Returns 200 if service is ready to accept traffic.
    """
    try:
        # Check database connectivity
        await session.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}

    except Exception as e:
        return {"status": "not_ready", "database": "disconnected", "error": str(e)}
