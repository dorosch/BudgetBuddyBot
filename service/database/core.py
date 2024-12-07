import logging

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from config import settings
from database.models import User

logger = logging.getLogger(__name__)


async def init():
    logger.info("Database initialization")

    models = (
        User,
    )

    client = AsyncIOMotorClient(settings.MONGODB_URI, authSource="admin")

    await init_beanie(database=client.get_default_database(), document_models=models)
