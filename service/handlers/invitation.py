from aiogram import Router
from aiogram.utils.deep_linking import create_start_link
from aiogram.filters import Command
from aiogram.handlers import MessageHandler
from aiogram.utils.chat_action import ChatActionSender

from database.models import Invite

router = Router()


@router.message(Command("create_invitation"))
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
