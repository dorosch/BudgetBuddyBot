import logging
from datetime import datetime, timedelta

from aiogram import Router, md
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.handlers import MessageHandler, CallbackQueryHandler
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from database.models import Transaction
from database.models.transaction import ReportEntry

router = Router()
logger = logging.getLogger(__name__)


class ReportCallback(CallbackData, prefix="report"):
    from_date: str
    to_date: str


@router.message(Command("report"))
class ReportCommandHandler(MessageHandler):
    """Handler of the report command."""

    async def handle(self):
        await self.event.answer(
            "Please select the period for your report 🗓",
            reply_markup=self._get_keyboard(),
        )

    @staticmethod
    def _get_keyboard() -> InlineKeyboardMarkup:
        now = datetime.now()

        # Current month
        current_month_start = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        current_month_end = now

        # Last 3 months
        last_3_months_start = (current_month_start - timedelta(days=90)).replace(day=1)
        last_3_months_end = current_month_end

        # Last 6 months
        last_6_months_start = (current_month_start - timedelta(days=180)).replace(day=1)
        last_6_months_end = current_month_end

        # Current year
        current_year_start = now.replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        current_year_end = now.replace(
            month=12, day=31, hour=23, minute=59, second=59, microsecond=999999
        )

        # Last year
        last_year_start = current_year_start.replace(year=current_year_start.year - 1)
        last_year_end = current_year_end.replace(year=current_year_end.year - 1)

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Current month",
                        callback_data=ReportCallback(
                            from_date=current_month_start.strftime("%Y-%m-%d"),
                            to_date=current_month_end.strftime("%Y-%m-%d"),
                        ).pack(),
                    ),
                    InlineKeyboardButton(
                        text="Last 3 months",
                        callback_data=ReportCallback(
                            from_date=last_3_months_start.strftime("%Y-%m-%d"),
                            to_date=last_3_months_end.strftime("%Y-%m-%d"),
                        ).pack(),
                    ),
                    InlineKeyboardButton(
                        text="Last 6 months",
                        callback_data=ReportCallback(
                            from_date=last_6_months_start.strftime("%Y-%m-%d"),
                            to_date=last_6_months_end.strftime("%Y-%m-%d"),
                        ).pack(),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="Current year",
                        callback_data=ReportCallback(
                            from_date=current_year_start.strftime("%Y-%m-%d"),
                            to_date=current_year_end.strftime("%Y-%m-%d"),
                        ).pack(),
                    ),
                    InlineKeyboardButton(
                        text="Last year",
                        callback_data=ReportCallback(
                            from_date=last_year_start.strftime("%Y-%m-%d"),
                            to_date=last_year_end.strftime("%Y-%m-%d"),
                        ).pack(),
                    ),
                ],
            ]
        )


@router.callback_query(ReportCallback.filter())
class ReportCallbackHandler(CallbackQueryHandler):
    """Callback for selecting a specific period for the report."""

    async def handle(self):
        callback_data = ReportCallback.unpack(self.callback_data)

        try:
            from_date = datetime.strptime(callback_data.from_date, "%Y-%m-%d")
            to_date = datetime.strptime(callback_data.to_date, "%Y-%m-%d")
        except ValueError as error:
            logger.error("parse date error", exc_info=error)

            return await self.event.answer("Something get wrong")

        report = await Transaction.get_report(self.from_user.id, from_date, to_date)

        await self.bot.send_message(
            chat_id=self.event.message.chat.id,
            text=(
                "Here is your financial report from "
                f"_{md.quote(callback_data.from_date)}_ to _{md.quote(callback_data.to_date)}_:"
                "\n\n"
                f"**Income** {md.quote(self._total_amount(report.income))}\n"
                f"{md.quote(self._build_report(report.income))}"
                "\n"
                f"**Expenses** {md.quote(self._total_amount(report.expenses))}\n"
                f"{md.quote(self._build_report(report.expenses))}"
            ),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        await self.event.answer()

    @staticmethod
    def _build_report(entry: ReportEntry) -> str:
        max_length = max(
            len(category)
            for currency, categories in entry.items()
            for category, amount in categories.items()
        )

        return (
            "".join(
                f"🔹 {category.ljust(max_length)} : {amount:.2f} {currency}\n"
                for currency, categories in entry.items()
                for category, amount in categories.items()
            )
            or "No data available"
        )

    @staticmethod
    def _total_amount(entry: ReportEntry) -> str:
        results = [
            f"{sum(categories.values()):.2f} {currency}"
            for currency, categories in entry.items()
        ]

        match len(results):
            case 1:
                return results.pop()
            case 2:
                first, last = results
                return f"{first} and {last}"
            case _:
                *items, last = results
                return f"{', '.join(items)} and {last}"
