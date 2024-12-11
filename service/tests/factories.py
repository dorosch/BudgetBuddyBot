import factory

from database.models import Invite, User
from bank_providers import swedbank, revolut


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
