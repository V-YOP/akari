"""
Unit tests for tasks API endpoints.
"""
import pytest
from httpx import AsyncClient
from app.models.task import ScheduleType


@pytest.mark.asyncio
class TestTasksAPI:
    """Test cases for tasks API."""

    async def test_get_tasks_empty(self, async_client: AsyncClient):
        """Test getting tasks when empty."""
        response = await async_client.get("/tasks/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["skip"] == 0
        assert data["limit"] == 100
        assert len(data["data"]) == 0

    async def test_create_task_cron(self, async_client: AsyncClient):
        """Test creating a task with cron schedule."""
        task_data = {
            "name": "Test Cron Task",
            "description": "A test task with cron schedule",
            "command": "python",
            "args": ["-c", "print('Hello')"],
            "schedule_type": ScheduleType.CRON.value,
            "cron_expression": "*/5 * * * *",
            "enabled": True,
            "timeout": 300,
            "max_concurrent": 1
        }

        response = await async_client.post("/tasks/", json=task_data)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["name"] == task_data["name"]
        assert data["schedule_type"] == ScheduleType.CRON.value
        assert data["cron_expression"] == task_data["cron_expression"]
        assert data["enabled"] is True

    async def test_create_task_interval(self, async_client: AsyncClient):
        """Test creating a task with interval schedule."""
        task_data = {
            "name": "Test Interval Task",
            "command": "echo",
            "args": ["Hello"],
            "schedule_type": ScheduleType.INTERVAL.value,
            "interval_seconds": 60,
            "enabled": False,
            "timeout": 60,
            "max_concurrent": 2
        }

        response = await async_client.post("/tasks/", json=task_data)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["schedule_type"] == ScheduleType.INTERVAL.value
        assert data["interval_seconds"] == 60
        assert data["enabled"] is False

    async def test_create_task_validation_error(self, async_client: AsyncClient):
        """Test task creation with invalid data."""
        # Missing required field: command
        task_data = {
            "name": "Invalid Task",
            "schedule_type": ScheduleType.CRON.value,
            "cron_expression": "* * * * *"
        }

        response = await async_client.post("/tasks/", json=task_data)
        assert response.status_code == 422  # Validation error

    async def test_create_task_cron_missing_expression(self, async_client: AsyncClient):
        """Test cron task creation without expression."""
        task_data = {
            "name": "Invalid Cron Task",
            "command": "python",
            "args": [],
            "schedule_type": ScheduleType.CRON.value,
            # Missing cron_expression
        }

        response = await async_client.post("/tasks/", json=task_data)
        assert response.status_code == 422
        assert "cron_expression" in response.text.lower()

    async def test_create_task_interval_missing_seconds(self, async_client: AsyncClient):
        """Test interval task creation without interval."""
        task_data = {
            "name": "Invalid Interval Task",
            "command": "python",
            "args": [],
            "schedule_type": ScheduleType.INTERVAL.value,
            # Missing interval_seconds
        }

        response = await async_client.post("/tasks/", json=task_data)
        assert response.status_code == 422
        assert "interval_seconds" in response.text.lower()

    async def test_get_task_by_id(self, async_client: AsyncClient):
        """Test retrieving a specific task by ID."""
        # First create a task
        task_data = {
            "name": "Task to Retrieve",
            "command": "ls",
            "args": ["-la"],
            "schedule_type": ScheduleType.CRON.value,
            "cron_expression": "0 * * * *",
            "enabled": True,
            "timeout": 30,
            "max_concurrent": 1
        }

        create_response = await async_client.post("/tasks", json=task_data)
        assert create_response.status_code == 201
        created_task = create_response.json()
        task_id = created_task["id"]

        # Retrieve the task
        response = await async_client.get(f"/tasks/{task_id}")
        assert response.status_code == 200
        retrieved_task = response.json()
        assert retrieved_task["id"] == task_id
        assert retrieved_task["name"] == task_data["name"]
        assert retrieved_task["command"] == task_data["command"]

    async def test_get_nonexistent_task(self, async_client: AsyncClient):
        """Test retrieving a task that doesn't exist."""
        response = await async_client.get("/tasks/99999")
        assert response.status_code == 404

    async def test_update_task(self, async_client: AsyncClient):
        """Test updating an existing task."""
        # Create a task
        task_data = {
            "name": "Original Task",
            "command": "python",
            "args": ["script.py"],
            "schedule_type": ScheduleType.CRON.value,
            "cron_expression": "*/5 * * * *",
            "enabled": True,
            "timeout": 300,
            "max_concurrent": 1
        }

        create_response = await async_client.post("/tasks", json=task_data)
        task_id = create_response.json()["id"]

        # Update the task
        update_data = {
            "name": "Updated Task",
            "description": "Updated description",
            "enabled": False,
            "timeout": 600
        }

        response = await async_client.put(f"/tasks/{task_id}", json=update_data)
        assert response.status_code == 200
        updated_task = response.json()
        assert updated_task["id"] == task_id
        assert updated_task["name"] == update_data["name"]
        assert updated_task["description"] == update_data["description"]
        assert updated_task["enabled"] == update_data["enabled"]
        assert updated_task["timeout"] == update_data["timeout"]
        # Original fields should remain
        assert updated_task["command"] == task_data["command"]
        assert updated_task["schedule_type"] == task_data["schedule_type"]

    async def test_update_nonexistent_task(self, async_client: AsyncClient):
        """Test updating a task that doesn't exist."""
        update_data = {"name": "Updated Name"}
        response = await async_client.put("/tasks/99999", json=update_data)
        assert response.status_code == 404

    async def test_delete_task(self, async_client: AsyncClient):
        """Test deleting a task."""
        # Create a task
        task_data = {
            "name": "Task to Delete",
            "command": "rm",
            "args": ["-rf", "/tmp/test"],
            "schedule_type": ScheduleType.INTERVAL.value,
            "interval_seconds": 3600,
            "enabled": True,
            "timeout": 60,
            "max_concurrent": 1
        }

        create_response = await async_client.post("/tasks", json=task_data)
        task_id = create_response.json()["id"]

        # Delete the task
        response = await async_client.delete(f"/tasks/{task_id}")
        assert response.status_code == 204

        # Verify task is deleted
        get_response = await async_client.get(f"/tasks/{task_id}")
        assert get_response.status_code == 404

    async def test_delete_nonexistent_task(self, async_client: AsyncClient):
        """Test deleting a task that doesn't exist."""
        response = await async_client.delete("/tasks/99999")
        assert response.status_code == 404

    async def test_get_tasks_with_pagination(self, async_client: AsyncClient):
        """Test pagination for tasks list."""
        # Create multiple tasks
        for i in range(15):
            task_data = {
                "name": f"Task {i}",
                "command": "echo",
                "args": [str(i)],
                "schedule_type": ScheduleType.INTERVAL.value,
                "interval_seconds": 60,
                "enabled": True,
                "timeout": 30,
                "max_concurrent": 1
            }
            await async_client.post("/tasks", json=task_data)

        # Test pagination
        response = await async_client.get("/tasks?skip=5&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 15
        assert data["skip"] == 5
        assert data["limit"] == 5
        assert len(data["data"]) == 5

    async def test_get_tasks_filter_enabled(self, async_client: AsyncClient):
        """Test filtering tasks by enabled status."""
        # Create enabled and disabled tasks
        for i in range(3):
            task_data = {
                "name": f"Enabled Task {i}",
                "command": "echo",
                "args": ["enabled"],
                "schedule_type": ScheduleType.INTERVAL.value,
                "interval_seconds": 60,
                "enabled": True,
                "timeout": 30,
                "max_concurrent": 1
            }
            await async_client.post("/tasks", json=task_data)

        for i in range(2):
            task_data = {
                "name": f"Disabled Task {i}",
                "command": "echo",
                "args": ["disabled"],
                "schedule_type": ScheduleType.INTERVAL.value,
                "interval_seconds": 60,
                "enabled": False,
                "timeout": 30,
                "max_concurrent": 1
            }
            await async_client.post("/tasks", json=task_data)

        # Get only enabled tasks
        response = await async_client.get("/tasks?enabled=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert all(task["enabled"] for task in data["data"])

        # Get only disabled tasks
        response = await async_client.get("/tasks?enabled=false")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(not task["enabled"] for task in data["data"])

    async def test_get_tasks_search(self, async_client: AsyncClient):
        """Test searching tasks by name or description."""
        # Create tasks with different names and descriptions
        tasks = [
            {
                "name": "Backup Database",
                "description": "Daily database backup",
                "command": "bash",
                "args": ["backup.sh"],
                "schedule_type": ScheduleType.CRON.value,
                "cron_expression": "0 2 * * *",
                "enabled": True,
                "timeout": 3600,
                "max_concurrent": 1
            },
            {
                "name": "Clean Logs",
                "description": "Clean old log files",
                "command": "rm",
                "args": ["-rf", "/tmp/logs/*.log"],
                "schedule_type": ScheduleType.CRON.value,
                "cron_expression": "0 3 * * *",
                "enabled": True,
                "timeout": 300,
                "max_concurrent": 1
            },
            {
                "name": "Monitor System",
                "description": "System monitoring script",
                "command": "python",
                "args": ["monitor.py"],
                "schedule_type": ScheduleType.INTERVAL.value,
                "interval_seconds": 300,
                "enabled": True,
                "timeout": 60,
                "max_concurrent": 1
            }
        ]

        for task_data in tasks:
            await async_client.post("/tasks", json=task_data)

        # Search for "backup"
        response = await async_client.get("/tasks?search=backup")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "backup" in data["data"][0]["name"].lower()

        # Search for "log"
        response = await async_client.get("/tasks?search=log")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "clean" in data["data"][0]["name"].lower()

    async def test_create_task_with_empty_args(self, async_client: AsyncClient):
        """Test creating a task with empty arguments list."""
        task_data = {
            "name": "Task with Empty Args",
            "command": "echo",
            "args": [],
            "schedule_type": ScheduleType.CRON.value,
            "cron_expression": "* * * * *",
            "enabled": True,
            "timeout": 30,
            "max_concurrent": 1
        }

        response = await async_client.post("/tasks/", json=task_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == task_data["name"]
        assert data["args"] == []  # Should preserve empty list

    async def test_create_task_with_null_description(self, async_client: AsyncClient):
        """Test creating a task with null description."""
        task_data = {
            "name": "Task with Null Description",
            "command": "pwd",
            "args": [],
            "schedule_type": ScheduleType.INTERVAL.value,
            "interval_seconds": 60,
            "enabled": True,
            "timeout": 30,
            "max_concurrent": 1
        }
        # description is omitted, should default to null

        response = await async_client.post("/tasks/", json=task_data)
        assert response.status_code == 201
        data = response.json()
        assert data["description"] is None

    async def test_update_task_partial_schedule_info(self, async_client: AsyncClient):
        """Test updating task with partial schedule information."""
        # Create an interval task
        task_data = {
            "name": "Interval Task",
            "command": "echo",
            "args": ["test"],
            "schedule_type": ScheduleType.INTERVAL.value,
            "interval_seconds": 60,
            "enabled": True,
            "timeout": 30,
            "max_concurrent": 1
        }

        create_response = await async_client.post("/tasks", json=task_data)
        task_id = create_response.json()["id"]

        # Update just the interval seconds
        update_data = {
            "interval_seconds": 120
        }

        response = await async_client.put(f"/tasks/{task_id}", json=update_data)
        assert response.status_code == 200
        updated_task = response.json()
        assert updated_task["interval_seconds"] == 120
        # Other fields should remain unchanged
        assert updated_task["schedule_type"] == ScheduleType.INTERVAL.value
        assert updated_task["name"] == "Interval Task"

    async def test_update_task_invalid_schedule_combination(self, async_client: AsyncClient):
        """Test updating task with invalid schedule type and expression combination."""
        # Create a cron task
        task_data = {
            "name": "Cron Task",
            "command": "echo",
            "args": ["test"],
            "schedule_type": ScheduleType.CRON.value,
            "cron_expression": "*/5 * * * *",
            "enabled": True,
            "timeout": 30,
            "max_concurrent": 1
        }

        create_response = await async_client.post("/tasks", json=task_data)
        task_id = create_response.json()["id"]

        # Try to change to interval but forget to set interval_seconds
        update_data = {
            "schedule_type": ScheduleType.INTERVAL.value,
            "cron_expression": None  # Remove cron expression
        }

        response = await async_client.put(f"/tasks/{task_id}", json=update_data)
        assert response.status_code == 422
        assert "interval_seconds" in response.text.lower()

    async def test_get_tasks_with_invalid_pagination(self, async_client: AsyncClient):
        """Test getting tasks with invalid pagination parameters."""
        # Negative skip value
        response = await async_client.get("/tasks?skip=-1")
        assert response.status_code == 422

        # Zero limit (should fail as limit must be >= 1)
        response = await async_client.get("/tasks?limit=0")
        assert response.status_code == 422

        # Limit too large
        response = await async_client.get("/tasks?limit=1001")
        assert response.status_code == 422

    async def test_task_enable_disable_scheduler_interaction(self, async_client: AsyncClient):
        """Test that enabling/disabling task updates scheduler."""
        # Create a disabled task
        task_data = {
            "name": "Scheduler Test Task",
            "command": "echo",
            "args": ["scheduler test"],
            "schedule_type": ScheduleType.INTERVAL.value,
            "interval_seconds": 60,
            "enabled": False,
            "timeout": 30,
            "max_concurrent": 1
        }

        create_response = await async_client.post("/tasks", json=task_data)
        task_id = create_response.json()["id"]

        # Enable the task
        update_data = {"enabled": True}
        response = await async_client.put(f"/tasks/{task_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["enabled"] is True

        # Disable the task
        update_data = {"enabled": False}
        response = await async_client.put(f"/tasks/{task_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["enabled"] is False

    async def test_task_args_json_validation(self, async_client: AsyncClient):
        """Test that task args are properly validated as JSON array."""
        task_data = {
            "name": "Task with Complex Args",
            "command": "python",
            "args": ["script.py", "--verbose", "--output", "file.txt"],
            "schedule_type": ScheduleType.CRON.value,
            "cron_expression": "* * * * *",
            "enabled": True,
            "timeout": 60,
            "max_concurrent": 1
        }

        response = await async_client.post("/tasks/", json=task_data)
        assert response.status_code == 201
        data = response.json()
        # Verify args are preserved as array
        assert data["args"] == ["script.py", "--verbose", "--output", "file.txt"]
        assert len(data["args"]) == 4

    async def test_update_task_with_empty_update(self, async_client: AsyncClient):
        """Test updating a task with empty update data."""
        # Create a task
        task_data = {
            "name": "Task for Empty Update",
            "command": "echo",
            "args": ["test"],
            "schedule_type": ScheduleType.CRON.value,
            "cron_expression": "* * * * *",
            "enabled": True,
            "timeout": 30,
            "max_concurrent": 1
        }

        create_response = await async_client.post("/tasks", json=task_data)
        task_id = create_response.json()["id"]

        # Update with empty dict (should succeed and not change anything)
        update_data = {}
        response = await async_client.put(f"/tasks/{task_id}", json=update_data)
        assert response.status_code == 200
        updated_task = response.json()
        # All fields should remain the same
        assert updated_task["name"] == "Task for Empty Update"
        assert updated_task["command"] == "echo"
        assert updated_task["cron_expression"] == "* * * * *"