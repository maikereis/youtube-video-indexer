"""
Logging configuration module using Loguru.

This module defines a logging configuration function `configure_logging`
that sets up logging output both to the console (stderr) and to a file.
It supports different log levels and manages log file rotation and retention.

Classes:
    LogLevels: An enumeration of supported logging levels.

Functions:
    configure_logging(log_level: str, log_file: str): Configures logger with given level and file path.

Example:
    configure_logging(log_level="INFO", log_file="logs/app.log")
"""

import sys
from enum import StrEnum
from pathlib import Path

from loguru import logger


class LogLevels(StrEnum):
    """
    Enumeration of supported logging levels.

    Attributes:
        INFO (str): Informational messages.
        WARN (str): Warning messages.
        ERROR (str): Error messages.
        DEBUG (str): Debug messages.
    """

    INFO = "INFO"
    WARN = "WARNING"
    ERROR = "ERROR"
    DEBUG = "DEBUG"


def configure_logging(log_level: str = LogLevels.ERROR, log_file: str = "logs/api.log"):
    """
    Configure logging outputs with Loguru logger.

    Sets up logging to both stderr and a rotating file.
    Creates necessary directories for log files if they don't exist.

    Args:
        log_level (str, optional): Logging level to use. Defaults to LogLevels.ERROR.
            Valid levels are: "INFO", "WARNING", "ERROR", "DEBUG".
        log_file (str, optional): File path to save logs. Defaults to "logs/app.log".

    Returns:
        None
    """
    log_level = str(log_level).upper()
    valid_levels = [level.value for level in LogLevels]

    if log_level not in valid_levels:
        log_level = LogLevels.ERROR

    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.remove()

    # Console output
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time}</green> <level>{message}</level>",
    )

    # File output
    logger.add(
        log_file,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        rotation="10 MB",  # Optional: rotates after 10 MB
        retention="7 days",  # Optional: keeps logs for 7 days
        enqueue=True,  # Thread-safe logging
        backtrace=True,  # Helpful for exceptions
        diagnose=True,  # Helpful for debugging
    )
