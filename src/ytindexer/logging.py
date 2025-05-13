import sys
from loguru import logger
from enum import StrEnum

class LogLevels(StrEnum):
    info = "INFO"
    warn = "WARNING"
    error = "ERROR"
    debug = "DEBUG"

def configure_logging(log_level: str = LogLevels.error):
    log_level = str(log_level).upper()
    valid_levels = [level.value for level in LogLevels]

    if log_level not in valid_levels:
        log_level = LogLevels.error

    logger.remove()
    if log_level == LogLevels.debug:
        logger.add(sys.stderr, level=log_level, format="<green>{time}</green> <level>{message}</level>")
    else:
        logger.add(sys.stderr, level=log_level)