"""Task management endpoints for triggering background jobs."""

from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.dependencies import current_active_user
from app.auth.models import User
from app.infra.monitoring.logging.logger import logger
from app.worker.app import celery_app
from app.worker.tasks.example import example_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskRequest(BaseModel):
    """Task request."""

    message: str


class TaskResponse(BaseModel):
    """Task submission response."""

    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    """Task status response."""

    task_id: str
    status: str
    result: Any = None
    error: str | None = None


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_task(
    request: TaskRequest,
    user: User = Depends(current_active_user),
) -> TaskResponse:
    """
    Trigger an async background task.

    Args:
        request: Task parameters
        user: Authenticated user

    Returns:
        Task ID and status
    """
    logger.info("Triggering background task", message=request.message, user_id=user.id)

    task = example_task.delay(message=request.message)

    return TaskResponse(task_id=task.id, status="pending")


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    user: User = Depends(current_active_user),  # noqa: ARG001
) -> TaskStatusResponse:
    """
    Get the status of a background task.

    Args:
        task_id: Task ID to check
        user: Authenticated user

    Returns:
        Task status and result if available
    """
    task_result = AsyncResult(task_id, app=celery_app)

    if task_result.state == "PENDING":
        return TaskStatusResponse(
            task_id=task_id,
            status="pending",
        )
    if task_result.state == "SUCCESS":
        return TaskStatusResponse(
            task_id=task_id,
            status="success",
            result=task_result.result,
        )
    if task_result.state == "FAILURE":
        return TaskStatusResponse(
            task_id=task_id,
            status="failed",
            error=str(task_result.info),
        )
    if task_result.state == "RETRY":
        return TaskStatusResponse(
            task_id=task_id,
            status="retrying",
            error=str(task_result.info) if task_result.info else None,
        )
    return TaskStatusResponse(
        task_id=task_id,
        status=task_result.state.lower(),
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_task(
    task_id: str,
    user: User = Depends(current_active_user),  # noqa: ARG001
) -> None:
    """
    Revoke a pending or running task.

    Args:
        task_id: Task ID to revoke
        user: Authenticated user
    """
    logger.info("Revoking task", task_id=task_id)

    task_result = AsyncResult(task_id, app=celery_app)

    if task_result.state in ("PENDING", "STARTED"):
        task_result.revoke(terminate=True)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot revoke task in state: {task_result.state}",
        )
