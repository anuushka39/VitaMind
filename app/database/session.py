"""
Database connection layer.

Why this file exists:
    This is the ONLY file that constructs the SQLAlchemy engine and session
    factory. Repositories (V2 onward) depend on `get_db()` as a FastAPI
    dependency, never on the engine directly — that's what keeps this the
    single point of change when the database itself changes, as it just did.

    V1->V2 change: switched from async MySQL to sync SQLite. SQLite has no
    real concurrent-write model for async to meaningfully help with, and
    FastAPI already runs sync dependencies in a threadpool, so the event
    loop is never blocked by this choice. Repositories and services written
    from here on are plain `def`, not `async def` — that's a direct
    consequence of this decision, not an inconsistency.

    Database-agnostic by design: nothing outside this file (and one
    SQLite-only connect_args flag below) knows or cares that the database
    is SQLite. Migrating to MySQL later means changing DATABASE_URL and
    dropping the connect_args block — no repository or service changes.

Which files depend on this:
    app/api/health.py (connectivity check)
    app/repositories/*.py (V2 onward, all DB access)
    app/database/base.py (imports nothing from here, but Alembic's env.py
        will import both base.py's Base and this file's engine)
"""

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# connect_args is the one genuinely SQLite-specific line in this file.
# SQLite objects aren't thread-safe by default; FastAPI may serve a sync
# dependency from a different thread than the one that opened the
# connection, so we relax that check here. On MySQL this line is simply
# removed — there is no equivalent flag to carry over.
_connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(
    settings.database_url,
    echo=False,          # set True locally if you need to see raw SQL
    pool_pre_ping=True,   # detects and replaces dead connections automatically
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session and guarantees it's
    closed afterward, even if the request raises an exception.

    Usage in a router:
        @router.get("/something")
        def handler(db: Session = Depends(get_db)):
            ...
    Note: `def`, not `async def` — FastAPI runs sync dependencies in a
    threadpool automatically, so this doesn't block the event loop.
    """
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_db_connection() -> bool:
    """
    Lightweight connectivity check used by the health endpoint.
    Returns True/False rather than raising, so /health can report status
    instead of crashing when the DB is briefly unavailable.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("Database connectivity check failed: %s", exc)
        return False
