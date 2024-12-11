import logging
from datetime import datetime
from typing import Iterator, Optional
from dataclasses import dataclass

from .base import BankProvider
from .errors import UnsupportedFileType
from database.models.transaction import Transaction

logger = logging.getLogger(__name__)


@dataclass
class TransactionData:
    user_id: int
    name: str
    timestamp: str
    amount: str
    type: str
    currency: str
    account_number: str
    description: str


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

                if transaction := self._build_transaction_instance(
                    TransactionData(
                        user_id=self.user_id,
                        name=self.name,
                        timestamp=date,
                        amount=amount,
                        type=operation_type,
                        currency=currency,
                        account_number=account_number,
                        description=description,
                    )
                ):
                    yield transaction

    @staticmethod
    def _build_transaction_instance(data: TransactionData) -> Optional[Transaction]:
        try:
            return Transaction(
                tg_id=data.user_id,
                bank=data.name,
                timestamp=datetime.strptime(data.timestamp, "%Y-%m-%d"),
                amount=float(data.amount),
                type=Transaction.Type.parse(data.type),
                currency=Transaction.Currency.parse(data.currency),
                category=None,
                account_number=data.account_number,
                description=data.description,
            )
        except Exception as error:
            logger.error("csv parse error", exc_info=error)
