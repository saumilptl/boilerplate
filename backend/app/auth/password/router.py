"""Password authentication routes."""

from fastapi import APIRouter

from app.auth.dependencies import bearer_backend, cookie_backend, fastapi_users
from app.auth.models import UserCreate, UserRead, UserUpdate

# Create base router
router = APIRouter()

# Add cookie authentication routes (for browser clients)
router.include_router(
    fastapi_users.get_auth_router(cookie_backend),
    prefix="/cookie",
)

# Add bearer token authentication routes (for API clients)
router.include_router(
    fastapi_users.get_auth_router(bearer_backend),
    prefix="/bearer",
)

# Add user registration routes
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
)

# Add password reset functionality
router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/forgot-password",
)

# Add users management routes
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
)
