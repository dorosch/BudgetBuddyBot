from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Self

from beanie import Document, TimeSeriesConfig, Granularity


@dataclass
class Report:
    income: dict["Transaction.Currency":float]
    expenses: dict["Transaction.Currency":float]


class Transaction(Document):
    class Type(Enum):
        debit = "D"
        credit = "C"
        unknown = "Unk"

        def __str__(self) -> str:
            return self.value

        @classmethod
        def parse(cls, value: str) -> Self:
            match value.strip().upper():
                case "D":
                    return cls.debit
                case "C" | "K":
                    return cls.credit
                case _:
                    return cls.unknown

    class Currency(Enum):
        usd = "USD"
        eur = "EUR"

        def __str__(self) -> str:
            return self.value

        @classmethod
        def parse(cls, value: str) -> Self:
            match value.strip().upper():
                case "USD":
                    return cls.usd
                case "EUR":
                    return cls.eur
                case _:
                    raise ValueError(f"Unknown currency {value}")

    class Category(str, Enum):
        INCOME = "Income"
        HOUSING = "Housing"
        TRANSPORT = "Transport"
        CHILDREN = "Children"
        BEAUTY = "Beauty"
        HEALTH = "Health"
        MISC = "Miscellaneous"
        GAMES = "Games"
        SHOPPING = "Shopping"
        SERVICES = "Services"
        EDUCATION = "Education"
        TRAVEL = "Travel"
        PETS = "Pets"
        UNCATEGORIZED = "Uncategorized"
        FOOD = "Food"
        SPORT = "Sport"

    tg_id: int
    bank: str
    timestamp: datetime
    amount: float
    type: Type
    currency: Currency
    category: Optional[Category] = None
    account_number: Optional[str] = None
    description: Optional[str] = None

    @classmethod
    async def get_income_and_expenses(
        cls, tg_id: int, start_date: datetime, end_date: datetime
    ) -> "Report":
        result = await cls.aggregate(
            [
                {
                    "$match": {
                        "tg_id": tg_id,
                        "timestamp": {
                            "$gte": start_date,
                            "$lte": end_date,
                        },
                    }
                },
                {
                    "$group": {
                        "_id": {"type": "$type", "currency": "$currency"},
                        "total_amount": {"$sum": "$amount"},
                    }
                },
            ]
        ).to_list()

        income = defaultdict(float)
        expenses = defaultdict(float)

        for entry in result:
            operation = cls.Type.parse(entry["_id"]["type"])
            currency = cls.Currency.parse(entry["_id"]["currency"])

            if operation == cls.Type.credit:
                income[currency] += entry["total_amount"]
            elif operation == cls.Type.debit:
                expenses[currency] += entry["total_amount"]

        return Report(income=dict(income), expenses=dict(expenses))
