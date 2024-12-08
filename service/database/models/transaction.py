from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document, Link, TimeSeriesConfig, Granularity

from database.models import User


class Transaction(Document):
    class Type(Enum):
        debit = "D"
        credit = "C"
        unknown = "Unk"

    class Currency(Enum):
        usd = "USD"
        eur = "EUR"

    user: Link[User]
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

    class Config:
        indexes = [
            {"fields": ["user", "timestamp", "amount"], "unique": True}
        ]
