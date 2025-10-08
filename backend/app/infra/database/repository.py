"""Generic repository pattern for database operations."""

from collections.abc import Sequence
from typing import Any, ClassVar, Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from app.infra.database.models import PaginationInfo, SoftDeleteModel
from app.infra.monitoring.logging.logger import logger

T = TypeVar("T", bound=SQLModel)


class Repository(Generic[T]):
    """
    Generic repository for database operations.

    Provides common CRUD operations with support for:
    - Bulk operations
    - Soft deletes
    - Pagination
    - Full-text search
    - Complex filtering
    """

    model_class: ClassVar[type[T]]

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session.

        Args:
            session: Async database session
        """
        self.session = session

    async def get_by_id(self, id: UUID | int, include_deleted: bool = False) -> T | None:
        """
        Get a single record by ID.

        Args:
            id: Record ID
            include_deleted: Include soft-deleted records

        Returns:
            Model instance or None if not found
        """
        stmt = select(self.model_class).where(self.model_class.id == id)

        # Exclude soft-deleted records
        if not include_deleted and issubclass(self.model_class, SoftDeleteModel):
            stmt = stmt.where(self.model_class.deleted_at.is_(None))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_ids(self, ids: list[UUID | int], include_deleted: bool = False) -> dict[UUID | int, T]:
        """
        Get multiple records by IDs.

        Args:
            ids: List of record IDs
            include_deleted: Include soft-deleted records

        Returns:
            Dictionary mapping ID to model instance
        """
        if not ids:
            return {}

        stmt = select(self.model_class).where(self.model_class.id.in_(ids))

        if not include_deleted and issubclass(self.model_class, SoftDeleteModel):
            stmt = stmt.where(self.model_class.deleted_at.is_(None))

        result = await self.session.execute(stmt)
        records = result.scalars().all()

        return {record.id: record for record in records}

    async def create(self, obj: T) -> T:
        """
        Create a new record.

        Args:
            obj: Model instance to create

        Returns:
            Created model instance with generated fields
        """
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)

        logger.debug("Created record", model=self.model_class.__name__, id=obj.id)

        return obj

    async def bulk_create(self, objects: list[T]) -> list[T]:
        """
        Create multiple records in bulk.

        Args:
            objects: List of model instances to create

        Returns:
            List of created model instances
        """
        if not objects:
            return []

        self.session.add_all(objects)
        await self.session.flush()

        for obj in objects:
            await self.session.refresh(obj)

        logger.debug(
            "Bulk created records",
            model=self.model_class.__name__,
            count=len(objects),
        )

        return objects

    async def update(self, obj: T) -> T:
        """
        Update an existing record.

        Args:
            obj: Model instance with updated fields

        Returns:
            Updated model instance
        """
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)

        logger.debug("Updated record", model=self.model_class.__name__, id=obj.id)

        return obj

    async def bulk_update(self, filter_criteria: dict[str, Any], values: dict[str, Any]) -> int:
        """
        Update multiple records matching criteria.

        Args:
            filter_criteria: Dictionary of field names and values to filter by
            values: Dictionary of field names and values to update

        Returns:
            Number of updated records
        """
        conditions = [getattr(self.model_class, k) == v for k, v in filter_criteria.items()]
        stmt = update(self.model_class).where(and_(*conditions)).values(**values)

        result = await self.session.execute(stmt)

        logger.debug(
            "Bulk updated records",
            model=self.model_class.__name__,
            count=result.rowcount,
        )

        return result.rowcount or 0

    async def delete(self, obj: T) -> None:
        """
        Hard delete a record.

        Args:
            obj: Model instance to delete
        """
        await self.session.delete(obj)
        await self.session.flush()

        logger.debug("Deleted record", model=self.model_class.__name__, id=obj.id)

    async def soft_delete(self, obj: T, deleted_by_id: UUID | None = None) -> T:
        """
        Soft delete a record.

        Args:
            obj: Model instance to soft delete
            deleted_by_id: ID of user performing deletion

        Returns:
            Soft-deleted model instance
        """
        if not isinstance(obj, SoftDeleteModel):
            raise TypeError(f"{self.model_class.__name__} does not support soft delete")

        from datetime import datetime

        obj.deleted_at = datetime.now()
        if deleted_by_id:
            obj.deleted_by_id = deleted_by_id

        return await self.update(obj)

    async def find_by_attributes(self, **kwargs: Any) -> Sequence[T]:
        """
        Find all records matching attribute values.

        Args:
            **kwargs: Field names and values to filter by

        Returns:
            List of matching model instances
        """
        conditions = [getattr(self.model_class, k) == v for k, v in kwargs.items()]
        stmt = select(self.model_class).where(and_(*conditions))

        # Exclude soft-deleted records
        if issubclass(self.model_class, SoftDeleteModel):
            stmt = stmt.where(self.model_class.deleted_at.is_(None))

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_one_by_attributes(self, **kwargs: Any) -> T | None:
        """
        Find a single record matching attribute values.

        Args:
            **kwargs: Field names and values to filter by

        Returns:
            Model instance or None if not found
        """
        conditions = [getattr(self.model_class, k) == v for k, v in kwargs.items()]
        stmt = select(self.model_class).where(and_(*conditions))

        # Exclude soft-deleted records
        if issubclass(self.model_class, SoftDeleteModel):
            stmt = stmt.where(self.model_class.deleted_at.is_(None))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists(self, id: UUID | int) -> bool:
        """
        Check if a record exists.

        Args:
            id: Record ID

        Returns:
            True if record exists, False otherwise
        """
        stmt = select(func.count()).select_from(self.model_class).where(self.model_class.id == id)

        # Exclude soft-deleted records
        if issubclass(self.model_class, SoftDeleteModel):
            stmt = stmt.where(self.model_class.deleted_at.is_(None))

        result = await self.session.execute(stmt)
        count = result.scalar_one()

        return count > 0

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """
        Count records matching filters.

        Args:
            filters: Optional dictionary of field names and values to filter by

        Returns:
            Number of matching records
        """
        stmt = select(func.count()).select_from(self.model_class)

        if filters:
            conditions = [getattr(self.model_class, k) == v for k, v in filters.items()]
            stmt = stmt.where(and_(*conditions))

        # Exclude soft-deleted records
        if issubclass(self.model_class, SoftDeleteModel):
            stmt = stmt.where(self.model_class.deleted_at.is_(None))

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def paginate(
        self,
        page: int = 1,
        page_size: int = 50,
        filters: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_desc: bool = False,
    ) -> tuple[Sequence[T], PaginationInfo]:
        """
        Paginate records with optional filtering and ordering.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            filters: Optional dictionary of field names and values to filter by
            order_by: Optional field name to order by
            order_desc: Order descending if True

        Returns:
            Tuple of (records, pagination_info)
        """
        # Build base query
        stmt = select(self.model_class)

        # Apply filters
        if filters:
            conditions = [getattr(self.model_class, k) == v for k, v in filters.items()]
            stmt = stmt.where(and_(*conditions))

        # Exclude soft-deleted records
        if issubclass(self.model_class, SoftDeleteModel):
            stmt = stmt.where(self.model_class.deleted_at.is_(None))

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.session.execute(count_stmt)
        total_count = result.scalar_one()

        # Apply ordering
        if order_by:
            order_column = getattr(self.model_class, order_by)
            stmt = stmt.order_by(order_column.desc() if order_desc else order_column)

        # Apply pagination
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        # Execute query
        result = await self.session.execute(stmt)
        records = result.scalars().all()

        # Build pagination info
        total_pages = (total_count + page_size - 1) // page_size
        pagination_info = PaginationInfo(
            page=page,
            page_size=page_size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

        return records, pagination_info

    async def search(
        self,
        search_term: str,
        search_fields: list[str],
        page: int = 1,
        page_size: int = 50,
        filters: dict[str, Any] | None = None,
    ) -> tuple[Sequence[T], PaginationInfo]:
        """
        Full-text search across multiple fields.

        Args:
            search_term: Search term
            search_fields: List of field names to search in
            page: Page number (1-indexed)
            page_size: Number of items per page
            filters: Optional additional filters

        Returns:
            Tuple of (records, pagination_info)
        """
        # Build base query
        stmt = select(self.model_class)

        # Apply search across multiple fields
        search_conditions = [getattr(self.model_class, field).ilike(f"%{search_term}%") for field in search_fields]
        stmt = stmt.where(or_(*search_conditions))

        # Apply additional filters
        if filters:
            conditions = [getattr(self.model_class, k) == v for k, v in filters.items()]
            stmt = stmt.where(and_(*conditions))

        # Exclude soft-deleted records
        if issubclass(self.model_class, SoftDeleteModel):
            stmt = stmt.where(self.model_class.deleted_at.is_(None))

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.session.execute(count_stmt)
        total_count = result.scalar_one()

        # Apply pagination
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        # Execute query
        result = await self.session.execute(stmt)
        records = result.scalars().all()

        # Build pagination info
        total_pages = (total_count + page_size - 1) // page_size
        pagination_info = PaginationInfo(
            page=page,
            page_size=page_size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

        return records, pagination_info

    async def execute_query(self, stmt: Select[tuple[T]]) -> Sequence[T]:
        """
        Execute a custom query statement.

        Args:
            stmt: SQLAlchemy select statement

        Returns:
            List of model instances
        """
        result = await self.session.execute(stmt)
        return result.scalars().all()
