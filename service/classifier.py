import asyncio
import logging.config
import re
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

logging.config.dictConfig(settings.LOGGING_CONFIG)
logger = logging.getLogger(__name__)

CATEGORY_MAPPING = {
    Transaction.Category.FOOD: (
        "maxima",
        "rimi",
        "iki",
        "lidl",
        "ikea restaurant",
        "kfc",
        "restaurant",
        "cafe",
        "omelegg",
        "dominospizza",
        "casa la familia",
        "dodo pizza",
        "wolt",
        "aibe",
        "narvesen",
        "mangas",
        "ilunch",
        "kavine",
        "restoranas",
        "def enjoy",
        "bistro",
        "distilerija",
        "zemaiciu asotis",
        "domino's pizza",
        "brussels",
        "restauracja bazar",
        "stacja paliw",
        "swojski smak",
        "mcdonalds",
        "cash&carry",
        "kebab",
        "pizzaria",
        "lido atputas",
        "food truct",
        "barbora",
        "sushi",
        "asian bistro",
    ),
    Transaction.Category.GAMES: (
        "steam",
        "baitukas",
        "wargamingeu",
        "ccp games",
        "the game galaxy",
        "gamekeeper",
        "gamegoods",
        "eneba",
        "G2ACOMLIMIT",
        "LEANTEAMSRL",
    ),
    Transaction.Category.HEALTH: (
        "vin klinika",
        "geroves klinika",
        "vaistine",
        "northway",
        "optometrijos centras",
    ),
    Transaction.Category.PETS: ("veta klinika", "petcity", "zoobaze"),
    Transaction.Category.TRANSPORT: ("bolt", "admita", "uber", "ride share", "mticket"),
    Transaction.Category.INCOME: ("Wargaming Vilnius UAB: Salary",),
    Transaction.Category.SHOPPING: (
        "ikea store",
        "duck store",
        "mi-store",
        "aliexpress",
        "pigu parduotuve",
        "omniva",
        "oysho",
        "zara",
        "ideal",
        "krinona",
        "tiger",
        "massimo",
        "jo malone",
        "senukai",
        "diva boutique",
        "topo centras",
        "jysk",
        "h&m",
        "majai",
        "nike",
        "tezenis",
    ),
    Transaction.Category.BEAUTY: (
        "barbershop",
        "drogas",
        "aneb-exclusive",
        "creme de la creme",
    ),
    Transaction.Category.EDUCATION: (
        "english lesson",
        "pegasas",
        "mnogoknig",
        "UNITYTECHNO",
        "ITALKI",
    ),
    Transaction.Category.SPORT: ("teniso pasaulis", "218137"),
    Transaction.Category.SERVICES: (
        "spotify",
        "netflix",
        "leetcode",
        "mokestis",
        "72429488",
    ),
    Transaction.Category.UNCATEGORIZED: ("mokestis: grynieji", "magernastya99"),
    Transaction.Category.TRAVEL: (
        "kempingas",
        "economybookings",
        "hotel",
        "ryanair",
        "lisboa",
        "paris",
        "berlin",
        "ticketshop",
    ),
    Transaction.Category.HOUSING: ("flat",),
    Transaction.Category.MISC: ("apollo",),
}


class Classifier:
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

    @staticmethod
    async def warmup():
        """Set transaction categories by keywords."""

        logger.info("Classifier warmup")

        async def update_category(category, keywords):
            await Transaction.find(
                {
                    "category": {"$eq": None},
                    "description": {
                        "$regex": re.compile("|".join(keywords), re.IGNORECASE)
                    },
                }
            ).update({"$set": {Transaction.category: category}})

        tasks = [
            update_category(category, keywords)
            for category, keywords in CATEGORY_MAPPING.items()
        ]

        await asyncio.gather(*tasks)

    async def train(self):
        """Preparing data and training the model on data from the database."""

        logger.info("Classifier training")

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
    await database_init()

    classifier = Classifier()
    await classifier.warmup()
    await classifier.train()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped")
