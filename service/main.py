import asyncio
import logging.config

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramRetryAfter
from aiogram.fsm.storage.mongo import MongoStorage
from aiogram.types import BotCommand
from motor.motor_asyncio import AsyncIOMotorClient

from handlers import (
    analytics as analytics_handler,
    report as report_handler,
    help as help_handler,
    invite as invitation_helper,
    start as start_handler,
    upload as upload_handler,
)
from config import settings
from database import core as database

logging.config.dictConfig(settings.LOGGING_CONFIG)
logger = logging.getLogger(__name__)


async def main():
    await database.init()

    bot = Bot(token=settings.TOKEN)

    dispatcher = Dispatcher(
        bot=bot,
        storage=MongoStorage(
            AsyncIOMotorClient(settings.MONGODB_URI, authSource="admin")
        ),
    )

    dispatcher.include_router(analytics_handler.router)
    dispatcher.include_router(report_handler.router)
    dispatcher.include_router(help_handler.router)
    dispatcher.include_router(invitation_helper.router)
    dispatcher.include_router(start_handler.router)
    dispatcher.include_router(upload_handler.router)

    await bot.set_my_commands(
        [
            BotCommand(command="/help", description="Information about the bot"),
            BotCommand(
                command="/report",
                description="Report of your income and expenses",
            ),
            BotCommand(
                command="/analytics",
                description="Analytics of your expenses and income",
            ),
            BotCommand(command="/upload", description="Upload your account statement"),
            BotCommand(
                command="/invite",
                description="Invite someone to share a budget",
            ),
        ]
    )

    try:
        await dispatcher.start_polling(bot)
    finally:
        try:
            await bot.close()
        except TelegramRetryAfter as error:
            # There except needed because if you call bot.close()
            # to many telegram will block your calls for 10 minutes
            logger.error(error)


if __name__ == "__main__":
    logger.info("Application start")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped")
