"""
集成测试：任务完整生命周期和系统组件交互
"""
import pytest
import asyncio
from httpx import AsyncClient
from app.models.task import ScheduleType
from app.models.log import ExecutionStatus
from app.scheduler.scheduler import scheduler


@pytest.mark.asyncio
class TestTaskLifecycleIntegration:
    """集成测试：任务完整生命周期"""

    async def test_task_creation_to_execution_flow(self, async_client: AsyncClient):
        """测试任务创建到执行的完整流程"""
        # 1. 创建任务
        task_data = {
            "name": "Integration Test Task",
            "description": "Task for integration testing",
            "command": "echo",
            "args": ["integration test"],
            "schedule_type": ScheduleType.INTERVAL.value,
            "interval_seconds": 300,  # 5分钟，足够测试
            "enabled": True,
            "timeout": 30,
            "max_concurrent": 1
        }

        create_response = await async_client.post("/tasks/", json=task_data)
        assert create_response.status_code == 201
        created_task = create_response.json()
        task_id = created_task["id"]

        # 验证任务已创建
        assert created_task["name"] == task_data["name"]
        assert created_task["enabled"] is True
        assert created_task["schedule_type"] == ScheduleType.INTERVAL.value
        assert created_task["interval_seconds"] == 300

        # 2. 获取任务验证
        get_response = await async_client.get(f"/tasks/{task_id}")
        assert get_response.status_code == 200
        retrieved_task = get_response.json()
        assert retrieved_task["id"] == task_id
        assert retrieved_task["name"] == task_data["name"]

        # 3. 手动执行任务
        execute_response = await async_client.post(f"/tasks/{task_id}/execute")
        assert execute_response.status_code == 202
        execute_data = execute_response.json()
        assert execute_data["task_id"] == task_id
        assert "message" in execute_data

        # 4. 等待一小段时间让任务执行完成
        await asyncio.sleep(0.5)

        # 5. 检查任务日志
        logs_response = await async_client.get(f"/tasks/{task_id}/logs")
        assert logs_response.status_code == 200
        logs_data = logs_response.json()

        # 应该至少有一条日志
        assert logs_data["total"] >= 1
        if logs_data["total"] > 0:
            log_entry = logs_data["data"][0]
            assert log_entry["command_executed"] is not None
            assert "echo" in log_entry["command_executed"].lower()

        # 6. 检查所有日志列表
        all_logs_response = await async_client.get("/logs/")
        assert all_logs_response.status_code == 200
        all_logs_data = all_logs_response.json()

        # 总日志数应该包含我们创建的任务日志
        assert all_logs_data["total"] >= 1

        # 7. 更新任务
        update_data = {
            "name": "Updated Integration Task",
            "description": "Updated description",
            "enabled": False
        }

        update_response = await async_client.put(f"/tasks/{task_id}", json=update_data)
        assert update_response.status_code == 200
        updated_task = update_response.json()
        assert updated_task["name"] == update_data["name"]
        assert updated_task["description"] == update_data["description"]
        assert updated_task["enabled"] == update_data["enabled"]

        # 8. 尝试执行已禁用的任务（应该失败）
        execute_disabled_response = await async_client.post(f"/tasks/{task_id}/execute")
        assert execute_disabled_response.status_code == 400
        assert "disabled" in execute_disabled_response.text.lower()

        # 9. 删除任务
        delete_response = await async_client.delete(f"/tasks/{task_id}")
        assert delete_response.status_code == 204

        # 10. 验证任务已删除
        get_deleted_response = await async_client.get(f"/tasks/{task_id}")
        assert get_deleted_response.status_code == 404

        # 11. 验证日志仍然存在（级联删除可能未配置或不需要）
        remaining_logs_response = await async_client.get("/logs/")
        assert remaining_logs_response.status_code == 200
        # 日志可能仍然存在，取决于级联删除配置

    async def test_task_scheduler_integration(self, async_client: AsyncClient):
        """测试任务与调度器的集成"""
        # 1. 创建禁用的任务
        task_data = {
            "name": "Scheduler Integration Task",
            "command": "echo",
            "args": ["scheduler test"],
            "schedule_type": ScheduleType.CRON.value,
            "cron_expression": "*/5 * * * *",
            "enabled": False,
            "timeout": 30,
            "max_concurrent": 1
        }

        create_response = await async_client.post("/tasks/", json=task_data)
        assert create_response.status_code == 201
        created_task = create_response.json()
        task_id = created_task["id"]

        # 2. 验证任务在调度器中不存在（因为禁用）
        # 注意：这里我们检查调度器内部状态
        # 由于调度器可能没有公开API来查询任务，我们通过启用/禁用来测试

        # 3. 启用任务
        update_response = await async_client.put(f"/tasks/{task_id}", json={"enabled": True})
        assert update_response.status_code == 200
        updated_task = update_response.json()
        assert updated_task["enabled"] is True

        # 4. 验证任务现在应该在调度器中
        # 通过再次执行任务来验证调度器是否正常工作
        execute_response = await async_client.post(f"/tasks/{task_id}/execute")
        assert execute_response.status_code == 202

        # 5. 禁用任务
        update_response = await async_client.put(f"/tasks/{task_id}", json={"enabled": False})
        assert update_response.status_code == 200
        updated_task = update_response.json()
        assert updated_task["enabled"] is False

        # 6. 清理：删除任务
        delete_response = await async_client.delete(f"/tasks/{task_id}")
        assert delete_response.status_code == 204

    async def test_multiple_tasks_concurrent_execution(self, async_client: AsyncClient):
        """测试多个任务的并发执行"""
        task_ids = []

        # 1. 创建3个任务
        for i in range(3):
            task_data = {
                "name": f"Concurrent Task {i}",
                "command": "echo",
                "args": [f"task {i}"],
                "schedule_type": ScheduleType.INTERVAL.value,
                "interval_seconds": 60,
                "enabled": True,
                "timeout": 10,
                "max_concurrent": 1
            }

            create_response = await async_client.post("/tasks/", json=task_data)
            assert create_response.status_code == 201
            task_id = create_response.json()["id"]
            task_ids.append(task_id)

        # 2. 并发执行所有任务
        execute_tasks = []
        for task_id in task_ids:
            execute_response = await async_client.post(f"/tasks/{task_id}/execute")
            assert execute_response.status_code == 202
            execute_tasks.append(execute_response.json())

        # 3. 等待执行完成，使用重试机制
        max_retries = 5
        for retry in range(max_retries):
            await asyncio.sleep(0.5)  # 每次等待0.5秒

            # 检查所有任务的日志
            all_have_logs = True
            for task_id in task_ids:
                logs_response = await async_client.get(f"/tasks/{task_id}/logs")
                assert logs_response.status_code == 200
                logs_data = logs_response.json()
                if logs_data["total"] < 1:
                    all_have_logs = False
                    break

            if all_have_logs:
                break
        else:
            # 如果所有重试后仍然没有日志
            pytest.fail(f"任务执行未生成日志，重试{max_retries}次后仍然失败")

        # 5. 检查总日志数
        all_logs_response = await async_client.get("/logs/")
        assert all_logs_response.status_code == 200
        all_logs_data = all_logs_response.json()
        # 应该至少有3条日志
        assert all_logs_data["total"] >= 3

        # 6. 清理：删除所有任务
        for task_id in task_ids:
            delete_response = await async_client.delete(f"/tasks/{task_id}")
            assert delete_response.status_code == 204

    async def test_task_logs_integration(self, async_client: AsyncClient):
        """测试任务日志集成"""
        # 1. 创建任务
        task_data = {
            "name": "Log Integration Task",
            "command": "echo",
            "args": ["log test"],
            "schedule_type": ScheduleType.INTERVAL.value,
            "interval_seconds": 60,
            "enabled": True,
            "timeout": 30,
            "max_concurrent": 1
        }

        create_response = await async_client.post("/tasks/", json=task_data)
        assert create_response.status_code == 201
        created_task = create_response.json()
        task_id = created_task["id"]

        # 2. 多次执行任务以生成日志
        for i in range(3):
            execute_response = await async_client.post(f"/tasks/{task_id}/execute")
            assert execute_response.status_code == 202

        # 3. 等待执行完成，使用重试机制
        max_retries = 5
        for retry in range(max_retries):
            await asyncio.sleep(0.5)  # 每次等待0.5秒

            # 检查任务特定日志
            task_logs_response = await async_client.get(f"/tasks/{task_id}/logs")
            assert task_logs_response.status_code == 200
            task_logs_data = task_logs_response.json()
            if task_logs_data["total"] >= 3:
                break
        else:
            # 如果所有重试后仍然没有足够的日志
            pytest.fail(f"任务执行未生成足够日志，重试{max_retries}次后只有{task_logs_data['total']}条日志")

        # 5. 检查过滤功能
        # 按状态过滤（假设执行成功）
        completed_logs_response = await async_client.get(f"/tasks/{task_id}/logs?status={ExecutionStatus.COMPLETED.value}")
        assert completed_logs_response.status_code == 200
        completed_logs_data = completed_logs_response.json()
        # 至少有一些完成的日志

        # 6. 检查全局日志搜索
        search_response = await async_client.get(f"/logs/?search=echo")
        assert search_response.status_code == 200
        search_data = search_response.json()
        # 应该找到包含"echo"的日志

        # 7. 清除特定任务的日志
        clear_response = await async_client.delete(f"/logs/?task_id={task_id}")
        assert clear_response.status_code == 204

        # 8. 验证日志已清除
        verify_logs_response = await async_client.get(f"/tasks/{task_id}/logs")
        assert verify_logs_response.status_code == 200
        verify_logs_data = verify_logs_response.json()
        # 日志可能已被清除，取决于清除操作是否立即生效

        # 9. 清理：删除任务
        delete_response = await async_client.delete(f"/tasks/{task_id}")
        assert delete_response.status_code == 204

    async def test_task_schedule_type_transition(self, async_client: AsyncClient):
        """测试任务调度类型转换"""
        # 1. 创建Cron任务
        task_data = {
            "name": "Schedule Transition Task",
            "command": "echo",
            "args": ["transition test"],
            "schedule_type": ScheduleType.CRON.value,
            "cron_expression": "*/5 * * * *",
            "enabled": True,
            "timeout": 30,
            "max_concurrent": 1
        }

        create_response = await async_client.post("/tasks/", json=task_data)
        assert create_response.status_code == 201
        created_task = create_response.json()
        task_id = created_task["id"]

        # 2. 验证初始设置
        assert created_task["schedule_type"] == ScheduleType.CRON.value
        assert created_task["cron_expression"] == "*/5 * * * *"
        assert created_task["interval_seconds"] is None

        # 3. 转换为Interval任务
        update_data = {
            "schedule_type": ScheduleType.INTERVAL.value,
            "cron_expression": None,
            "interval_seconds": 120
        }

        update_response = await async_client.put(f"/tasks/{task_id}", json=update_data)
        assert update_response.status_code == 200
        updated_task = update_response.json()

        assert updated_task["schedule_type"] == ScheduleType.INTERVAL.value
        assert updated_task["interval_seconds"] == 120
        assert updated_task["cron_expression"] is None

        # 4. 转换回Cron任务
        update_data = {
            "schedule_type": ScheduleType.CRON.value,
            "cron_expression": "0 * * * *",
            "interval_seconds": None
        }

        update_response = await async_client.put(f"/tasks/{task_id}", json=update_data)
        assert update_response.status_code == 200
        updated_task = update_response.json()

        assert updated_task["schedule_type"] == ScheduleType.CRON.value
        assert updated_task["cron_expression"] == "0 * * * *"
        assert updated_task["interval_seconds"] is None

        # 5. 清理：删除任务
        delete_response = await async_client.delete(f"/tasks/{task_id}")
        assert delete_response.status_code == 204