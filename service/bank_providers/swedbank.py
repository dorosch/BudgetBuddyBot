import logging
from datetime import datetime
from typing import Iterator

from .base import BankProvider
from .errors import UnsupportedFileType
from database.models.transaction import Transaction

logger = logging.getLogger(__name__)


class Swedbank(BankProvider):
    name: str = "Swedbank"
    supported_extensions: tuple[str] = (".csv",)

    def parse_transactions(self) -> Iterator[Transaction]:
        if self.document.suffix == ".csv":
            return self._parse_transactions_from_csv()
        else:
            raise UnsupportedFileType()

    def _parse_transactions_from_csv(self) -> Iterator[Transaction]:
        with open(self.document) as file:
            # Skip line with headers
            _ = file.readline()

            # Here need to use strange logic how to get the value of the column
            # whose header is empty, since the csv reader skips such a value
            for line in file:
                if not line:
                    continue

                try:
                    (
                        account_number,
                        code,
                        date,
                        _,
                        description,
                        amount,
                        currency,
                        operation_type,
                        *_,
                    ) = (item.replace('"', "") for item in line.strip().split(","))
                except ValueError as error:
                    logger.error("csv split line error", exc_info=error)

                    continue

                # need to skip transactions made by non-user
                if code != "20":
                    continue

                try:
                    yield Transaction(
                        tg_id=self.user_id,
                        bank=self.name,
                        timestamp=datetime.strptime(date, "%Y-%m-%d"),
                        amount=float(amount),
                        type=Transaction.Type.parse(operation_type),
                        currency=Transaction.Currency.parse(currency),
                        category=None,
                        account_number=account_number,
                        description=description,
                    )
                except Exception as error:
                    logger.error("csv parse error", exc_info=error)
