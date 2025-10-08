"""Dependency injection container configuration."""

from functools import lru_cache

from dependency_injector import containers, providers

from app.config import get_config
from app.infra.database.db import Database
from app.infra.monitoring.logging.logger import initialize_logging
from app.infra.monitoring.tracer import Tracer


class MonitoringContainer(containers.DeclarativeContainer):
    """Container for monitoring services."""

    config = providers.Configuration()

    # Logging
    logging_config = providers.Resource(
        initialize_logging,
        service_name=config.SERVICE_NAME,
        config=config.MONITORING,
        environment=config.ENVIRONMENT,
    )

    # Tracing
    tracer = providers.Singleton(
        Tracer,
    )

    tracer_init = providers.Resource(
        lambda tracer, service_name, config: (
            tracer.initialize(service_name, config),
            tracer.initialize_datadog(service_name, config),
            tracer,
        )[-1],
        tracer=tracer,
        service_name=config.SERVICE_NAME,
        config=config.MONITORING,
    )


class DatabaseContainer(containers.DeclarativeContainer):
    """Container for database services."""

    config = providers.Configuration()

    # Database
    database = providers.Singleton(
        Database,
        config=config.DATABASE,
    )

    # Initialize database
    database_init = providers.Resource(
        lambda db: (db.init(), db)[-1],
        db=database,
    )


class ApplicationContainer(containers.DeclarativeContainer):
    """Main application container."""

    # Configuration
    config = providers.Configuration()

    # Sub-containers
    monitoring = providers.Container(
        MonitoringContainer,
        config=config,
    )

    database = providers.Container(
        DatabaseContainer,
        config=config,
    )


def init_container() -> ApplicationContainer:
    """
    Initialize and configure the application container.

    Returns:
        Configured application container
    """
    container = ApplicationContainer()

    # Load configuration - pass the actual config objects, not dumped dicts
    app_config = get_config()
    container.config.from_dict(
        {
            "DATABASE": app_config.DATABASE,
            "REDIS": app_config.REDIS,
            "MONITORING": app_config.MONITORING,
            "SECURITY": app_config.SECURITY,
            "WORKER": app_config.WORKER,
            "ENVIRONMENT": app_config.ENVIRONMENT,
            "SERVICE_NAME": app_config.SERVICE_NAME,
            "DEBUG": app_config.DEBUG,
            "HOST": app_config.HOST,
            "PORT": app_config.PORT,
            "WORKERS": app_config.WORKERS,
            "RELOAD": app_config.RELOAD,
        }
    )

    return container


@lru_cache(maxsize=1)
def get_container() -> ApplicationContainer:
    """
    Get cached application container.

    Returns:
        Application container instance
    """
    return init_container()
