"""
Shared pytest fixtures.

Core idea: swap MySQL for an in-memory SQLite database for the whole test
session, using a StaticPool so the same in-memory DB persists across
connections (plain SQLite :memory: otherwise gives every new connection its
own empty database).

Several modules do `from app.db.session import SessionLocal` directly
(webhooks, scheduler jobs) rather than importing the app.db.session module
and accessing SessionLocal through it — that import style binds the name at
import time, so patching app.db.session.SessionLocal alone would NOT affect
those modules. Each one is patched explicitly below for that reason.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(autouse=True)
def _reset_rate_limit_state():
    """
    Runs before every test. The rate-limit middleware's hit counters live
    on a module-level dict (see rate_limit_middleware.py) precisely so this
    reset is possible — the FastAPI `app` object is created once and reused
    for the whole test session, so without this, hits from one test would
    leak into the next.
    """
    from app.middleware.rate_limit_middleware import reset_rate_limit_state

    reset_rate_limit_state()
    yield
    reset_rate_limit_state()


@pytest.fixture(autouse=True)
def _skip_vector_store_warmup(monkeypatch):
    """
    main.py's lifespan calls get_retriever() at startup to warm/build the
    FAISS index, per the app's real startup contract. In tests that would
    mean every single test's TestClient startup tries to download the
    HuggingFace embedding model over the network — patched to a no-op here
    so the whole suite stays network-free, as documented in the README.
    RecommendationService itself is tested separately, in isolation, with
    an injected fake retriever (see test_recommendation.py).
    """
    import app.main as main_mod

    monkeypatch.setattr(main_mod, "get_retriever", lambda: None)


@pytest.fixture()
def test_session_factory(monkeypatch, _skip_vector_store_warmup):
    """Sets up a fresh in-memory SQLite DB and patches every module that
    holds its own reference to the engine/SessionLocal. Function-scoped so
    each test starts with a clean database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestSessionLocal = sessionmaker(bind=engine)

    import app.db.session as session_mod

    monkeypatch.setattr(session_mod, "engine", engine)
    monkeypatch.setattr(session_mod, "SessionLocal", TestSessionLocal)

    import app.db.init_db as init_db_mod

    monkeypatch.setattr(init_db_mod, "engine", engine)

    import app.api.webhooks.telegram as telegram_mod
    # import app.api.webhooks.whatsapp as whatsapp_mod
    import app.scheduler.jobs as jobs_mod

    monkeypatch.setattr(telegram_mod, "SessionLocal", TestSessionLocal)
    # monkeypatch.setattr(whatsapp_mod, "SessionLocal", TestSessionLocal)
    monkeypatch.setattr(jobs_mod, "SessionLocal", TestSessionLocal)

    yield TestSessionLocal

    engine.dispose()


@pytest.fixture()
def client(test_session_factory):
    """A TestClient wired to the in-memory DB, with the app's full
    lifespan (table creation, scheduler start/stop) running around it."""
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db_session(test_session_factory):
    """A raw DB session for direct setup/assertions in tests that need to
    bypass the API (e.g. inserting meals with a specific meal_time to test
    the weekly report's date-window filtering)."""
    session = test_session_factory()
    yield session
    session.close()


@pytest.fixture()
def make_user(db_session):
    """Factory fixture: make_user() -> a persisted User with sensible
    defaults, overridable via kwargs."""
    from app.models.user import Platform, User

    def _make(platform=Platform.telegram, platform_user_id="test_chat_1", name="Test User"):
        user = User(platform=platform, platform_user_id=platform_user_id, name=name)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make
