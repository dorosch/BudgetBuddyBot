from typing import Optional

import factory
from dataclasses import dataclass, field

from database.models import Invite, User
from bank_providers import swedbank, revolut


@dataclass
class TelegramUser:
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None


@dataclass
class Message:
    from_user: TelegramUser
    answers: list[str] = field(default_factory=list)

    async def answer(self, text: str, *args, **kwargs):
        self.answers.append(text)


class InviteFactory(factory.Factory):
    class Meta:
        model = Invite

    tg_id = factory.Faker("pyint")
    code = factory.LazyFunction(lambda: Invite.generate_code())


class UserFactory(factory.Factory):
    class Meta:
        model = User

    tg_id = factory.Faker("pyint")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    username = factory.Faker("pystr")
    language_code = factory.Faker("locale")


class TelegramUserFactory(factory.Factory):
    class Meta:
        model = TelegramUser

    id = factory.Faker("pyint")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    username = factory.Faker("pystr")
    language_code = factory.Faker("locale")


class MessageFactory(factory.Factory):
    class Meta:
        model = Message

    from_user = factory.SubFactory(TelegramUserFactory)


class RevolutTransactionDataFactory(factory.Factory):
    class Meta:
        model = revolut.TransactionData

    user_id = factory.Faker("pyint")
    name = factory.Faker("name")
    timestamp = factory.Faker("date")
    amount = factory.Faker("pyfloat", positive=True)
    currency = factory.Faker("random_element", elements=["EUR", "USD"])
    description = factory.Faker("sentence", nb_words=5)


class SwedbankTransactionDataFactory(factory.Factory):
    class Meta:
        model = swedbank.TransactionData

    user_id = factory.Faker("pyint")
    name = factory.Faker("name")
    timestamp = factory.Faker("date")
    amount = factory.Faker("pyfloat", positive=True)
    type = factory.Faker("random_element", elements=["D", "C", "K"])
    currency = factory.Faker("random_element", elements=["EUR", "USD"])
    account_number = factory.Faker("iban")
    description = factory.Faker("sentence", nb_words=5)
