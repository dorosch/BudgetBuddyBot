import asyncio
import logging.config
from datetime import datetime
from typing import AsyncIterator, Optional

import numpy
import pandas as pd
from beanie import PydanticObjectId
from pydantic import BaseModel, Field
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report

from config import settings
from database.core import init as database_init
from database.models import Transaction

logger = logging.getLogger(__name__)


class MlClassifier:
    class TransactionProjection(BaseModel):
        """Extracting only the necessary fields from transaction."""

        id: PydanticObjectId = Field(alias="_id")
        amount: float
        timestamp: datetime
        type: str
        category: Optional[str] = None
        description: Optional[str] = None

        class Settings:
            populate_by_name = True

    def __init__(self, batch_size=1024):
        self.batch_size = batch_size
        self._is_initial_step = True

        # Converting categorical data to numeric using TF-IDF
        self.vectorizer = TfidfVectorizer()

        # Convert type and category to numeric values
        self.type_encoder = LabelEncoder()
        self.category_encoder = LabelEncoder()

        # Target model for fit
        self.model = SGDClassifier()

    async def run(self):
        """Preparing data and training the model on data from the database."""

        logger.info("Ml classifier started")

        # Set initial values for use classification_report
        X = None
        y = None

        async for batch in self.get_data({"category": {"$ne": None}}):
            df = pd.DataFrame(item.model_dump() for item in batch)

            df["hour"] = df["timestamp"].dt.hour
            df["day"] = df["timestamp"].dt.weekday
            df["month"] = df["timestamp"].dt.month
            df["description"] = df["description"].fillna("Unknown")
            df["description"] = self.vectorizer.fit_transform(
                df["description"]
            ).toarray()
            df["type"] = self.type_encoder.fit_transform((df["type"]))
            df["category"] = self.category_encoder.fit_transform(df["category"])

            X = df[["description", "hour", "day", "month", "type", "amount"]]
            y = df["category"]

            if self._is_initial_step:
                self._is_initial_step = False
                self.model.fit(X, y)
            else:
                self.model.partial_fit(X, y)

        y_predicted = self.model.predict(X)

        logger.info(
            classification_report(
                y,
                y_predicted,
                target_names=self.category_encoder.classes_,
                zero_division=numpy.nan,
            )
        )

    async def get_data(
        self, filters: dict
    ) -> AsyncIterator[list[TransactionProjection]]:
        batch = []

        async for transaction in Transaction.find(
            filters, batch_size=self.batch_size
        ).project(self.TransactionProjection):
            if len(batch) < self.batch_size:
                batch.append(transaction)
            else:
                yield batch
                batch.clear()

        if batch:
            yield batch


async def main():
    logging.config.dictConfig(settings.LOGGING_CONFIG)

    await database_init()

    await MlClassifier().run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
