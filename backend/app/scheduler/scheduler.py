import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
from datetime import datetime, timezone
import sys
from typing import Optional, Dict, Any, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from app.models.task import Task, ScheduleType
from app.models.log import TaskLog, ExecutionStatus
from app.config import settings
import subprocess
import shlex

logger = logging.getLogger(__name__)

def run_command_in_thread(*cmd_args):
    """
    在线程中执行命令的同步函数
    这里需要根据你的实际需求实现具体的命令执行逻辑
    """
    # 示例：执行一个同步操作
    # 在实际应用中，这里可能是调用某个同步库或执行同步代码
    import subprocess
    import sys
    
    # 如果是要执行系统命令，可以使用 subprocess.run
    result = subprocess.run(
        cmd_args,
        capture_output=True,
        text=True,
        timeout=None  # 超时由外层的 asyncio.wait_for 控制
    )
    
    return result.returncode, result.stdout, result.stderr

executor = ThreadPoolExecutor(max_workers=8)

import asyncio
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
class AsyncSubprocess:
    """将 subprocess 包装为异步形式"""
    
    def __init__(self):
        pass
    
    async def run_with_timeout(self, cmd, timeout):
        """运行命令并设置超时"""
        process = None
        
        try:
            # 在线程池中运行阻塞的 subprocess 调用
            process = await asyncio.get_event_loop().run_in_executor(
                executor,
                lambda: subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,  # 返回字符串而不是字节
                    encoding='utf-8',
                    errors='ignore'
                )
            )
            
            # 创建异步任务来等待进程完成
            communicate_task = asyncio.create_task(
                self._communicate_async(process)
            )
            
            try:
                # 等待进程完成或超时
                stdout, stderr = await asyncio.wait_for(
                    communicate_task,
                    timeout=timeout
                )
                exit_code = process.returncode
                return exit_code, stdout, stderr
                
            except asyncio.TimeoutError:
                # 超时处理
                communicate_task.cancel()
                
                # Windows 特定的终止方式
                if sys.platform == 'win32':
                    self._terminate_windows(process)
                else:
                    process.terminate()
                
                # 等待进程真正结束
                await asyncio.get_event_loop().run_in_executor(
                    executor,
                    process.wait
                )
                
                raise TimeoutError(f"Task timed out after {timeout} seconds")
                
        except Exception as e:
            # 异常处理
            if process and process.poll() is None:
                if sys.platform == 'win32':
                    self._terminate_windows(process)
                else:
                    process.terminate()
                await asyncio.get_event_loop().run_in_executor(
                    executor,
                    process.wait
                )
            raise e
    
    async def _communicate_async(self, process: subprocess.Popen[str]):
        """异步版本的 communicate()"""
        loop = asyncio.get_event_loop()
        
        # 并行读取 stdout 和 stderr
        stdout_future = loop.run_in_executor(
            executor,
            process.stdout.read
        )
        stderr_future = loop.run_in_executor(
            executor,
            process.stderr.read
        )
        
        # 等待进程结束
        wait_future = loop.run_in_executor(
            executor,
            process.wait
        )
        
        # 等待所有任务完成
        stdout, stderr, _ = await asyncio.gather(
            stdout_future,
            stderr_future,
            wait_future
        )
        
        return stdout, stderr
    
    def _terminate_windows(self, process):
        """Windows 上的进程终止方法"""
        try:
            # 尝试优雅终止
            process.terminate()
        except:
            try:
                # 使用 taskkill 强制终止
                subprocess.run(
                    ['taskkill', '/F', '/T', '/PID', str(process.pid)],
                    capture_output=True,
                    timeout=2
                )
            except:
                pass


