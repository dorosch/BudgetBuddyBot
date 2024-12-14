import asyncio
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Self, TypeAlias

from beanie import Document


ReportEntry: TypeAlias = dict[
    "Transaction.Currency", dict["Transaction.Category", float]
]


@dataclass
class Report:
    income: ReportEntry
    expenses: ReportEntry


@dataclass
class Analytics:
    original_period: Report
    compared_period: Report


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
            try:
                return cls(value.upper())
            except ValueError as error:
                raise ValueError(f"Unknown currency {value}") from error

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
        UNKNOWN = "Unknown"
        FOOD = "Food"
        SPORT = "Sport"

        def __str__(self) -> str:
            return self.value

        @classmethod
        def parse(cls, value: str) -> Self:
            try:
                return cls(value.lower().capitalize())
            except ValueError as error:
                raise ValueError(f"Unknown category {value}") from error

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
    async def get_report(
        cls, tg_id: int, start_date: datetime, end_date: datetime
    ) -> Report:
        result = await cls.aggregate(
            [
                {
                    "$match": {
                        "tg_id": tg_id,
                        "timestamp": {"$gte": start_date, "$lte": end_date},
                    }
                },
                {
                    "$addFields": {
                        "category": {
                            "$ifNull": ["$category", str(cls.Category.UNKNOWN)]
                        }
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "category": "$category",
                            "type": "$type",
                            "currency": "$currency",
                        },
                        "total_amount": {"$sum": "$amount"},
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "type": "$_id.type",
                            "currency": "$_id.currency",
                        },
                        "categories": {
                            "$push": {
                                "category": "$_id.category",
                                "total_amount": "$total_amount",
                            }
                        },
                    }
                },
            ]
        ).to_list()

        income = defaultdict(lambda: defaultdict(float))
        expenses = defaultdict(lambda: defaultdict(float))

        for record in result:
            operation = cls.Type.parse(record["_id"]["type"])
            currency = cls.Currency.parse(record["_id"]["currency"])

            for category_record in record["categories"]:
                amount = category_record["total_amount"]
                category = Transaction.Category.parse(category_record["category"])

                if operation == cls.Type.credit:
                    income[currency][category] += amount
                elif operation == cls.Type.debit:
                    expenses[currency][category] += amount

        return Report(income=dict(income), expenses=dict(expenses))

    @classmethod
    async def get_analytics(
        cls,
        tg_id: int,
        original: tuple[datetime, datetime],
        compared: tuple[datetime, datetime],
    ) -> Analytics:
        original_period_start, original_period_end = original
        compared_period_start, compared_period_end = compared

        assert original_period_start < original_period_end
        assert compared_period_start < compared_period_end
        assert compared_period_end <= original_period_start

        original_period, compared_period = await asyncio.gather(
            cls.get_report(
                tg_id=tg_id,
                start_date=original_period_start,
                end_date=original_period_end,
            ),
            cls.get_report(
                tg_id=tg_id,
                start_date=compared_period_start,
                end_date=compared_period_end,
            ),
        )

        return Analytics(
            original_period=original_period, compared_period=compared_period
        )
