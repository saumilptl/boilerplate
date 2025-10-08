"""Unit of Work pattern for managing database transactions."""

from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database.db import get_database
from app.infra.database.repository import Repository
from app.infra.monitoring.logging.logger import logger

R = TypeVar("R", bound=Repository[Any])


class UnitOfWork:
    """
    Unit of Work pattern for managing database transactions.

    Provides:
    - Automatic transaction management
    - Repository registry
    - Commit/rollback handling
    - Decorator for service methods
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize Unit of Work with database session.

        Args:
            session: Async database session
        """
        self._session = session
        self._repositories: dict[type[Repository[Any]], Repository[Any]] = {}

    @property
    def session(self) -> AsyncSession:
        """Get the underlying database session."""
        return self._session

    def get_repository(self, repository_class: type[R]) -> R:
        """
        Get or create a repository instance.

        Args:
            repository_class: Repository class to instantiate

        Returns:
            Repository instance
        """
        if repository_class not in self._repositories:
            repository = repository_class(session=self._session)
            self._repositories[repository_class] = repository

        return self._repositories[repository_class]  # type: ignore[return-value]

    def register_repositories(self, *repository_classes: type[Repository[Any]]) -> None:
        """
        Pre-register repository classes.

        Args:
            *repository_classes: Repository classes to register
        """
        for repository_class in repository_classes:
            self.get_repository(repository_class)

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._session.commit()
        logger.debug("Transaction committed")

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        await self._session.rollback()
        logger.debug("Transaction rolled back")

    async def flush(self) -> None:
        """Flush pending changes without committing."""
        await self._session.flush()

    async def refresh(self, obj: Any) -> None:
        """Refresh an object from the database."""
        await self._session.refresh(obj)

    @classmethod
    @asynccontextmanager
    async def begin(cls) -> AsyncGenerator["UnitOfWork", None]:
        """
        Create a new Unit of Work context.

        Usage:
            async with UnitOfWork.begin() as uow:
                user_repo = uow.get_repository(UserRepository)
                user = await user_repo.create(user)
                # Automatically commits on success, rolls back on error

        Yields:
            UnitOfWork instance
        """
        db = get_database()

        async with db.session() as session:
            uow = cls(session=session)

            try:
                logger.debug("Starting unit of work")
                yield uow
                await uow.commit()
                logger.debug("Unit of work completed successfully")

            except Exception as e:
                logger.exception("Unit of work failed, rolling back", error=str(e))
                await uow.rollback()
                raise

    @classmethod
    def with_repositories(cls, *repository_classes: type[Repository[Any]]) -> Callable[..., Any]:
        """
        Decorator for service methods that require repositories.

        Automatically provides a Unit of Work with registered repositories.
        If a 'uow' parameter is already provided, reuses it (for nested calls).

        Usage:
            @UnitOfWork.with_repositories(UserRepository, OrganizationRepository)
            async def create_user_with_org(user_data, org_data, uow=None):
                user_repo = uow.get_repository(UserRepository)
                org_repo = uow.get_repository(OrganizationRepository)
                # ... business logic

        Args:
            *repository_classes: Repository classes to register

        Returns:
            Decorated function
        """

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Check if UoW already provided (nested call)
                if "uow" in kwargs and kwargs["uow"] is not None:
                    return await func(*args, **kwargs)

                # Create new UoW
                async with cls.begin() as uow:
                    # Register repositories
                    uow.register_repositories(*repository_classes)

                    # Call function with UoW
                    return await func(*args, **kwargs, uow=uow)

            return wrapper

        return decorator
