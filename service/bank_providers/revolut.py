import logging
import math
from typing import Iterator

import openpyxl

from database.models import Transaction
from .base import BankProvider
from .errors import UnsupportedFileType

logger = logging.getLogger(__name__)


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

            try:
                yield Transaction(
                    tg_id=self.user_id,
                    bank=self.name,
                    timestamp=data["Started Date"],
                    amount=math.fabs(data["Amount"]),
                    type=(
                        Transaction.Type.debit
                        if data["Amount"] > 0
                        else Transaction.Type.credit
                    ),
                    currency=Transaction.Currency.parse(data["Currency"]),
                    category=None,
                    account_number=None,
                    description=data["Description"],
                )
            except Exception as error:
                logger.error("csv parse error", exc_info=error)
