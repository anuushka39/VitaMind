"""
Logging configuration.

Sets up two handlers:
  - console handler: human-readable, for local dev
  - rotating file handler: persists logs to disk, capped in size so it
    doesn't grow unbounded

Call configure_logging() once at app startup (see main.py). Every other
module just does `logger = logging.getLogger(__name__)` and logs normally —
that's the standard Python logging pattern, no custom wrapper needed.
"""

import logging
import logging.handlers
import os

from app.core.config import settings

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "vitamind.log")

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def configure_logging() -> None:
    os.makedirs(LOG_DIR, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)

    # Avoid duplicate handlers if configure_logging() ever gets called twice
    # (e.g. under a reloader) — without this, logs print multiple times.
    if root_logger.handlers:
        return

    formatter = logging.Formatter(LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Quiet down noisy third-party loggers so app logs aren't drowned out.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
