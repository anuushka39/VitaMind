"""
Structured logging configuration.

Why this file exists:
    Without a central setup, every module ends up either using bare print()
    or reconfiguring the logging module in slightly different ways. This
    file configures logging once, at import time, with a consistent format
    that includes the timestamp, log level, module name, and message —
    which is what makes logs greppable/debuggable once there's more than
    one file writing to them.

How it's used elsewhere:
    from app.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("meal logged", extra={"user_id": user_id})
"""

import logging
import sys

from app.config.settings import settings

_LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)


def _configure_root_logger() -> None:
    root = logging.getLogger()
    if root.handlers:
        # Already configured (e.g. re-imported in tests) — don't duplicate handlers.
        return

    root.setLevel(settings.log_level.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root.addHandler(handler)


_configure_root_logger()


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger, e.g. get_logger(__name__)."""
    return logging.getLogger(name)
