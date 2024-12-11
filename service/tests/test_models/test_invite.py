import pytest

from database.models import Invite


class TestInviteModel:
    def test_generate_code(self):
        code = Invite.generate_code()

        assert isinstance(code, str) and 8 <= len(code) <= 12

    @pytest.mark.asyncio
    async def test_get_or_create_code_creates_new_code(self, invite):
        code = await invite.get_or_create_code()

        assert code is not None and isinstance(code, str)
        assert (await Invite.find_one(Invite.tg_id == invite.tg_id)).code == code

    @pytest.mark.asyncio
    async def test_get_or_create_code_returns_existing_code(self, invite):
        invite = await invite.create()

        assert await invite.get_or_create_code() == invite.code
