import pytest

from database.models import Transaction


class TestTransactionModel:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("D", Transaction.Type.debit),
            ("C", Transaction.Type.credit),
            ("K", Transaction.Type.credit),
            ("d", Transaction.Type.debit),
            ("UNK", Transaction.Type.unknown),
            ("unknown", Transaction.Type.unknown),
            ("X", Transaction.Type.unknown),
        ],
    )
    def test_transaction_type_parse(self, value, expected):
        assert Transaction.Type.parse(value) == expected

    @pytest.mark.parametrize(
        "value, expected",
        [
            ("USD", Transaction.Currency.usd),
            ("EUR", Transaction.Currency.eur),
            ("usd", Transaction.Currency.usd),
            ("eur", Transaction.Currency.eur),
        ],
    )
    def test_transaction_currency_parse(self, value, expected):
        assert Transaction.Currency.parse(value) == expected
