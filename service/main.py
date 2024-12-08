import asyncio
import logging.config

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramRetryAfter
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.mongo import MongoStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.handlers import MessageHandler
from aiogram.types import BotCommand, ReplyKeyboardMarkup, KeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient

from config import settings
from database import core as database
from database.models import User

logging.config.dictConfig(settings.LOGGING_CONFIG)
logger = logging.getLogger(__name__)

dispatcher = Dispatcher(
    storage=MongoStorage(
        AsyncIOMotorClient(settings.MONGODB_URI, authSource="admin")
    )
)

MENU_COMMANDS = [
    BotCommand(command="/help", description="Information about the bot"),
    BotCommand(command="/upload", description="Upload your account statement"),
]


class UploadBankAccountStatement(StatesGroup):
    selected_bank = State()
    uploaded_file = State()


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


@dispatcher.message(Command("upload"))
class UploadBankAccountStatementHandler(MessageHandler):
    """Handler of the upload command."""

    reply_markup = ReplyKeyboardMarkup(keyboard=[
        [
            KeyboardButton(text="Swedbank", callback_data="Swedbank"),
            KeyboardButton(text="Revolut", callback_data="Revolut"),
        ]
    ])

    async def handle(self):
        await self.event.answer(
            "Please choose your bank",
            reply_markup=self.reply_markup
        )

        await self.data["state"].set_state(
            UploadBankAccountStatement.selected_bank
        )


async def main():
    await database.init()

    bot = Bot(token=settings.TOKEN)

    try:
        await bot.set_my_commands(MENU_COMMANDS)
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
