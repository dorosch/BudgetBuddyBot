import asyncio
import logging.config
from datetime import UTC, datetime
from pathlib import Path
from itertools import batched

from aiogram import Bot, Dispatcher, F, md
from aiogram.utils.deep_linking import create_start_link
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramRetryAfter
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.mongo import MongoStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.handlers import MessageHandler
from aiogram.types import (
    BotCommand,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
)
from aiogram.utils.chat_action import ChatActionSender
from motor.motor_asyncio import AsyncIOMotorClient
from aiogram.enums.content_type import ContentType

from config import settings
from bank_providers import BANK_PROVIDERS
from bank_providers.errors import UnsupportedFileType
from database import core as database
from database.models import User, Transaction, Invite

logging.config.dictConfig(settings.LOGGING_CONFIG)
logger = logging.getLogger(__name__)

dispatcher = Dispatcher(
    storage=MongoStorage(AsyncIOMotorClient(settings.MONGODB_URI, authSource="admin"))
)

MENU_COMMANDS = [
    BotCommand(command="/help", description="Information about the bot"),
    BotCommand(command="/upload", description="Upload your account statement"),
    BotCommand(
        command="/create_invitation", description="Invite someone to share a budget"
    ),
]


class UploadBankStatement(StatesGroup):
    selected_bank = State()
    uploaded_file = State()


@dispatcher.message(CommandStart(deep_link=False))
class StartCommandHandler(MessageHandler):
    """Handler of the start command without deep link."""

    async def handle(self):
        invitation_code = self.data["command"].args

        await User(
            tg_id=self.from_user.id,
            first_name=self.from_user.first_name,
            last_name=self.from_user.last_name,
            username=self.from_user.username,
            language_code=self.from_user.language_code,
            accepted_invite_code=invitation_code,
        ).insert_or_update()

        await self.event.answer(
            "Welcome to BudgetBuddy\\! 💰\n"
            "Your personal assistant for tracking expenses and income\n"
            "\n"
            "🔹 Easily monitor your finances:\n"
            "  Track your spending, manage your income, and gain insights into your financial\n"
            "\n"
            "🔹 Simple and intuitive:\n"
            "  Upload bank statements or enter transactions manually, BudgetBuddy will do the rest\n"
            "\n"
            "🔹 Get started:\n"
            "  Just type /help to see all available commands and learn how to use the bot\n"
            "\n"
            "Let’s take control of your budget together\\! 🚀",
            parse_mode=ParseMode.MARKDOWN_V2,
        )

        if invitation_code is not None:
            invite = await Invite.find_one(Invite.code == invitation_code)

            if not invite:
                return

            user = await User.find_one(User.tg_id == invite.tg_id)

            await self.event.answer(
                f"Also you have been invited by _{user.first_name} {user.last_name}_ "
                "and now you can see the shared budget",
                parse_mode=ParseMode.MARKDOWN_V2,
            )


@dispatcher.message(CommandStart(deep_link=True))
class StartCommandHandlerWithDeepLink(StartCommandHandler):
    """Handler of the start command with deep link."""

    async def handle(self):
        await super().handle()


@dispatcher.message(Command("help"))
class HelpCommandHandler(MessageHandler):
    """Handler of the help command."""

    async def handle(self):
        await self.event.answer(
            "BudgetBuddy Help Menu 📖\n"
            "\n"
            "🔹 /help \\- see the current message with command hints\n"
            "\n"
            "🔹 /upload \\- Upload your bank statement to start tracking your expenses and incomes\\. "
            f"{self._get_supported_banks()}"
            "\n"
            "🔹 /create_invitation \\ - Invite another person to manage a joint budget",
            parse_mode=ParseMode.MARKDOWN_V2,
        )

    @staticmethod
    def _get_supported_banks() -> str:
        match len(BANK_PROVIDERS):
            case 0:
                return "We do not support any banks yet\\."
            case 1:
                bank, *_ = BANK_PROVIDERS.keys()
                return f"We support {bank}\\."
            case 2:
                bank_a, bank_b = BANK_PROVIDERS.keys()
                return f"We support {bank_a} and {bank_b}\\."
            case _:
                others, bank = BANK_PROVIDERS.keys()
                return f"We support {', '.join(others)} and {bank}\\."


