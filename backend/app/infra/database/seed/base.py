"""Base seeder class and registry for database seeding."""

import contextlib
from abc import ABC, abstractmethod
from typing import ClassVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.monitoring.logging.logger import logger


class Seeder(ABC):
    """
    Base class for database seeders.

    Seeders are used to initialize data in the database.
    Each seeder should implement the `run` method which contains
    the logic for inserting data.

    Seeders are automatically registered when they are defined.
    """

    # Required class attributes
    name: ClassVar[str]
    description: ClassVar[str] = ""
    dependencies: ClassVar[list[str]] = []

    def __init_subclass__(cls, **kwargs: dict) -> None:
        """Register all subclasses with the registry."""
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "name") and cls.name:
            SeedRegistry.register(cls)

    @abstractmethod
    async def run(self, session: AsyncSession) -> bool:
        """
        Run the seeder logic.

        Should be idempotent - if the data already exists, it should not be duplicated.

        Args:
            session: Async database session

        Returns:
            True if data was inserted, False if it already existed
        """


class SeedRegistry:
    """Registry of all available seeders."""

    _registry: ClassVar[dict[str, type[Seeder]]] = {}

    @classmethod
    def register(cls, seeder_class: type[Seeder]) -> None:
        """
        Register a seeder class.

        Args:
            seeder_class: Seeder class to register
        """
        cls._registry[seeder_class.name] = seeder_class
        logger.debug("Registered seeder", seeder_name=seeder_class.name)

    @classmethod
    def get_all_seeders(cls) -> dict[str, type[Seeder]]:
        """
        Get all registered seeders.

        Returns:
            Dictionary mapping seeder name to seeder class
        """
        return cls._registry.copy()

    @classmethod
    def get_seeder(cls, name: str) -> type[Seeder] | None:
        """
        Get a specific seeder by name.

        Args:
            name: Seeder name

        Returns:
            Seeder class or None if not found
        """
        return cls._registry.get(name)

    @classmethod
    def discover_seeders(cls) -> None:
        """
        Discover all seeders in the codebase.

        This method walks through all modules in the app package
        to ensure all seeders are registered.
        """
        import importlib
        import pkgutil

        import app

        # Walk through all modules in the app package
        for _, module_name, _ in pkgutil.walk_packages(app.__path__, prefix="app."):
            with contextlib.suppress(ImportError):
                importlib.import_module(module_name)
