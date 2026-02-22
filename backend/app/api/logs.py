from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, timezone
from app.models.log import TaskLog, TaskLog_Pydantic
from app.core.schemas import PaginatedResponse
from tortoise.expressions import Q
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("", response_model=PaginatedResponse[TaskLog_Pydantic])
async def get_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    task_id: Optional[int] = None,
    status: Optional[int] = None,
    search: Optional[str] = None
):
    """
    Get execution logs with filtering
    """
    query = TaskLog.all().prefetch_related("task")

    if task_id is not None:
        query = query.filter(task_id=task_id)
    if status is not None:
        query = query.filter(status=status)
    if search:
        query = query.filter(
            Q(stdout__icontains=search) |
            Q(stderr__icontains=search) |
            Q(error_message__icontains=search) |
            Q(command_executed__icontains=search)
        )

    total = await query.count()
    logs_query = query.offset(skip).limit(limit).order_by("-started_at")
    return PaginatedResponse(
        total=total,
        skip=skip,
        limit=limit,
        data=await TaskLog_Pydantic.from_queryset(logs_query)
    )


@router.get("/{log_id}", response_model=TaskLog_Pydantic)
async def get_log(log_id: int):
    """
    Get a specific log by ID
    """
    log = await TaskLog.get_or_none(id=log_id).prefetch_related("task")
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")
    return await TaskLog_Pydantic.from_tortoise_orm(log)


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_log(log_id: int):
    """
    Delete a log entry
    """
    log = await TaskLog.get_or_none(id=log_id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")

    await log.delete()
    return None


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_logs(
    older_than_days: Optional[int] = Query(None, ge=1, description="Delete logs older than N days"),
    task_id: Optional[int] = None
):
    """
    Clear logs with optional filters
    """
    query = TaskLog.all()

    if task_id is not None:
        query = query.filter(task_id=task_id)

    if older_than_days:
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        query = query.filter(started_at__lt=cutoff_date)

    await query.delete()
    return None


@router.delete("/cleanup/before")
async def clear_logs_before(
    before: str = Query(..., description="ISO format datetime, delete logs with started_at before this time")
):
    """
    Delete logs older than a specific timestamp
    """
    try:
        before_time = datetime.fromisoformat(before)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid datetime format, use ISO format (e.g., 2024-01-01T00:00:00)"
        )

    # If datetime is timezone-aware, convert to UTC and make it naive
    if before_time.tzinfo is not None:
        before_time = before_time.astimezone(timezone.utc)
        before_time = before_time.replace(tzinfo=None)

    query = TaskLog.all()
    query = query.filter(started_at__lt=before_time)

    deleted_count = await query.count()
    await query.delete()

    return {"deleted": deleted_count}