__all__ = (
    "BANK_PROVIDERS",
    "Revolut",
    "Swedbank",
)

from typing import Type

from .base import BankProvider
from .revolut import Revolut
from .swedbank import Swedbank


BANK_PROVIDERS: dict[str, Type[BankProvider]] = {
    Revolut.name: Revolut,
    Swedbank.name: Swedbank,
}
