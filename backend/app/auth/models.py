"""User authentication models."""

import uuid
from datetime import datetime

from fastapi_users import schemas
from pydantic import ConfigDict
from sqlmodel import TIMESTAMP, Column, Field

from app.infra.database.models import TimeStampedModel


class User(TimeStampedModel, table=True):
    """User database model compatible with FastAPI Users."""

    __tablename__ = "users"
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Primary key - FastAPI Users requires UUID
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)

    # Authentication fields
    email: str = Field(index=True, unique=True)
    hashed_password: str | None = None
    full_name: str

    # Status fields
    is_active: bool = True
    is_verified: bool = False
    is_superuser: bool = False

    # Security tracking
    last_login: datetime | None = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True), nullable=True))
    password_changed_at: datetime | None = Field(
        default=None, sa_column=Column(TIMESTAMP(timezone=True), nullable=True)
    )
    failed_login_attempts: int = 0
    locked_until: datetime | None = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True), nullable=True))


# FastAPI Users schemas
class UserCreate(schemas.BaseUserCreate):
    """Schema for user creation."""

    full_name: str


class UserRead(schemas.BaseUser[uuid.UUID]):
    """Schema for user response."""

    full_name: str
    created_at: datetime


class UserUpdate(schemas.BaseUserUpdate):
    """Schema for user update."""

    full_name: str | None = None
