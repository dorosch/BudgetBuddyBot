import asyncio
import logging.config
import os

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramRetryAfter
from aiogram.filters import CommandStart
from aiogram.handlers import MessageHandler

from config import settings
from database import core as database

logging.config.dictConfig(settings.LOGGING_CONFIG)
logger = logging.getLogger(__name__)

dispatcher = Dispatcher()


@dispatcher.message(CommandStart())
class StartCommandHandler(MessageHandler):
    """Handler of the start command."""

    async def handle(self):
        await self.event.answer("Start")


async def main():
    await database.init()

    bot = Bot(token=os.environ["TOKEN"])

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
