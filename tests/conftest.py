"""
Shared pytest fixtures.

Why this file exists:
    Every repository/service/API test needs an isolated database — never
    the real vitamind.db, and never sharing state between tests. This file
    provides one: a fresh in-memory SQLite database per test function,
    built from the same Base.metadata the real app uses (so schema drift
    between test and prod DB is impossible), torn down automatically after
    each test.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app import models as _models  # noqa: F401 — ensures all models are registered on Base


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # keeps the same in-memory DB across connections within a test
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session: Session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
