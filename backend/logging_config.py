"""Logging configuration — structured logging for the Intern Pipeline.

Provides:
- Console handler (stdout) for uvicorn integration
- Rotating file handler (logs/app.log, 5MB max, 3 backups)
- Structured format with timestamps
- get_logger() helper for easy module-level loggers
- Suppressed noisy third-party loggers
"""
import logging
import logging.handlers
import os
import sys


LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")

FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging():
    """Configure root logger with console + rotating file handlers."""
    os.makedirs(LOG_DIR, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers on reload
    if root_logger.handlers:
        return

    formatter = logging.Formatter(FORMAT, datefmt=DATE_FORMAT)

    # Console handler (stdout, for uvicorn)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    for name in ("httpx", "httpcore", "sqlalchemy.engine", "sqlalchemy.pool", "uvicorn.access"):
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger. Call setup_logging() first (done in main.py startup)."""
    return logging.getLogger(name)
