"""Celery application configuration."""

from celery import Celery, signals

from app.config import config as get_app_config
from app.infra.monitoring.logging.logger import logger


def create_celery_app() -> Celery:
    """
    Create and configure Celery application.

    Returns:
        Configured Celery application
    """
    # Get configuration
    config = get_app_config()

    # Build Redis URL for broker and backend
    redis_url = config.REDIS.url

    # Create Celery app
    app = Celery(
        "backend-worker",
        broker=redis_url,
        backend=redis_url,
    )

    # Configure Celery
    app.conf.update(
        # Worker settings
        worker_prefetch_multiplier=config.WORKER.WORKER_PREFETCH_MULTIPLIER,
        worker_max_tasks_per_child=config.WORKER.WORKER_MAX_TASKS_PER_CHILD,
        worker_hijack_root_logger=False,
        # Task settings
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        # Task time limits
        task_soft_time_limit=config.WORKER.TASK_SOFT_TIME_LIMIT,
        task_time_limit=config.WORKER.TASK_TIME_LIMIT,
        # Result backend settings
        result_expires=3600,
        result_persistent=True,
    )

    # Auto-discover tasks
    app.autodiscover_tasks(["app.worker.tasks"])

    logger.info(
        "Celery application created",
        broker=redis_url,
        backend=redis_url,
    )

    return app


# Create Celery app instance
celery_app = create_celery_app()


# Worker lifecycle hooks
@signals.worker_process_init.connect
def init_worker_process(**_kwargs: any) -> None:
    """Initialize worker process resources."""
    logger.info("Worker process initializing")

    # Initialize database connection pool
    from app.infra.database.db import get_database

    db = get_database()
    db.init()

    logger.info("Worker process initialized")


@signals.worker_process_shutdown.connect
def shutdown_worker_process(**_kwargs: any) -> None:
    """Cleanup worker process resources."""
    logger.info("Worker process shutting down")


@signals.task_failure.connect
def task_failure_handler(task_id: str, exception: Exception, **_kwargs: any) -> None:
    """Handle task failures."""
    logger.error(
        "Task failed",
        task_id=task_id,
        error=str(exception),
        exc_info=True,
    )


@signals.task_success.connect
def task_success_handler(sender: any, **_kwargs: any) -> None:
    """Handle task success."""
    logger.debug("Task succeeded", task_name=sender.name if sender else "unknown")
