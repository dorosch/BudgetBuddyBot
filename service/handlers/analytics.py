import logging
from datetime import datetime, timedelta

from aiogram import Router, md
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.handlers import MessageHandler, CallbackQueryHandler
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.markdown import bold, italic

from database.models import Transaction
from database.models.transaction import ReportEntry, Analytics

router = Router()
logger = logging.getLogger(__name__)


class AnalyticsCallback(CallbackData, prefix="analytics"):
    original_from_date: str
    original_to_date: str
    compared_from_date: str
    compared_to_date: str


@router.message(Command("analytics"))
class AnalyticsCommandHandler(MessageHandler):
    """Handler of the analytics command."""

    async def handle(self):
        await self.event.answer(
            (
                "Please select the period for your analytics 💰\n"
                "The selected period will be compared with the same period before"
            ),
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
        compared_current_month_start = (
            current_month_start - timedelta(days=30)
        ).replace(day=1)
        compared_current_month_end = current_month_start

        # Last 3 months
        last_3_months_start = (current_month_start - timedelta(days=90)).replace(day=1)
        last_3_months_end = current_month_end
        compared_last_3_months_start = (
            last_3_months_start - timedelta(days=90)
        ).replace(day=1)
        compared_last_3_months_end = last_3_months_start

        # Last 6 months
        last_6_months_start = (current_month_start - timedelta(days=180)).replace(day=1)
        last_6_months_end = current_month_end
        compared_last_6_months_start = (
            last_6_months_start - timedelta(days=180)
        ).replace(day=1)
        compared_last_6_months_end = last_6_months_start

        # Current year
        current_year_start = now.replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        current_year_end = now.replace(
            month=12, day=31, hour=23, minute=59, second=59, microsecond=999999
        )
        compared_current_year_start = current_year_start.replace(
            year=current_year_start.year - 1
        )
        compared_current_year_end = current_year_start

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Current month",
                        callback_data=AnalyticsCallback(
                            original_from_date=current_month_start.strftime("%Y-%m-%d"),
                            original_to_date=current_month_end.strftime("%Y-%m-%d"),
                            compared_from_date=compared_current_month_start.strftime(
                                "%Y-%m-%d"
                            ),
                            compared_to_date=compared_current_month_end.strftime(
                                "%Y-%m-%d"
                            ),
                        ).pack(),
                    ),
                    InlineKeyboardButton(
                        text="Last 3 months",
                        callback_data=AnalyticsCallback(
                            original_from_date=last_3_months_start.strftime("%Y-%m-%d"),
                            original_to_date=last_3_months_end.strftime("%Y-%m-%d"),
                            compared_from_date=compared_last_3_months_start.strftime(
                                "%Y-%m-%d"
                            ),
                            compared_to_date=compared_last_3_months_end.strftime(
                                "%Y-%m-%d"
                            ),
                        ).pack(),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="Last 6 months",
                        callback_data=AnalyticsCallback(
                            original_from_date=last_6_months_start.strftime("%Y-%m-%d"),
                            original_to_date=last_6_months_end.strftime("%Y-%m-%d"),
                            compared_from_date=compared_last_6_months_start.strftime(
                                "%Y-%m-%d"
                            ),
                            compared_to_date=compared_last_6_months_end.strftime(
                                "%Y-%m-%d"
                            ),
                        ).pack(),
                    ),
                    InlineKeyboardButton(
                        text="Current year",
                        callback_data=AnalyticsCallback(
                            original_from_date=current_year_start.strftime("%Y-%m-%d"),
                            original_to_date=current_year_end.strftime("%Y-%m-%d"),
                            compared_from_date=compared_current_year_start.strftime(
                                "%Y-%m-%d"
                            ),
                            compared_to_date=compared_current_year_end.strftime(
                                "%Y-%m-%d"
                            ),
                        ).pack(),
                    ),
                ],
            ]
        )


@router.callback_query(AnalyticsCallback.filter())
class ReportCallbackHandler(CallbackQueryHandler):
    """Callback for selecting a specific period for the report."""

    async def handle(self):
        callback_data = AnalyticsCallback.unpack(self.callback_data)

        try:
            original_from_date = datetime.strptime(
                callback_data.original_from_date, "%Y-%m-%d"
            )
            original_to_date = datetime.strptime(
                callback_data.original_to_date, "%Y-%m-%d"
            )
            compared_from_date = datetime.strptime(
                callback_data.compared_from_date, "%Y-%m-%d"
            )
            compared_to_date = datetime.strptime(
                callback_data.compared_to_date, "%Y-%m-%d"
            )
        except ValueError as error:
            logger.error("parse date error", exc_info=error)

            return await self.event.answer("Something get wrong")

        analytics = await Transaction.get_analytics(
            self.from_user.id,
            original=(original_from_date, original_to_date),
            compared=(compared_from_date, compared_to_date),
        )

        await self.bot.send_message(
            chat_id=self.event.message.chat.id,
            text=self._format_analytics(analytics),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        await self.event.answer()

    @classmethod
    def _format_analytics(cls, analytics: Analytics) -> str:
        """Formats the full analytics report, comparing two periods."""

        # Reports for income and expenses in two periods
        original_income = cls._format_report(
            analytics.original_period.income, "Income (Original Period)"
        )
        original_expenses = cls._format_report(
            analytics.original_period.expenses, "Expenses (Original Period)"
        )
        compared_income = cls._format_report(
            analytics.compared_period.income, "Income (Compared Period)"
        )
        compared_expenses = cls._format_report(
            analytics.compared_period.expenses, "Expenses (Compared Period)"
        )

        # Calculate changes in expenses by category
        changes = []

        for currency, original_categories in analytics.original_period.expenses.items():
            compared_categories = analytics.compared_period.expenses.get(currency, {})
            changes.append(f"\n💱 {bold(currency)}:")
            all_categories = set(original_categories.keys()).union(
                compared_categories.keys()
            )
            for category in all_categories:
                original_amount = original_categories.get(category, 0.0)
                compared_amount = compared_categories.get(category, 0.0)
                change = original_amount - compared_amount
                emoji = "⬆️" if change > 0 else "⬇️" if change < 0 else "⏺️"
                changes.append(
                    f" • {italic(md.quote(category))}: "
                    f"{md.quote(str(round(compared_amount, 2)))} "
                    f"\\({emoji} {md.quote(str(round(change, 2)))}\\)"
                )

        # Compile the final message
        return (
            f"{bold('📊 Analytics Report')}\n\n"
            f"{original_income}\n\n"
            f"{original_expenses}\n\n"
            f"{compared_income}\n\n"
            f"{compared_expenses}\n\n"
            f"{bold('🔄 Changes in Expenses by Category')}\n" + "\n".join(changes)
        )

    @staticmethod
    def _format_report(report: ReportEntry, title: str) -> str:
        """Formats a report for a single period."""

        result = [f"{bold(title)}\n"]

        for currency, categories in report.items():
            result.append(f"💱 {bold(currency)}:")

            for category, amount in categories.items():
                result.append(
                    f" • {italic(category)}: {md.quote(str(round(amount, 2)))}"
                )

        return "\n".join(result)
