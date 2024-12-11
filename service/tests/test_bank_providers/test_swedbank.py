from bank_providers import BANK_PROVIDERS, Swedbank


class TestSwedbank:
    def test_provider_available(self):
        assert Swedbank.name in BANK_PROVIDERS.keys()

    def test_supported_extensions(self):
        assert Swedbank.supported_extensions == (".csv",)

    def test_build_transaction_instance(self, swedbank_transaction_data):
        assert Swedbank._build_transaction_instance(swedbank_transaction_data)
