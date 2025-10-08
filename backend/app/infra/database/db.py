"""Database connection management with async SQLAlchemy."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from app.config import DatabaseConfig
from app.infra.monitoring.logging.logger import logger


class Database:
    """Async database connection manager."""

    def __init__(self, config: DatabaseConfig) -> None:
        """
        Initialize database with configuration.

        Args:
            config: Database configuration
        """
        self.config = config
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    def init(self) -> None:
        """Initialize database engine and session factory."""
        if self._engine is not None:
            logger.warning("Database already initialized")
            return

        engine_kwargs: dict[str, Any] = {
            "echo": self.config.ECHO,
            "pool_pre_ping": self.config.POOL_PRE_PING,
            "pool_recycle": self.config.POOL_RECYCLE,
        }

        # Configure connection pool
        if self.config.POOL_SIZE > 0:
            engine_kwargs.update(
                {
                    "pool_size": self.config.POOL_SIZE,
                    "max_overflow": self.config.MAX_OVERFLOW,
                }
            )
        else:
            # Use NullPool for serverless environments
            engine_kwargs["poolclass"] = NullPool

        # Configure SSL
        if self.config.SSL_MODE and self.config.SSL_MODE != "disable":
            connect_args = {"ssl": self.config.SSL_MODE}
            engine_kwargs["connect_args"] = connect_args

        self._engine = create_async_engine(self.config.url, **engine_kwargs)

        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        logger.info(
            "Database initialized",
            host=self.config.HOST,
            port=self.config.PORT,
            database=self.config.NAME,
            pool_size=self.config.POOL_SIZE,
        )

    async def close(self) -> None:
        """Close database connections."""
        if self._engine is None:
            return

        await self._engine.dispose()
        self._engine = None
        self._session_factory = None

        logger.info("Database connections closed")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session context manager.

        Yields:
            Async database session

        Example:
            async with database.session() as session:
                result = await session.execute(select(User))
                users = result.scalars().all()
        """
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call init() first.")

        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    @property
    def engine(self) -> AsyncEngine:
        """Get database engine."""
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call init() first.")
        return self._engine

    async def create_all_tables(self) -> None:
        """Create all tables defined in SQLModel metadata."""
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call init() first.")

        async with self._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        logger.info("All tables created")

    async def drop_all_tables(self) -> None:
        """Drop all tables defined in SQLModel metadata."""
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call init() first.")

        async with self._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)

        logger.warning("All tables dropped")


# Global database instance
_database: Database | None = None


def get_database() -> Database:
    """Get global database instance."""
    global _database
    if _database is None:
        from app.config import config as get_app_config

        _database = Database(config=get_app_config().DATABASE)
        _database.init()
    return _database


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database session.

    Example:
        @app.get("/users")
        async def get_users(session: AsyncSession = Depends(get_session)):
            result = await session.execute(select(User))
            return result.scalars().all()
    """
    db = get_database()
    async with db.session() as session:
        yield session
