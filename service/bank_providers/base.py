from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator

from .errors import UnsupportedFileType
from database.models.transaction import Transaction


class BankProvider(ABC):
    name: str = None
    supported_extensions: tuple[str] = None

    def __init__(self, user_id: int, document_path: Path):
        self.user_id = user_id
        self.document = document_path

    def parse(self) -> Iterator[Transaction]:
        if self.document.suffix not in self.supported_extensions:
            raise UnsupportedFileType(
                f"{self.name} doesn't support {self.document.suffix} files"
            )

        return self.parse_transactions()

    @abstractmethod
    def parse_transactions(self) -> Iterator[Transaction]: ...
