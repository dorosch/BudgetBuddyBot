from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.handlers import MessageHandler

from database.models import User, Invite

router = Router()


@router.message(CommandStart(deep_link=False))
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


@router.message(CommandStart(deep_link=True))
class StartCommandHandlerWithDeepLink(StartCommandHandler):
    """Handler of the start command with deep link."""

    async def handle(self):
        await super().handle()