@dispatcher.message(Command("create_invitation"))
class InvitationCommandHandler(MessageHandler):
    """Handler of the invitation command."""

    async def handle(self):
        async with ChatActionSender.typing(bot=self.bot, chat_id=self.event.chat.id):
            code = await Invite(tg_id=self.from_user.id).get_or_create_code()
            link = await create_start_link(self.bot, code)

        await self.event.answer(
            "Here is your link, share it to invite someone to a joint budget"
        )
        await self.event.answer(link)


@dispatcher.message(Command("upload"))
class UploadHandler(MessageHandler):
    """Handler of the upload command."""

    reply_markup = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=provider_name)
                for provider_name in BANK_PROVIDERS.keys()
            ]
        ],
        resize_keyboard=True,
    )

    async def handle(self):
        await self.event.answer(
            "Please select your bank from the list below",
            reply_markup=self.reply_markup,
        )

        await self.data["state"].set_state(UploadBankStatement.selected_bank)


@dispatcher.message(
    UploadBankStatement.selected_bank, F.text.in_(BANK_PROVIDERS.keys())
)
class SelectBankHandler(MessageHandler):
    async def handle(self):
        bank = self.event.text
        state = self.data["state"]

        await state.update_data(selected_bank=bank)
        await state.set_state(UploadBankStatement.uploaded_file)

        await self.event.answer(
            "Please upload your bank statement file\\. "
            f"{self._get_supported_formats(bank)}",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=ReplyKeyboardRemove(),
        )

    def _get_supported_formats(self, bank: str) -> str:
        formats = BANK_PROVIDERS[bank].supported_extensions

        match len(formats):
            case 0:
                return (
                    f"We do not currently support any bank statement format from {bank}"
                )
            case 1:
                format, *_ = formats
                return f"We support format _{md.quote(format)}_"
            case 2:
                format_a, format_b = formats
                return f"We support formats _{md.quote(format_a)}_ and _{md.quote(format_b)}_"
            case _:
                others, format = BANK_PROVIDERS.keys()
                others = [f"_{md.quote(other)}_" for other in others]
                return f"We support {', '.join(others)} and {bank}\\."


@dispatcher.message(
    UploadBankStatement.uploaded_file, F.content_type == ContentType.DOCUMENT
)
class UploadBankStatementDocumentHandler(MessageHandler):
    async def handle(self):
        state = self.data["state"]
        data = await state.get_data()
        selected_bank = data["selected_bank"]
        bank_provider = BANK_PROVIDERS[selected_bank]
        document_path = self._get_download_destination(selected_bank)

        async with ChatActionSender.typing(bot=self.bot, chat_id=self.event.chat.id):
            await self.bot.download(
                self.event.document.file_id, destination=document_path
            )
            await state.update_data(uploaded_file=str(document_path))

            try:
                amount = 0

                for batch in batched(
                    bank_provider(self.from_user.id, document_path).parse(), 256
                ):
                    amount += len(batch)
                    await Transaction.insert_many(batch)
            except UnsupportedFileType as error:
                await self.event.answer(str(error))
            else:
                await state.clear()

                # Remove uploaded document from a disk
                document_path.unlink(missing_ok=True)

                if amount > 0:
                    await self.event.answer(
                        f"{amount} transactions were processed and saved"
                    )
                else:
                    await self.event.answer(
                        "There are no valid transactions in the file"
                    )

    def _get_download_destination(self, selected_bank: str) -> Path:
        return settings.DOCUMENT_STORAGE_PATH / "_".join(
            (
                str(self.from_user.id),
                selected_bank,
                str(datetime.now(UTC)),
                self.event.document.file_name,
            )
        )


async def main():
    await database.init()

    bot = Bot(token=settings.TOKEN)
    await bot.set_my_commands(MENU_COMMANDS)

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
