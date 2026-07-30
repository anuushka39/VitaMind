"""Repository-layer test — talks to a real (in-memory) SQLite DB, no mocks.
This is the layer where you WANT real DB behavior tested, since it's the
only layer that issues actual queries."""

from app.models.user import User
from app.repositories.user_repository import UserRepository


def test_create_and_get_user(db_session):
    repo = UserRepository(db_session)
    user = repo.create(User(name="Anu", email="anu@example.com"))

    fetched = repo.get(user.id)
    assert fetched is not None
    assert fetched.email == "anu@example.com"


def test_get_by_email(db_session):
    repo = UserRepository(db_session)
    repo.create(User(name="Anu", email="anu@example.com"))

    found = repo.get_by_email("anu@example.com")
    assert found is not None

    missing = repo.get_by_email("nobody@example.com")
    assert missing is None
