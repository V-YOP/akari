from shutil import which

from fastapi import APIRouter, HTTPException, status, Query, BackgroundTasks
from typing import List, Optional

from pydantic import BaseModel
from app.models.task import Task, Task_Pydantic, TaskIn_Pydantic, TaskUpdate_Pydantic, ScheduleType, TaskWithStats
from app.models.log import TaskLog, TaskLog_Pydantic, ExecutionStatus
from app.core.schemas import PaginatedResponse
from app.scheduler.scheduler import scheduler
from tortoise.transactions import atomic
from tortoise.expressions import Q
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=PaginatedResponse[TaskWithStats])
async def get_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    enabled: Optional[bool] = None,
    search: Optional[str] = None
):
    """
    Get list of tasks with pagination and filtering
    """
    query = Task.all()
    if enabled is not None:
        query = query.filter(enabled=enabled)
    if search:
        query = query.filter(Q(name__icontains=search) | Q(description__icontains=search))

    total = await query.count()
    tasks = await query.offset(skip).limit(limit).order_by("-created_at")

    # Build response with statistics
    tasks_with_stats = []
    for task in tasks:
        # Get log count for this task
        log_count = await task.logs.all().count()

        # Get latest execution status
        last_execution_success = None
        latest_log = await task.logs.all().order_by("-started_at").first()
        if latest_log:
            last_execution_success = latest_log.status == ExecutionStatus.COMPLETED

        # Create TaskWithStats instance
        task_data = await Task_Pydantic.from_tortoise_orm(task)
        task_dict = task_data.model_dump()
        task_with_stats = TaskWithStats(
            **task_dict,
            log_count=log_count,
            last_execution_success=last_execution_success
        )
        tasks_with_stats.append(task_with_stats)

    return PaginatedResponse(
        total=total,
        skip=skip,
        limit=limit,
        data=tasks_with_stats
    )


@router.get("/{task_id}", response_model=Task_Pydantic)
async def get_task(task_id: int):
    """
    Get a specific task by ID
    """
    task = await Task.get_or_none(id=task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return await Task_Pydantic.from_tortoise_orm(task)


@router.post("/", response_model=Task_Pydantic, status_code=status.HTTP_201_CREATED)
@atomic()
async def create_task(task_in: TaskIn_Pydantic):
    """
    Create a new task
    """
    # Validate schedule type
    if task_in.schedule_type == ScheduleType.CRON and not task_in.cron_expression:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="cron_expression is required for cron schedule type"
        )
    if task_in.schedule_type == ScheduleType.INTERVAL and not task_in.interval_seconds:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="interval_seconds is required for interval schedule type"
        )

    task = await Task.create(**task_in.model_dump(exclude_unset=True))
    # Add to scheduler if enabled
    if task.enabled:
        await scheduler.add_task(task)
    return await Task_Pydantic.from_tortoise_orm(task)


@router.put("/{task_id}", response_model=Task_Pydantic)
@atomic()
async def update_task(task_id: int, task_update: TaskUpdate_Pydantic):
    """
    Update an existing task
    """
    task = await Task.get_or_none(id=task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    update_data = task_update.model_dump(exclude_unset=True)

    # Validate schedule type consistency
    if "schedule_type" in update_data or "cron_expression" in update_data or "interval_seconds" in update_data:
        schedule_type = update_data.get("schedule_type", task.schedule_type)
        cron_expression = update_data.get("cron_expression", task.cron_expression)
        interval_seconds = update_data.get("interval_seconds", task.interval_seconds)

        if schedule_type == ScheduleType.CRON and not cron_expression:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="cron_expression is required for cron schedule type"
            )
        if schedule_type == ScheduleType.INTERVAL and not interval_seconds:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="interval_seconds is required for interval schedule type"
            )

    # Store old enabled state for scheduler update
    old_enabled = task.enabled

    await task.update_from_dict(update_data)
    await task.save()

    # Update scheduler
    if not old_enabled and task.enabled:
        # Task was enabled
        await scheduler.add_task(task)
    elif old_enabled and not task.enabled:
        # Task was disabled
        await scheduler.remove_task(task.id)
    elif task.enabled:
        # Task remains enabled, update scheduler
        await scheduler.remove_task(task.id)
        await scheduler.add_task(task)

    return await Task_Pydantic.from_tortoise_orm(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
@atomic()
async def delete_task(task_id: int):
    """
    Delete a task
    """
    task = await Task.get_or_none(id=task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Remove from scheduler
    await scheduler.remove_task(task_id)

    await task.delete()
    return None


@router.get("/{task_id}/logs", response_model=PaginatedResponse[TaskLog_Pydantic])
async def get_task_logs(
    task_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[int] = None
):
    """
    Get execution logs for a specific task
    """
    task = await Task.get_or_none(id=task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    query = task.logs.all()
    if status is not None:
        query = query.filter(status=status)

    total = await query.count()
    logs_query = query.offset(skip).limit(limit).order_by("-started_at")
    return PaginatedResponse(
        total=total,
        skip=skip,
        limit=limit,
        data=await TaskLog_Pydantic.from_queryset(logs_query)
    )


@router.post("/{task_id}/execute", status_code=status.HTTP_202_ACCEPTED)
async def execute_task(task_id: int, background_tasks: BackgroundTasks):
    """
    Manually trigger task execution
    """
    task = await Task.get_or_none(id=task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Trigger execution in background
    background_tasks.add_task(scheduler.execute_now, task_id)
    return {"message": "Task execution started in background", "task_id": task_id}

class ExecuteTaskModel(BaseModel):
    command: str
    args: list[str] = []
    timeout: int = 5

@router.post("/test_execute", status_code=status.HTTP_200_OK)
async def test_execute_task(task_in: ExecuteTaskModel):
    """
    根据相关信息测试执行task（取其中的命令、参数、超时时间字段），不操作数据库，返回返回码，标准输入流，标准输出流
    """
    command = task_in.command
    if not which(command):
        return {'exit_code': 1, 'stdout': '', 'stderr': f'No such command "{command}" found'}
    args = task_in.args
    timeout = task_in.timeout
    exit_code, stdout, stderr = await scheduler.do_execute_task(command, args, timeout)
    return {
        'exit_code': exit_code,
        'stdout': stdout,
        'stderr': stderr,
    }

