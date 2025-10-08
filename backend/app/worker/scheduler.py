"""Celery Beat scheduler for periodic tasks."""

from celery import Celery

from app.infra.monitoring.logging.logger import logger


def setup_periodic_tasks(_app: Celery) -> None:
    """
    Configure periodic tasks for Celery Beat.

    Args:
        _app: Celery application instance (unused - reserved for future use)

    Example configurations:
        Run every 5 minutes:
            app.add_periodic_task(
                300.0,  # 5 minutes in seconds
                example_task.s(),
                name="example-task-every-5-min",
            )

        Run daily at midnight:
            app.add_periodic_task(
                crontab(hour=0, minute=0),
                daily_cleanup_task.s(),
                name="daily-cleanup",
            )
    """
    logger.info("Periodic tasks configured")
