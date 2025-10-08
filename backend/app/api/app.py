"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from app.api.middleware.security import add_security_middleware, exception_middleware
from app.api.routes import health, tasks
from app.auth.password import router as auth_router
from app.config import config as get_app_config
from app.di import get_container
from app.infra.monitoring.logging.logger import logger


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    app_config = get_app_config()
    logger.info("Application starting up", service=app_config.SERVICE_NAME, environment=app_config.ENVIRONMENT)

    # Initialize dependency injection container
    container = get_container()

    try:
        # Initialize resources
        container.init_resources()  # type: ignore[attr-defined]
        logger.info("Resources initialized")

        yield

    finally:
        # Shutdown resources
        logger.info("Application shutting down")
        container.shutdown_resources()  # type: ignore[attr-defined]

        # Close database connections
        from app.infra.database.db import get_database

        db = get_database()
        await db.close()

        logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app_config = get_app_config()

    app = FastAPI(
        title="Backend API",
        description="Production-ready FastAPI backend boilerplate",
        version="0.1.0",
        docs_url="/docs" if app_config.DEBUG else None,
        redoc_url="/redoc" if app_config.DEBUG else None,
        lifespan=lifespan,
    )

    # Add exception middleware first (outermost)
    app.middleware("http")(exception_middleware)

    # Add security middleware
    add_security_middleware(app, app_config.SECURITY)

    # Create API router
    api_router = APIRouter(prefix="/api")

    # Include route modules
    api_router.include_router(health.router)
    api_router.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    api_router.include_router(tasks.router)

    # Register API router
    app.include_router(api_router)

    logger.info(
        "FastAPI application created",
        debug=app_config.DEBUG,
        environment=app_config.ENVIRONMENT,
    )

    return app


# Create application instance
app = create_app()
