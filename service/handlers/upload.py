from datetime import UTC, datetime
from pathlib import Path
from itertools import batched

from aiogram import Router, F, md
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.handlers import MessageHandler
from aiogram.types import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
)
from aiogram.utils.chat_action import ChatActionSender
from aiogram.enums.content_type import ContentType

from config import settings
from bank_providers import BANK_PROVIDERS
from bank_providers.errors import UnsupportedFileType
from database.models import Transaction

router = Router()


class UploadBankStatement(StatesGroup):
    selected_bank = State()
    uploaded_file = State()


@router.message(Command("upload"))
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


@router.message(
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


@router.message(
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
