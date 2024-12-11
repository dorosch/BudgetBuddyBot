import pytest
from faker import Faker

from database.models import User


@pytest.mark.asyncio
class TestUserModel:
    async def test_insert_or_update(self, user):
        updated_username = Faker().user_name()
        user.username = updated_username

        await user.insert_or_update()

        assert (
            await User.find(
                User.tg_id == user.tg_id, User.username == updated_username
            ).first_or_none()
            is not None
        )
