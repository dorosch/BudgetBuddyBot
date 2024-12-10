from datetime import datetime
from enum import Enum
from typing import Optional, Self

from beanie import Document, TimeSeriesConfig, Granularity


class Transaction(Document):
    class Type(Enum):
        debit = "D"
        credit = "C"
        unknown = "Unk"

        @classmethod
        def parse(cls, value: str) -> Self:
            match value.upper():
                case "D":
                    return cls.debit
                case "C" | "K":
                    return cls.credit
                case _:
                    return cls.unknown

    class Currency(Enum):
        usd = "USD"
        eur = "EUR"

        @classmethod
        def parse(cls, value: str) -> Self:
            match value.upper():
                case "USD":
                    return cls.usd
                case "EUR":
                    return cls.eur
                case _:
                    raise ValueError(f"Unknown currency {value}")

    tg_id: int
    bank: str
    timestamp: datetime
    amount: float
    type: Type
    currency: Currency
    category: Optional[str] = None
    account_number: Optional[str] = None
    description: Optional[str] = None

    class Settings:
        timeseries = TimeSeriesConfig(
            time_field="timestamp",
            meta_field="category",
            granularity=Granularity.hours,
        )
