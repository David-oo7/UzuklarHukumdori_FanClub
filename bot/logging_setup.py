import logging
import os
from logging.handlers import RotatingFileHandler

from bot import config


def setup_logging() -> None:
    os.makedirs(config.LOG_DIR, exist_ok=True)

    logger = logging.getLogger("support_bot")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = RotatingFileHandler(
        config.LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # aiogram'ning o'z loglarini ham shu faylga yozamiz.
    aiogram_logger = logging.getLogger("aiogram")
    aiogram_logger.setLevel(logging.WARNING)
    aiogram_logger.addHandler(file_handler)
