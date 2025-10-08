"""Auth dependencies for FastAPI."""

import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    CookieTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.password.manager import UserManager
from app.config import config
from app.infra.database.db import get_session

cfg = config()


async def get_user_db(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    """Get a SQLAlchemy user database with proper session."""
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    """Get a configured user manager with DB access."""
    yield UserManager(user_db=user_db)


def get_jwt_strategy() -> JWTStrategy:
    """Get JWT strategy for token generation."""
    return JWTStrategy(
        secret=cfg.SECURITY.JWT_SECRET_KEY,
        lifetime_seconds=cfg.SECURITY.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# Cookie transport for browser clients
cookie_transport = CookieTransport(
    cookie_name="auth-token",
    cookie_max_age=cfg.SECURITY.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    cookie_secure=True,  # Required for HTTPS (ngrok)
    cookie_httponly=True,
    cookie_samesite="none",  # Required for cross-site cookies through ngrok
)

# Bearer token transport for API clients
bearer_transport = BearerTransport(tokenUrl="api/auth/bearer/login")

# Authentication backends
cookie_backend = AuthenticationBackend(
    name="cookie",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

bearer_backend = AuthenticationBackend(
    name="bearer",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


def get_fastapi_users() -> FastAPIUsers[User, uuid.UUID]:
    """Create the FastAPI Users instance with proper dependencies."""
    return FastAPIUsers[User, uuid.UUID](
        get_user_manager,
        [cookie_backend, bearer_backend],
    )


# Create and export the instance
fastapi_users = get_fastapi_users()

# Ready-to-use dependencies for routes
current_user = fastapi_users.current_user(active=True, verified=True)
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
