import logging
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator, Optional

import openpyxl

from database.models import Transaction
from .base import BankProvider
from .errors import UnsupportedFileType

logger = logging.getLogger(__name__)


@dataclass
class TransactionData:
    user_id: int
    name: str
    timestamp: datetime
    amount: float
    currency: str
    description: str


class Revolut(BankProvider):
    name: str = "Revolut"
    supported_extensions: tuple[str] = (".xlsx",)

    def parse_transactions(self) -> Iterator[Transaction]:
        if self.document.suffix == ".xlsx":
            return self._parse_transactions_from_csv()
        else:
            raise UnsupportedFileType()

    def _parse_transactions_from_csv(self) -> Iterator[Transaction]:
        workbook = openpyxl.load_workbook(self.document)
        rows = workbook.active.rows
        headers = [str(cell.value) for cell in next(rows)]

        for row in rows:
            data = dict(zip(headers, (cell.value for cell in row)))

            if transaction := self._build_transaction_instance(
                TransactionData(
                    user_id=self.user_id,
                    name=self.name,
                    timestamp=data["Started Date"],
                    amount=data["Amount"],
                    currency=data["Currency"],
                    description=data["Description"],
                )
            ):
                yield transaction

    @staticmethod
    def _build_transaction_instance(data: TransactionData) -> Optional[Transaction]:
        try:
            return Transaction(
                tg_id=data.user_id,
                bank=data.name,
                timestamp=data.timestamp,
                amount=math.fabs(data.amount),
                type=(
                    Transaction.Type.debit
                    if data.amount > 0
                    else Transaction.Type.credit
                ),
                currency=Transaction.Currency.parse(data.currency),
                category=None,
                account_number=None,
                description=data.description.strip(),
            )
        except Exception as error:
            logger.error("csv parse error", exc_info=error)
