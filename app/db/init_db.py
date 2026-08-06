"""
Table creation.

V1 uses Base.metadata.create_all() for simplicity — good enough while the
schema is still small and changing daily. A migration tool (Alembic) gets
introduced later (V4 polish, or sooner if the schema needs a real migration
instead of a fresh create) once the schema stabilizes and you need to alter
existing tables without dropping data.

Models must be imported here (even if unused directly) so Base.metadata
knows about them before create_all() runs — SQLAlchemy only registers a
table once its model class has been imported somewhere.
"""

import logging

from app.db.base import Base
from app.db.session import engine
from app.models import conversation  # noqa: F401  (import registers the model)
from app.models import meal  # noqa: F401  (import registers the model)
from app.models import reminder  # noqa: F401  (import registers the model)
from app.models import user  # noqa: F401  (import registers the model)

logger = logging.getLogger(__name__)


def init_db() -> None:
    logger.info("Creating database tables (if not already present)...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready.")
