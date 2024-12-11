from dataclasses import dataclass
from typing import Optional

import pytest

from database.models import User
from handlers.start import StartCommandHandler, StartCommandHandlerWithDeepLink


@dataclass
class Command:
    args: Optional[str] = None


@pytest.mark.asyncio
class TestStartCommandHandler:
    async def test_handler_send_answer(self, message):
        await StartCommandHandler(message, command=Command()).handle()

        assert len(message.answers) == 1

    async def test_handler_crate_new_user(self, message):
        await StartCommandHandler(message, command=Command()).handle()

        assert await User.find_one(User.tg_id == message.from_user.id)

    async def test_handler_with_existing_user(self, message, user):
        await user.insert()
        message.from_user.id = user.tg_id
        await StartCommandHandler(message, command=Command()).handle()

        assert await User.find_one(User.tg_id == message.from_user.id)


@pytest.mark.asyncio
class TestStartCommandHandlerWithDeepLink:
    async def test_handler_send_answer_without_invite(self, message):
        await StartCommandHandler(message, command=Command()).handle()

        assert len(message.answers) == 1

    async def test_handler_send_answer_with_invite(self, message, user, invite):
        user.tg_id = invite.tg_id
        await user.insert()
        await invite.insert()

        await StartCommandHandlerWithDeepLink(
            message, command=Command(args=invite.code)
        ).handle()

        assert len(message.answers) == 2
        assert await User.find_one(User.tg_id == message.from_user.id)
