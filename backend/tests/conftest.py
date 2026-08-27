import os
import tempfile

import pytest

from app import create_app
from app.extensions import db


@pytest.fixture
def client(monkeypatch):
    """A Flask test client backed by a fresh, throwaway SQLite file per test."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    monkeypatch.setenv("DATABASE_PATH", db_path)

    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client

    # SQLAlchemy pools a persistent connection to the SQLite file (unlike the
    # old per-request sqlite3.connect()/close()), so it has to be disposed
    # before the file can be removed — otherwise Windows refuses to unlink a
    # file that's still open.
    with app.app_context():
        db.session.remove()
        db.engine.dispose()

    os.close(db_fd)
    os.unlink(db_path)


def register(client, name="Alice", email="alice@example.com", password="secret123"):
    return client.post(
        "/api/auth/register", json={"name": name, "email": email, "password": password}
    )


def auth_headers(client, **kwargs):
    """Registers a user and returns headers ready to use on protected routes."""
    response = register(client, **kwargs)
    token = response.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}