class TaskScheduler:
    """
    Task scheduler service using APScheduler
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler(
            job_defaults=settings.scheduler_job_defaults,
            timezone=None
        )
        self.running_jobs: Dict[int, asyncio.Task] = {}
        self.job_id_map: Dict[int, str] = {}  # task_id -> scheduler job id

    async def start(self):
        """
        Start the scheduler
        """
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Task scheduler started")

    async def stop(self):
        """
        Stop the scheduler
        """
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Task scheduler stopped")

    async def add_task(self, task: Task) -> Optional[str]:
        """
        Add a task to the scheduler
        Returns job ID if successful
        """
        if not task.enabled:
            logger.info(f"Task {task.id} is disabled, not scheduling")
            return None

        # Remove existing job if any
        await self.remove_task(task.id)

        # Create trigger based on schedule type
        if task.schedule_type == ScheduleType.CRON:
            if not task.cron_expression:
                logger.error(f"Task {task.id} has cron schedule type but no cron expression")
                return None
            try:
                # Parse cron expression
                parts = task.cron_expression.split()
                if len(parts) != 5:
                    raise ValueError(f"Invalid cron expression: {task.cron_expression}")
                trigger = CronTrigger.from_crontab(task.cron_expression)
            except Exception as e:
                logger.error(f"Failed to parse cron expression for task {task.id}: {e}")
                return None
        elif task.schedule_type == ScheduleType.INTERVAL:
            if not task.interval_seconds:
                logger.error(f"Task {task.id} has interval schedule type but no interval_seconds")
                return None
            trigger = IntervalTrigger(seconds=task.interval_seconds)
        else:
            logger.error(f"Unknown schedule type for task {task.id}: {task.schedule_type}")
            return None

        # Add job to scheduler
        job_id = f"task_{task.id}"
        try:
            self.scheduler.add_job(
                self._execute_task_wrapper,
                trigger=trigger,
                args=[task.id],
                id=job_id,
                replace_existing=True,
                name=f"Task: {task.name}",
                misfire_grace_time=settings.scheduler_job_defaults.get("misfire_grace_time", 60)
            )
            self.job_id_map[task.id] = job_id
            logger.info(f"Scheduled task {task.id} ({task.name}) with {trigger}")
            return job_id
        except Exception as e:
            logger.error(f"Failed to schedule task {task.id}: {e}")
            return None

    async def remove_task(self, task_id: int):
        """
        Remove a task from the scheduler
        """
        job_id = self.job_id_map.get(task_id)
        if job_id:
            try:
                self.scheduler.remove_job(job_id)
                del self.job_id_map[task_id]
                logger.info(f"Removed scheduled task {task_id}")
            except Exception as e:
                logger.error(f"Failed to remove scheduled task {task_id}: {e}")

        # Cancel any running execution
        if task_id in self.running_jobs:
            running_task = self.running_jobs[task_id]
            if not running_task.done():
                running_task.cancel()
                try:
                    await running_task
                except asyncio.CancelledError:
                    pass
            del self.running_jobs[task_id]

    async def _execute_task_wrapper(self, task_id: int):
        """
        Wrapper for task execution to handle concurrent limits
        """
        # Check concurrent executions
        task = await Task.get_or_none(id=task_id)
        if not task or not task.enabled:
            return

        # Check if already running
        if task_id in self.running_jobs:
            running_task = self.running_jobs[task_id]
            if not running_task.done():
                logger.warning(f"Task {task_id} is already running, skipping")
                return

        # Check concurrent limit
        running_count = sum(1 for t in self.running_jobs.values() if not t.done())
        if running_count >= task.max_concurrent:
            logger.warning(f"Concurrent limit reached for task {task_id}, skipping")
            return

        # Execute task
        execution_task = asyncio.create_task(self._execute_task(task))
        self.running_jobs[task_id] = execution_task
        try:
            await execution_task
        except asyncio.CancelledError:
            logger.info(f"Task {task_id} execution cancelled")
        except Exception as e:
            logger.error(f"Task {task_id} execution failed: {e}")
            logger.exception('exception detail: ')
        finally:
            if task_id in self.running_jobs:
                del self.running_jobs[task_id]

    async def do_execute_task(self, command: str, args: list[str], timeout: int):
        """
        单纯地执行命令并返回返回码，标准输出流，标准错误流
        """
        cmd = [command, *(str(x) for x in args)]
        async_subprocess = AsyncSubprocess()
        exit_code, stdout, stderr = await async_subprocess.run_with_timeout(
            cmd=cmd,
            timeout=timeout
        )
        return exit_code, stdout, stderr

    async def _execute_task(self, task: Task):
        """
        Execute a task command and log results
        """
        log = TaskLog(
            task=task,
            status=ExecutionStatus.RUNNING,
            command_executed=f"{task.command} {' '.join(map(str, task.args))}",
            started_at=datetime.now(timezone.utc)
        )
        await log.save()

        try:
            # Build command
            cmd = [task.command] + [str(arg) for arg in task.args]

            # Execute command with timeout
            logger.info(f"Executing task {task.id}: {' '.join(cmd)}")

            async_subprocess = AsyncSubprocess()
    
            try:
                exit_code, stdout, stderr = await async_subprocess.run_with_timeout(
                    cmd=cmd,
                    timeout=task.timeout
                )
                
                log.stdout = stdout
                log.stderr = stderr
                log.exit_code = exit_code
            except TimeoutError:
                log.status = ExecutionStatus.TIMEOUT
                log.error_message = f"Task timed out after {task.timeout} seconds"
                log.stdout = ""
                log.stderr = ""
                log.exit_code = -1
            except Exception as e:
                raise e

            # Update log with results
            log.finished_at = datetime.now(timezone.utc)
            log.duration = (log.finished_at - log.started_at).total_seconds()
            log.exit_code = exit_code

            if exit_code == 0:
                log.status = ExecutionStatus.COMPLETED
            else:
                log.status = ExecutionStatus.FAILED
                log.error_message = f"Command failed with exit code {exit_code}"

            # Decode output
            log.stdout = stdout if stdout else ""
            log.stderr = stderr if stderr else ""

            logger.info(f"Task {task.id} completed with status {log.status.name} "
                       f"(exit code: {exit_code}, duration: {log.duration:.2f}s)")

        except Exception as e:
            # Unexpected error during execution
            log.finished_at = datetime.now(timezone.utc)
            log.duration = (log.finished_at - log.started_at).total_seconds()
            log.status = ExecutionStatus.FAILED
            log.error_message = str(e)
            log.stdout = ""
            log.stderr = ""
            logger.error(f"Task {task.id} execution error: {e}")
            logger.exception('exception detail:')

        await log.save()

    async def execute_now(self, task_id: int) -> Optional[int]:
        """
        Execute a task immediately
        Returns log ID if execution started
        """
        task = await Task.get_or_none(id=task_id)
        if not task:
            return None

        # Create execution task
        execution_task = asyncio.create_task(self._execute_task(task))
        self.running_jobs[task_id] = execution_task
        return task_id

    async def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """
        Get list of scheduled tasks
        """
        jobs = self.scheduler.get_jobs()
        result = []
        for job in jobs:
            task_id = int(job.id.split('_')[1]) if job.id.startswith('task_') else None
            result.append({
                "job_id": job.id,
                "task_id": task_id,
                "name": job.name,
                "next_run_time": job.next_run_time,
                "trigger": str(job.trigger)
            })
        return result


# Global scheduler instance
scheduler = TaskScheduler()