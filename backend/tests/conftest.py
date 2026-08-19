import os
import tempfile

import pytest

from app import create_app


@pytest.fixture
def client(monkeypatch):
    """A Flask test client backed by a fresh, throwaway SQLite file per test."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    monkeypatch.setenv("DATABASE_PATH", db_path)

    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client

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
