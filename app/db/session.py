"""
SQLAlchemy engine + session factory + the get_db dependency.

Design choice: synchronous SQLAlchemy (Session, not AsyncSession) for V1.
FastAPI still runs sync route functions correctly (it offloads them to a
thread pool automatically), so this doesn't block the event loop. The async
value in this project shows up later (V2/V3) around Gemini/Telegram I/O and
concurrent external calls — the DB layer itself doesn't need to be async to
make that case, and sync SQLAlchemy is simpler to reason about and debug.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # detects and recycles dropped connections
    pool_size=5,
    max_overflow=10,
    echo=True,  # log SQL queries to stdout for debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency. Yields one Session per request and guarantees it's
    closed afterward, even if the request raised an exception. This is the
    concrete form of "dependency injection" in this project: routes never
    construct their own DB session, they receive one via Depends(get_db).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# @contextmanager
# def get_session_context():
#     session = Session(engine)

#     try:
#         yield session
#     except:
#         session.rollback()
#         raise
#     finally:
#         session.close()

# def get_session():
#     with get_session_context() as session:
#         yield session

# # def get_session() -> Session:
# #     with Session(engine) as session:
# #         yield session
# SessionDependency = Annotated[Session, Depends(get_session)]
