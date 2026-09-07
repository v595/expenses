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


def test_update_name(client):
    headers = auth_headers(client)
    response = client.put("/api/auth/me", json={"name": "Alicia"}, headers=headers)
    assert response.status_code == 200
    assert response.get_json()["user"]["name"] == "Alicia"


def test_change_password_requires_correct_current_password(client):
    headers = auth_headers(client)
    response = client.put(
        "/api/auth/me",
        json={"current_password": "wrong", "new_password": "newsecret123"},
        headers=headers,
    )
    assert response.status_code == 401


def test_update_avatar(client):
    headers = auth_headers(client)
    tiny_png = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    response = client.put("/api/auth/me", json={"avatar": tiny_png}, headers=headers)
    assert response.status_code == 200
    assert response.get_json()["user"]["avatar"] == tiny_png


def test_update_avatar_rejects_non_image(client):
    headers = auth_headers(client)
    response = client.put("/api/auth/me", json={"avatar": "not-an-image"}, headers=headers)
    assert response.status_code == 400


def test_change_password_success_then_old_password_fails(client):
    headers = auth_headers(client)
    response = client.put(
        "/api/auth/me",
        json={"current_password": "secret123", "new_password": "newsecret123"},
        headers=headers,
    )
    assert response.status_code == 200

    old_login = client.post(
        "/api/auth/login", json={"email": "alice@example.com", "password": "secret123"}
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/auth/login", json={"email": "alice@example.com", "password": "newsecret123"}
    )
    assert new_login.status_code == 200


def test_account_locks_after_repeated_failed_logins(client):
    register(client)

    for _ in range(5):
        response = client.post(
            "/api/auth/login", json={"email": "alice@example.com", "password": "wrong"}
        )
        assert response.status_code == 401

    # 6th attempt is locked out even with the correct password.
    locked = client.post(
        "/api/auth/login", json={"email": "alice@example.com", "password": "secret123"}
    )
    assert locked.status_code == 429


def test_two_factor_setup_enable_and_login_flow(client):
    headers = auth_headers(client)

    setup = client.post("/api/auth/2fa/setup", headers=headers)
    assert setup.status_code == 200
    secret = setup.get_json()["secret"]

    import pyotp

    code = pyotp.TOTP(secret).now()
    enable = client.post("/api/auth/2fa/enable", json={"code": code}, headers=headers)
    assert enable.status_code == 200
    assert enable.get_json()["user"]["totp_enabled"] is True

    # Password alone no longer completes login.
    login = client.post(
        "/api/auth/login", json={"email": "alice@example.com", "password": "secret123"}
    )
    assert login.status_code == 200
    login_data = login.get_json()
    assert login_data["requires_two_factor"] is True
    assert "token" not in login_data

    verify = client.post(
        "/api/auth/2fa/verify",
        json={"ticket": login_data["ticket"], "code": pyotp.TOTP(secret).now()},
    )
    assert verify.status_code == 200
    assert "token" in verify.get_json()


def test_two_factor_wrong_code_rejected(client):
    headers = auth_headers(client)
    setup = client.post("/api/auth/2fa/setup", headers=headers)
    secret = setup.get_json()["secret"]

    import pyotp

    client.post("/api/auth/2fa/enable", json={"code": pyotp.TOTP(secret).now()}, headers=headers)

    login = client.post(
        "/api/auth/login", json={"email": "alice@example.com", "password": "secret123"}
    )
    ticket = login.get_json()["ticket"]

    bad = client.post("/api/auth/2fa/verify", json={"ticket": ticket, "code": "000000"})
    assert bad.status_code == 401


def test_two_factor_disable_requires_password_and_code(client):
    headers = auth_headers(client)
    setup = client.post("/api/auth/2fa/setup", headers=headers)
    secret = setup.get_json()["secret"]

    import pyotp

    client.post("/api/auth/2fa/enable", json={"code": pyotp.TOTP(secret).now()}, headers=headers)

    wrong_password = client.post(
        "/api/auth/2fa/disable",
        json={"password": "wrong", "code": pyotp.TOTP(secret).now()},
        headers=headers,
    )
    assert wrong_password.status_code == 401

    disable = client.post(
        "/api/auth/2fa/disable",
        json={"password": "secret123", "code": pyotp.TOTP(secret).now()},
        headers=headers,
    )
    assert disable.status_code == 200
    assert disable.get_json()["user"]["totp_enabled"] is False
