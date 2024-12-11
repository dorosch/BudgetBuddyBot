from datetime import datetime

from aiogram import Router, md
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.handlers import MessageHandler

from database.models import Transaction

router = Router()


@router.message(Command("analytics"))
class AnalyticsCommandHandler(MessageHandler):
    """Handler of the analytics command."""

    async def handle(self):
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1)

        analytics = await Transaction.get_income_and_expenses(
            self.from_user.id, start_of_month, now
        )

        incomes = (
            "".join(
                f"🔹 {amount} {currency}\n"
                for currency, amount in analytics.income.items()
            )
            or "No data available"
        )
        expenses = (
            "".join(
                f"🔹 {amount} {currency}\n"
                for currency, amount in analytics.expenses.items()
            )
            or "No data available"
        )

        await self.event.answer(
            (
                "Here is your financial report from "
                f"_{md.quote(start_of_month.strftime('%Y-%m-%d'))}_ to _{md.quote(now.strftime('%Y-%m-%d'))}_:"
                "\n\n"
                "**Income**:\n"
                f"{md.quote(incomes)}"
                "\n"
                "**Expenses**:\n"
                f"{md.quote(expenses)}"
            ),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
