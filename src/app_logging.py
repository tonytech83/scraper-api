# import logging
# from enum import StrEnum

# LOG_FORMAT_DEBUG = "%(levelname)s:%(message)s:%(pathname)s:%(funcName)s:%(lineno)d"

# class LogLevels(StrEnum):
#     info = "INFO"
#     warn = "WARN"
#     error = "ERROR"
#     debug = "DEBUG"

# def configure_logging(level: LogLevels = LogLevels.error) -> None:
#     level_map = {
#         LogLevels.debug: logging.DEBUG,
#         LogLevels.info: logging.INFO,
#         LogLevels.warn: logging.WARNING,
#         LogLevels.error: logging.ERROR,
#     }

#     logging_level = level_map.get(level, logging.ERROR)

#     if level == LogLevels.debug:
#         logging.basicConfig(level=logging_level, format=LOG_FORMAT_DEBUG)
#     else:
#         logging.basicConfig(level=logging_level)

# def get_logger(name: str | None = None) -> logging.Logger:
#     return logging.getLogger(name)
import logging
import logging.config
from copy import deepcopy
from enum import StrEnum

from uvicorn.config import LOGGING_CONFIG as UVICORN_LOGGING_CONFIG


class LogLevels(StrEnum):
    info = "INFO"
    warn = "WARN"
    error = "ERROR"
    debug = "DEBUG"


def configure_logging(level: LogLevels = LogLevels.info) -> None:
    """Use Uvicorn's logging config + add our own logger."""
    config = deepcopy(UVICORN_LOGGING_CONFIG)

    # Set global level
    config["loggers"]["uvicorn"]["level"] = level.value
    config["loggers"]["uvicorn.error"]["level"] = level.value
    config["loggers"]["uvicorn.access"]["level"] = level.value

    # Add our package logger so it uses the same `default` handler/formatter
    config["loggers"]["src"] = {
        "handlers": ["default"],
        "level": level.value,
        "propagate": False,
    }

    logging.config.dictConfig(config)


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name)
