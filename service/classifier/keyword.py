import asyncio
import re
import logging.config

from config import settings
from database.core import init as database_init
from database.models import Transaction

logger = logging.getLogger(__name__)


class KeywordClassifier:
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
        Transaction.Category.TRANSPORT: (
            "bolt",
            "admita",
            "uber",
            "ride share",
            "mticket",
        ),
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
        Transaction.Category.UNKNOWN: ("mokestis: grynieji", "magernastya99"),
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

    async def run(self):
        """Find the keyword in the transaction and assign the category."""

        logger.info("Keyword classifier started")

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
            for category, keywords in self.CATEGORY_MAPPING.items()
        ]

        await asyncio.gather(*tasks)


async def main():
    logging.config.dictConfig(settings.LOGGING_CONFIG)

    await database_init()

    await KeywordClassifier().run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
