from tortoise import Tortoise
from app.config import settings
import logging

logger = logging.getLogger(__name__)


async def init_db():
    """
    Initialize database connection
    """
    await Tortoise.init(
        db_url=settings.db_url,
        modules=settings.db_modules,
        use_tz=True,
    )
    # Generate the schema
    await Tortoise.generate_schemas()
    logger.info("Database initialized")


async def close_db():
    """
    Close database connection
    """
    await Tortoise.close_connections()
    logger.info("Database connections closed")