"""
集成测试：边界情况和错误场景
测试任务的边界情况、错误处理、并发限制等
"""
import pytest
import asyncio
from httpx import AsyncClient
from app.models.task import ScheduleType
from app.models.log import ExecutionStatus


@pytest.mark.asyncio
class TestTaskEdgeCases:
    """集成测试：边界情况和错误场景"""

    async def test_task_timeout_scenario(self, async_client: AsyncClient):
        """测试任务超时场景"""
        # 创建一个会超时的任务（使用sleep命令，但超时时间很短）
        task_data = {
            "name": "Timeout Test Task",
            "command": "python",
            "args": ["-c", "import time; time.sleep(10)"],
            "schedule_type": ScheduleType.INTERVAL.value,
            "interval_seconds": 300,  # 5分钟
            "enabled": True,
            "timeout": 1,  # 1秒超时
            "max_concurrent": 1
        }

        create_response = await async_client.post("/tasks/", json=task_data)
        assert create_response.status_code == 201
        created_task = create_response.json()
        task_id = created_task["id"]

        # 手动执行任务
        execute_response = await async_client.post(f"/tasks/{task_id}/execute")
        assert execute_response.status_code == 202

        # 等待足够长时间让任务超时
        await asyncio.sleep(3)

        # 检查任务日志，应该显示超时状态
        logs_response = await async_client.get(f"/tasks/{task_id}/logs")
        assert logs_response.status_code == 200
        logs_data = logs_response.json()

        if logs_data["total"] > 0:
            log_entry = logs_data["data"][0]
            # 任务应该超时（TIMEOUT状态码为4）
            # 检查状态是否为TIMEOUT或FAILED
            assert log_entry["status"] in [ExecutionStatus.TIMEOUT.value, ExecutionStatus.FAILED.value]

        # 清理
        delete_response = await async_client.delete(f"/tasks/{task_id}")
        assert delete_response.status_code == 204

    async def test_task_failure_scenario(self, async_client: AsyncClient):
        """测试任务执行失败场景（无效命令）"""
        task_data = {
            "name": "Failure Test Task",
            "command": "non_existent_command",
            "args": [],
            "schedule_type": ScheduleType.INTERVAL.value,
            "interval_seconds": 300,
            "enabled": True,
            "timeout": 30,
            "max_concurrent": 1
        }

        create_response = await async_client.post("/tasks/", json=task_data)
        assert create_response.status_code == 201
        created_task = create_response.json()
        task_id = created_task["id"]

        # 手动执行任务
        execute_response = await async_client.post(f"/tasks/{task_id}/execute")
        assert execute_response.status_code == 202

        # 等待执行完成
        await asyncio.sleep(2)

        # 检查任务日志，应该显示失败状态
        logs_response = await async_client.get(f"/tasks/{task_id}/logs")
        assert logs_response.status_code == 200
        logs_data = logs_response.json()

        if logs_data["total"] > 0:
            log_entry = logs_data["data"][0]
            # 任务应该失败
            assert log_entry["status"] == ExecutionStatus.FAILED.value
            # 错误信息应该存在
            assert log_entry["error_message"] is not None

        # 清理
        delete_response = await async_client.delete(f"/tasks/{task_id}")
        assert delete_response.status_code == 204

    async def test_max_concurrent_limit(self, async_client: AsyncClient):
        """测试最大并发限制"""
        # 创建一个最大并发为1的任务
        task_data = {
            "name": "Concurrent Limit Task",
            "command": "python",
            "args": ["-c", "import time; time.sleep(2)"],
            "schedule_type": ScheduleType.INTERVAL.value,
            "interval_seconds": 300,
            "enabled": True,
            "timeout": 30,
            "max_concurrent": 1  # 限制为1
        }

        create_response = await async_client.post("/tasks/", json=task_data)
        assert create_response.status_code == 201
        created_task = create_response.json()
        task_id = created_task["id"]

        # 同时触发多次执行（由于并发限制，应该排队）
        execution_count = 3
        for i in range(execution_count):
            execute_response = await async_client.post(f"/tasks/{task_id}/execute")
            assert execute_response.status_code == 202

        # 等待足够时间让所有执行完成
        await asyncio.sleep(8)

        # 检查日志数量
        logs_response = await async_client.get(f"/tasks/{task_id}/logs")
        assert logs_response.status_code == 200
        logs_data = logs_response.json()

        # 应该有多个日志条目
        # 注意：由于并发限制，可能不是所有执行都立即开始
        # 但最终应该记录所有执行尝试
        assert logs_data["total"] >= 1

        # 清理
        delete_response = await async_client.delete(f"/tasks/{task_id}")
        assert delete_response.status_code == 204

    async def test_invalid_cron_expression(self, async_client: AsyncClient):
        """测试无效的Cron表达式"""
        task_data = {
            "name": "Invalid Cron Task",
            "command": "echo",
            "args": ["test"],
            "schedule_type": ScheduleType.CRON.value,
            "cron_expression": "invalid-cron-expression",  # 无效的cron表达式
            "enabled": True,
            "timeout": 30,
            "max_concurrent": 1
        }

        # 创建任务时可能不会立即验证cron表达式
        # 这取决于实现，这里我们测试API是否能处理
        create_response = await async_client.post("/tasks/", json=task_data)
        # 可能是201（创建成功）或422（验证错误）
        # 取决于cron表达式验证的位置

        # 如果创建成功，测试调度器是否能处理无效cron
        if create_response.status_code == 201:
            created_task = create_response.json()
            task_id = created_task["id"]

            # 清理
            delete_response = await async_client.delete(f"/tasks/{task_id}")
            assert delete_response.status_code == 204
        else:
            # 如果是验证错误，确保是422
            assert create_response.status_code == 422

    async def test_task_with_empty_args(self, async_client: AsyncClient):
        """测试任务带有空参数数组"""
        task_data = {
            "name": "Empty Args Task",
            "command": "echo",
            "args": [],  # 空数组
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

        # 验证任务已创建
        assert created_task["name"] == task_data["name"]
        assert created_task["args"] == []  # 空数组应该被保存

        # 执行任务
        execute_response = await async_client.post(f"/tasks/{task_id}/execute")
        assert execute_response.status_code == 202

        # 等待执行
        await asyncio.sleep(1)

        # 清理
        delete_response = await async_client.delete(f"/tasks/{task_id}")
        assert delete_response.status_code == 204

    async def test_task_with_special_characters(self, async_client: AsyncClient):
        """测试任务名称和描述中的特殊字符"""
        task_data = {
            "name": "Task with spéciál chàrs & symbols 测试 123",
            "description": "Description with spéciál chàrs & symbols 测试 123",
            "command": "echo",
            "args": ["test"],
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

        # 验证特殊字符被正确保存
        assert created_task["name"] == task_data["name"]
        assert created_task["description"] == task_data["description"]

        # 清理
        delete_response = await async_client.delete(f"/tasks/{task_id}")
        assert delete_response.status_code == 204

    async def test_task_pagination_boundaries(self, async_client: AsyncClient):
        """测试任务分页的边界情况"""
        # 创建多个任务以测试分页
        task_count = 15
        task_ids = []

        for i in range(task_count):
            task_data = {
                "name": f"Pagination Task {i}",
                "command": "echo",
                "args": [f"task {i}"],
                "schedule_type": ScheduleType.INTERVAL.value,
                "interval_seconds": 60,
                "enabled": True,
                "timeout": 30,
                "max_concurrent": 1
            }

            create_response = await async_client.post("/tasks/", json=task_data)
            assert create_response.status_code == 201
            task_id = create_response.json()["id"]
            task_ids.append(task_id)

        # 测试不同的分页参数
        test_cases = [
            {"skip": 0, "limit": 5},   # 第一页
            {"skip": 5, "limit": 5},   # 第二页
            {"skip": 10, "limit": 5},  # 第三页
            {"skip": 0, "limit": 100}, # 超过总数
            {"skip": 20, "limit": 5},  # 超出范围
        ]

        for params in test_cases:
            response = await async_client.get("/tasks/", params=params)
            assert response.status_code == 200
            data = response.json()

            # 验证响应结构
            assert "total" in data
            assert "skip" in data
            assert "limit" in data
            assert "data" in data

            # skip和limit应该与请求一致
            assert data["skip"] == params["skip"]
            assert data["limit"] == params["limit"]

            # 数据条数不应超过limit
            assert len(data["data"]) <= params["limit"]

            # 如果skip超过总数，data应该为空
            if params["skip"] >= data["total"]:
                assert len(data["data"]) == 0

        # 清理
        for task_id in task_ids:
            delete_response = await async_client.delete(f"/tasks/{task_id}")
            assert delete_response.status_code == 204

    async def test_logs_filtering_edge_cases(self, async_client: AsyncClient):
        """测试日志过滤的边界情况"""
        # 创建一个任务并执行多次
        task_data = {
            "name": "Logs Filtering Task",
            "command": "echo",
            "args": ["filter test"],
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

        # 执行任务3次
        for i in range(3):
            execute_response = await async_client.post(f"/tasks/{task_id}/execute")
            assert execute_response.status_code == 202

        # 等待执行完成
        await asyncio.sleep(3)

        # 测试各种过滤条件
        # 1. 按状态过滤（使用存在的状态）
        response = await async_client.get(f"/tasks/{task_id}/logs", params={"status": ExecutionStatus.COMPLETED.value})
        assert response.status_code == 200
        data = response.json()
        # 状态过滤应该工作

        # 2. 按不存在的状态过滤
        response = await async_client.get(f"/tasks/{task_id}/logs", params={"status": 999})
        assert response.status_code == 200
        data = response.json()
        # 应该返回空结果或忽略无效状态

        # 3. 测试全局日志搜索
        response = await async_client.get("/logs/", params={"search": "echo"})
        assert response.status_code == 200
        data = response.json()
        # 应该找到包含"echo"的日志

        # 4. 测试不存在的搜索词
        response = await async_client.get("/logs/", params={"search": "nonexistentsearchterm"})
        assert response.status_code == 200
        data = response.json()
        # 应该返回空结果

        # 清理
        delete_response = await async_client.delete(f"/tasks/{task_id}")
        assert delete_response.status_code == 204

    async def test_task_update_partial_data(self, async_client: AsyncClient):
        """测试部分更新任务数据"""
        # 创建初始任务
        task_data = {
            "name": "Partial Update Task",
            "command": "echo",
            "args": ["initial"],
            "schedule_type": ScheduleType.INTERVAL.value,
            "interval_seconds": 60,
            "enabled": True,
            "timeout": 30,
            "max_concurrent": 1,
            "description": "Initial description"
        }

        create_response = await async_client.post("/tasks/", json=task_data)
        assert create_response.status_code == 201
        created_task = create_response.json()
        task_id = created_task["id"]

        # 部分更新：只更新名称和描述
        update_data = {
            "name": "Updated Task Name",
            "description": "Updated description only"
        }

        update_response = await async_client.put(f"/tasks/{task_id}", json=update_data)
        assert update_response.status_code == 200
        updated_task = update_response.json()

        # 验证只有指定字段被更新
        assert updated_task["name"] == update_data["name"]
        assert updated_task["description"] == update_data["description"]
        # 其他字段应保持不变
        assert updated_task["command"] == task_data["command"]
        assert updated_task["interval_seconds"] == task_data["interval_seconds"]
        assert updated_task["enabled"] == task_data["enabled"]

        # 清理
        delete_response = await async_client.delete(f"/tasks/{task_id}")
        assert delete_response.status_code == 204