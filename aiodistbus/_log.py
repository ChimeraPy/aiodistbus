import logging
import logging.config
from typing import Any, Dict

LOGGING_CONFIG: Dict[str, Any] = {
    "version": 1,
    "loggers": {
        "asyncio": {
            "level": "WARNING",
        },
    },
}


def setup():
    logging.config.dictConfig(LOGGING_CONFIG)
