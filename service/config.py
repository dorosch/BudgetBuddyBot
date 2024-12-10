from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TOKEN: str = "FAKE_TOKEN"

    MONGODB_URI: str = "mongodb://user:password@0.0.0.0:27017/app"

    DOCUMENT_STORAGE_PATH: Path = Path(__file__).resolve().parent / "documents"

    LOGGING_CONFIG: dict = {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"}
        },
        "handlers": {
            "default": {
                "level": "INFO",
                "formatter": "standard",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            "__main__": {"handlers": ["default"], "level": "INFO", "propagate": False},
            "aiogram": {"handlers": ["default"], "level": "INFO", "propagate": False},
        },
    }


settings = Settings()
settings.DOCUMENT_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
