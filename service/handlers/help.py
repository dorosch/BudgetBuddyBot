from typing import Collection

from aiogram import Router, md
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.handlers import MessageHandler

from bank_providers import BANK_PROVIDERS

router = Router()


@router.message(Command("help"))
class HelpCommandHandler(MessageHandler):
    """Handler of the help command."""

    async def handle(self):
        await self.event.answer(
            md.quote(
                "BudgetBuddy Help Menu 📖\n"
                "\n"
                "🔹 /help - see the current message with command hints"
                "\n"
                "🔹 /upload - Upload your bank statement to start tracking your expenses and incomes"
                f"{self._get_supported_banks(BANK_PROVIDERS.keys())}"
                "\n"
                "🔹 /invite - Invite another person to manage a joint budget"
            ),
            parse_mode=ParseMode.MARKDOWN_V2,
        )

    @staticmethod
    def _get_supported_banks(providers: Collection[str]) -> str:
        match len(providers):
            case 0:
                return "We do not support any banks yet."
            case 1:
                bank, *_ = providers
                return f"We support {bank}."
            case 2:
                bank_a, bank_b = providers
                return f"We support {bank_a} and {bank_b}."
            case _:
                *others, bank = providers
                return f"We support {', '.join(others)} and {bank}."
