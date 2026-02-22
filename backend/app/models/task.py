from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator
from enum import IntEnum
from typing import Optional, List
import json


class ScheduleType(IntEnum):
    CRON = 1
    INTERVAL = 2


class Task(models.Model):
    """
    Task model representing a scheduled job
    """
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, description="Task name")
    description = fields.TextField(null=True, description="Task description")

    # Command to execute
    command = fields.CharField(max_length=1000, description="Command to execute")
    args = fields.JSONField(default=list, description="Command arguments as list")

    # Scheduling
    schedule_type = fields.IntEnumField(ScheduleType, description="Schedule type: 1=cron, 2=interval")
    cron_expression = fields.CharField(max_length=100, null=True, description="Cron expression")
    interval_seconds = fields.IntField(null=True, description="Interval in seconds")

    # Execution settings
    enabled = fields.BooleanField(default=True, description="Whether task is enabled")
    timeout = fields.IntField(default=300, description="Timeout in seconds")
    max_concurrent = fields.IntField(default=1, description="Maximum concurrent executions")

    # Metadata
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "tasks"

    def __str__(self):
        return f"Task(id={self.id}, name={self.name})"

    @property
    def schedule_info(self) -> str:
        if self.schedule_type == ScheduleType.CRON:
            return f"Cron: {self.cron_expression}"
        else:
            return f"Interval: {self.interval_seconds}s"


# Pydantic schemas for API
Task_Pydantic = pydantic_model_creator(Task, name="Task")
TaskIn_Pydantic = pydantic_model_creator(Task, name="TaskIn", exclude_readonly=True)
TaskUpdate_Pydantic = pydantic_model_creator(Task, name="TaskUpdate", exclude_readonly=True, optional=["name", "description", "command", "args", "schedule_type", "cron_expression", "interval_seconds", "enabled", "timeout", "max_concurrent"])

from app.models.log import ExecutionStatus
from pydantic import BaseModel
from typing import Optional

class TaskWithStats(Task_Pydantic):
    """Task model with execution statistics"""
    log_count: int = 0
    last_execution_success: Optional[bool] = None