from fastapi import FastAPI
from app.db.database import init_db, close_db
from app.scheduler.scheduler import scheduler
from app.models.task import Task
import logging

logger = logging.getLogger(__name__)


async def startup_event():
    """
    Application startup event handler
    """
    # Initialize database
    await init_db()

    # Start scheduler
    await scheduler.start()

    # Load all enabled tasks into scheduler
    enabled_tasks = await Task.filter(enabled=True).all()
    for task in enabled_tasks:
        await scheduler.add_task(task)
        logger.info(f"Loaded task {task.id} ({task.name}) into scheduler")

    logger.info("Application startup complete")


async def shutdown_event():
    """
    Application shutdown event handler
    """
    # Stop scheduler
    await scheduler.stop()

    # Close database connections
    await close_db()

    logger.info("Application shutdown complete")