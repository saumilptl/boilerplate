"""Base database models with common patterns."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import ConfigDict
from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class TimeStampedModel(SQLModel, table=False):
    """Base model with automatic timestamp tracking."""

    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"server_default": text("now()")},
        description="Record creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={
            "onupdate": datetime.now,
            "server_default": text("now()"),
        },
        description="Record last update timestamp",
    )


class LLMFriendlyModel(SQLModel):
    """Model with utilities for LLM consumption."""

    model_config = ConfigDict(from_attributes=True)

    def to_llm_dict(self) -> dict[str, Any]:
        """
        Convert model to dictionary optimized for LLM consumption.

        Excludes internal fields and None values.
        """
        return self.model_dump(
            exclude={"id", "created_at", "updated_at"},
            exclude_none=True,
        )

    @classmethod
    def get_llm_schema(cls, exclude_fields: set[str] | None = None) -> dict[str, Any]:
        """
        Get clean JSON schema for LLM tool calling.

        Args:
            exclude_fields: Additional fields to exclude

        Returns:
            JSON schema dictionary
        """
        schema = cls.model_json_schema()

        # Default exclusions
        default_exclude = {"id", "created_at", "updated_at"}
        if exclude_fields:
            default_exclude.update(exclude_fields)

        # Remove excluded fields from schema
        if "properties" in schema:
            for field in default_exclude:
                schema["properties"].pop(field, None)

            # Update required fields
            if "required" in schema:
                schema["required"] = [f for f in schema["required"] if f not in default_exclude]

        return schema


class BaseModel(LLMFriendlyModel, TimeStampedModel, table=False):
    """Base model with UUID primary key and timestamps."""

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique identifier",
    )


class AuditableModel(SQLModel, table=False):
    """Model with audit trail tracking."""

    created_by_id: UUID | None = Field(
        default=None,
        foreign_key="users.id",
        description="User who created the record",
    )
    updated_by_id: UUID | None = Field(
        default=None,
        foreign_key="users.id",
        description="User who last updated the record",
    )


class SoftDeleteModel(SQLModel, table=False):
    """Model with soft delete support."""

    deleted_at: datetime | None = Field(
        default=None,
        description="Soft delete timestamp",
    )
    deleted_by_id: UUID | None = Field(
        default=None,
        foreign_key="users.id",
        description="User who deleted the record",
    )

    @property
    def is_deleted(self) -> bool:
        """Check if record is soft deleted."""
        return self.deleted_at is not None


class PaginationInfo(SQLModel):
    """Pagination metadata."""

    page: int = Field(description="Current page number")
    page_size: int = Field(description="Items per page")
    total_count: int = Field(description="Total number of items")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")


def create_jsonb_column(**kwargs: Any) -> Any:
    """Create a JSONB column for PostgreSQL."""
    return Field(sa_column=Column(JSONB, **kwargs))
