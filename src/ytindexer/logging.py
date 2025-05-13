import sys
from loguru import logger
from enum import StrEnum
from pathlib import Path

class LogLevels(StrEnum):
    info = "INFO"
    warn = "WARNING"
    error = "ERROR"
    debug = "DEBUG"

def configure_logging(log_level: str = LogLevels.error, log_file: str = "logs/app.log"):
    log_level = str(log_level).upper()
    valid_levels = [level.value for level in LogLevels]

    if log_level not in valid_levels:
        log_level = LogLevels.error

    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.remove()

    # Console output
    logger.add(sys.stderr, level=log_level, format="<green>{time}</green> <level>{message}</level>")

    # File output
    logger.add(
        log_file,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        rotation="10 MB",  # Optional: rotates after 10 MB
        retention="7 days",  # Optional: keeps logs for 7 days
        enqueue=True,       # Thread-safe logging
        backtrace=True,     # Helpful for exceptions
        diagnose=True       # Helpful for debugging
    )