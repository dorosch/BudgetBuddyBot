from random import randint, choices
from string import ascii_lowercase, digits
from typing import Optional

from pymongo import IndexModel, ASCENDING
from beanie import Document
from pymongo.errors import DuplicateKeyError


class Invite(Document):
    tg_id: int
    code: Optional[str] = None

    class Settings:
        indexes = [
            IndexModel(
                [
                    ("tg_id", ASCENDING),
                    ("code", ASCENDING),
                ],
                unique=True,
            )
        ]

    async def get_or_create_code(self) -> str:
        if invite := await Invite.find(Invite.tg_id == self.tg_id).first_or_none():
            return invite.code

        while code := "".join(choices(ascii_lowercase + digits, k=randint(8, 12))):
            invite = Invite(tg_id=self.tg_id, code=code)

            try:
                await invite.create()
            except DuplicateKeyError:
                continue
            else:
                return invite.code
