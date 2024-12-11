import re

import pytest_asyncio
from pytest_factoryboy import register

from database.core import init as database_init
from config import settings
from .factories import (
    InviteFactory,
    UserFactory,
    RevolutTransactionDataFactory,
    SwedbankTransactionDataFactory,
)


register(InviteFactory)
register(UserFactory)
register(RevolutTransactionDataFactory)
register(SwedbankTransactionDataFactory)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def init():
    settings.MONGODB_URI = re.sub(r"/\w*$", "/tests", settings.MONGODB_URI)

    await database_init()
