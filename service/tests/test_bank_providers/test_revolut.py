from bank_providers import BANK_PROVIDERS, Revolut


class TestRevolut:
    def test_provider_available(self):
        assert Revolut.name in BANK_PROVIDERS.keys()

    def test_supported_extensions(self):
        assert Revolut.supported_extensions == (".xlsx",)

    def test_build_transaction_instance(self, revolut_transaction_data):
        assert Revolut._build_transaction_instance(revolut_transaction_data)
