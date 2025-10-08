"""Example background task demonstrating worker patterns."""

from typing import Any

from app.infra.monitoring.logging.logger import logger
from app.worker.app import celery_app


@celery_app.task(bind=True, max_retries=3)
def example_task(
    self: Any,
    message: str,
) -> dict[str, str]:
    """
    Example background task with retry logic.

    Args:
        self: Task instance (bound automatically)
        message: Message to process

    Returns:
        Task result dictionary
    """
    try:
        logger.info("Processing example task", message=message, task_id=self.request.id)

        # Your actual work here
        result = f"Processed: {message}"

        logger.info("Task completed successfully", task_id=self.request.id)

        return {"status": "success", "result": result}

    except Exception as e:
        logger.exception("Task failed", task_id=self.request.id)
        # Retry with exponential backoff: 1s, 2s, 4s
        raise self.retry(exc=e, countdown=2**self.request.retries) from e
