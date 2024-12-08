import asyncio
import logging.config

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramRetryAfter
from aiogram.filters import CommandStart
from aiogram.handlers import MessageHandler

from config import settings
from database import core as database
from database.models import User

logging.config.dictConfig(settings.LOGGING_CONFIG)
logger = logging.getLogger(__name__)

dispatcher = Dispatcher()


@dispatcher.message(CommandStart())
class StartCommandHandler(MessageHandler):
    """Handler of the start command."""

    async def handle(self):
        await User(
            tg_id=self.from_user.id,
            first_name=self.from_user.first_name,
            last_name=self.from_user.last_name,
            username=self.from_user.username,
            language_code=self.from_user.language_code
        ).insert_or_update()

        await self.event.answer("Start")


async def main():
    await database.init()

    bot = Bot(token=settings.TOKEN)

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
