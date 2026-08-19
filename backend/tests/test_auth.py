from conftest import auth_headers, register


def test_register_success(client):
    response = register(client)
    assert response.status_code == 201
    data = response.get_json()
    assert data["user"]["email"] == "alice@example.com"
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]
    assert "token" in data


def test_register_duplicate_email_conflicts(client):
    register(client)
    response = register(client)  # same default email
    assert response.status_code == 409


def test_register_invalid_email_rejected(client):
    response = client.post(
        "/api/auth/register",
        json={"name": "Bob", "email": "not-an-email", "password": "secret123"},
    )
    assert response.status_code == 400


def test_login_success(client):
    register(client)
    response = client.post(
        "/api/auth/login", json={"email": "alice@example.com", "password": "secret123"}
    )
    assert response.status_code == 200
    assert "token" in response.get_json()


def test_login_wrong_password_rejected(client):
    register(client)
    response = client.post(
        "/api/auth/login", json={"email": "alice@example.com", "password": "wrong"}
    )
    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user(client):
    headers = auth_headers(client)
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["user"]["email"] == "alice@example.com"
