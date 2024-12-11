import re

import pytest_asyncio
from pytest_factoryboy import register

from database.core import init as database_init, drop as database_drop
from config import settings
from .factories import (
    MessageFactory,
    InviteFactory,
    UserFactory,
    TelegramUserFactory,
    RevolutTransactionDataFactory,
    SwedbankTransactionDataFactory,
)


register(MessageFactory)
register(InviteFactory)
register(UserFactory)
register(TelegramUserFactory)
register(RevolutTransactionDataFactory)
register(SwedbankTransactionDataFactory)


@pytest_asyncio.fixture(loop_scope="function", autouse=True)
async def init(database_for_tests="tests"):
    settings.MONGODB_URI = re.sub(
        r"/\w*$", f"/{database_for_tests}", settings.MONGODB_URI
    )

    await database_init()

    yield

    await database_drop()
