import pytest


@pytest.fixture(scope="function")
def swedbank_transaction_data(swedbank_transaction_data_factory):
    return swedbank_transaction_data_factory()


@pytest.fixture(scope="function")
def revolut_transaction_data(revolut_transaction_data_factory):
    return revolut_transaction_data_factory()
