import logging

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from config import settings
from database.models import MODELS

logger = logging.getLogger(__name__)


async def init():
    logger.info("Database initialization")

    client = AsyncIOMotorClient(settings.MONGODB_URI, authSource="admin")

    await init_beanie(database=client.get_default_database(), document_models=MODELS)


async def drop():
    logger.info("Database drop")

    client = AsyncIOMotorClient(settings.MONGODB_URI, authSource="admin")

    await client.drop_database(client.get_default_database())
