from typing import Optional

from beanie import Document, Indexed


class User(Document):
    tg_id: Indexed(str, unique=True)
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
