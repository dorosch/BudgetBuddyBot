from typing import Optional

from beanie import Document, Indexed
from beanie.odm.operators.update.general import Set


class User(Document):
    tg_id: Indexed(int, unique=True)
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    accepted_invite_code: Optional[str] = None

    async def insert_or_update(self) -> "User":
        await User.find_one(User.tg_id == self.tg_id).upsert(
            Set(
                {
                    User.first_name: self.first_name,
                    User.last_name: self.last_name,
                    User.username: self.username,
                    User.language_code: self.language_code,
                }
            ),
            on_insert=User(
                tg_id=self.tg_id,
                first_name=self.first_name,
                last_name=self.last_name,
                username=self.username,
                language_code=self.language_code,
            ),
        )

        return self
