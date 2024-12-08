import factory

from database.models import User


class UserFactory(factory.Factory):
    class Meta:
        model = User

    tg_id = factory.Faker("pyint")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    username = factory.Faker("pystr")
    language_code = factory.Faker("locale")
