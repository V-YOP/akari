from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator
from enum import IntEnum


class LogLevel(IntEnum):
    INFO = 1
    WARNING = 2
    ERROR = 3
    DEBUG = 4


class ExecutionStatus(IntEnum):
    PENDING = 1
    RUNNING = 2
    COMPLETED = 3
    FAILED = 4
    TIMEOUT = 5
    CANCELLED = 6


class TaskLog(models.Model):
    """
    Task execution log
    """
    id = fields.IntField(pk=True)

    # Foreign key to task
    task = fields.ForeignKeyField("models.Task", related_name="logs", on_delete=fields.CASCADE)

    # Execution info
    status = fields.IntEnumField(ExecutionStatus, description="Execution status")
    started_at = fields.DatetimeField(null=True, description="Start time")
    finished_at = fields.DatetimeField(null=True, description="Finish time")
    duration = fields.FloatField(null=True, description="Duration in seconds")

    # Command executed
    command_executed = fields.CharField(max_length=2000, description="Full command executed")

    # Output
    stdout = fields.TextField(null=True, description="Standard output")
    stderr = fields.TextField(null=True, description="Standard error")
    exit_code = fields.IntField(null=True, description="Exit code")

    # Error info
    error_message = fields.TextField(null=True, description="Error message if failed")

    # Metadata
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "task_logs"

    def __str__(self):
        return f"TaskLog(id={self.id}, task={self.task_id}, status={self.status})"


# Pydantic schemas for API
TaskLog_Pydantic = pydantic_model_creator(TaskLog, name="TaskLog")
TaskLogIn_Pydantic = pydantic_model_creator(TaskLog, name="TaskLogIn", exclude_readonly=True)