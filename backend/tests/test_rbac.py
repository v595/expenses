import os
import sqlite3

from tests.conftest import auth_headers, register


def _promote(email, role_name):
    """Test-only helper: directly sets a user's role by name, bypassing the
    admin API (which is exactly what these tests are verifying access to)."""
    conn = sqlite3.connect(os.environ["DATABASE_PATH"])
    role_id = conn.execute("SELECT id FROM roles WHERE name = ?", (role_name,)).fetchone()[0]
    is_admin = 1 if role_name in ("ADMIN", "SUPER_ADMIN") else 0
    conn.execute("UPDATE users SET role_id = ?, is_admin = ? WHERE email = ?", (role_id, is_admin, email))
    conn.commit()
    conn.close()


def _suspend(email):
    conn = sqlite3.connect(os.environ["DATABASE_PATH"])
    conn.execute("UPDATE users SET is_suspended = 1 WHERE email = ?", (email,))
    conn.commit()
    conn.close()


def _set_maintenance_mode(enabled):
    conn = sqlite3.connect(os.environ["DATABASE_PATH"])
    conn.execute(
        "UPDATE system_settings SET value = ? WHERE key = 'maintenance_mode'", ("true" if enabled else "false",)
    )
    conn.commit()
    conn.close()


def test_first_user_is_super_admin_rest_are_user(client):
    first = auth_headers(client, name="First", email="first@example.com")
    second = auth_headers(client, name="Second", email="second@example.com")

    first_me = client.get("/api/auth/me", headers=first).get_json()["user"]
    second_me = client.get("/api/auth/me", headers=second).get_json()["user"]

    assert first_me["role_name"] == "SUPER_ADMIN"
    assert second_me["role_name"] == "USER"


def test_user_blocked_from_admin_and_super_admin_apis(client):
    auth_headers(client, name="Admin", email="admin@example.com")  # first user = SUPER_ADMIN
    user_headers = auth_headers(client, name="Plain", email="plain@example.com")

    assert client.get("/api/admin/stats", headers=user_headers).status_code == 404
    assert client.get("/api/admin/audit-logs", headers=user_headers).status_code == 403
    assert client.get("/api/super-admin/admins", headers=user_headers).status_code == 403
    assert client.get("/api/super-admin/roles", headers=user_headers).status_code == 403
    assert client.get("/api/super-admin/system-health", headers=user_headers).status_code == 403


def test_unauthenticated_gets_401_not_403(client):
    assert client.get("/api/admin/audit-logs").status_code == 401
    assert client.get("/api/super-admin/admins").status_code == 401


def test_admin_can_view_users_but_not_super_admin_only_pages(client):
    auth_headers(client, name="Super", email="super@example.com")  # first user = SUPER_ADMIN
    admin_headers = auth_headers(client, name="Admin", email="admin2@example.com")
    _promote("admin2@example.com", "ADMIN")

    assert client.get("/api/admin/audit-logs", headers=admin_headers).status_code == 200
    # ADMIN has no admins.*/roles.*/feature_flags.*/settings.* permissions.
    assert client.get("/api/super-admin/admins", headers=admin_headers).status_code == 403
    assert client.get("/api/super-admin/roles", headers=admin_headers).status_code == 403
    assert client.get("/api/super-admin/feature-flags", headers=admin_headers).status_code == 403
    assert client.get("/api/super-admin/system-settings", headers=admin_headers).status_code == 403
    assert client.get("/api/super-admin/system-health", headers=admin_headers).status_code == 403


def test_admin_cannot_create_admin_or_super_admin_account(client):
    auth_headers(client, name="Super", email="super@example.com")
    admin_headers = auth_headers(client, name="Admin", email="admin2@example.com")
    _promote("admin2@example.com", "ADMIN")

    response = client.post(
        "/api/super-admin/admins",
        json={"name": "New", "email": "new@example.com", "password": "secret123", "role": "ADMIN"},
        headers=admin_headers,
    )
    assert response.status_code == 403


def test_super_admin_can_create_admin_but_not_via_admin_role(client):
    super_headers = auth_headers(client, name="Super", email="super@example.com")

    response = client.post(
        "/api/super-admin/admins",
        json={"name": "New Admin", "email": "newadmin@example.com", "password": "secret123", "role": "ADMIN"},
        headers=super_headers,
    )
    assert response.status_code == 201
    assert response.get_json()["user"]["role_name"] == "ADMIN"

    # The new ADMIN cannot mint a SUPER_ADMIN, even though admins.create was
    # never granted to ADMIN in the first place.
    new_admin_login = client.post(
        "/api/auth/login", json={"email": "newadmin@example.com", "password": "secret123"}
    ).get_json()
    new_admin_headers = {"Authorization": f"Bearer {new_admin_login['token']}"}
    response = client.post(
        "/api/super-admin/admins",
        json={"name": "Escalated", "email": "escalated@example.com", "password": "secret123", "role": "SUPER_ADMIN"},
        headers=new_admin_headers,
    )
    assert response.status_code == 403


def test_suspended_user_rejected_on_login_and_existing_token(client):
    headers = auth_headers(client, name="ToSuspend", email="suspend@example.com")
    assert client.get("/api/auth/me", headers=headers).status_code == 200

    _suspend("suspend@example.com")

    # Existing token stops working immediately.
    assert client.get("/api/auth/me", headers=headers).status_code == 403

    # Fresh login attempt is also rejected.
    response = client.post("/api/auth/login", json={"email": "suspend@example.com", "password": "secret123"})
    assert response.status_code == 403


def test_maintenance_mode_blocks_non_admin_not_admin(client):
    auth_headers(client, name="Super", email="super@example.com")
    register(client, name="Regular", email="regular@example.com")

    _set_maintenance_mode(True)
    try:
        response = client.post(
            "/api/auth/login", json={"email": "regular@example.com", "password": "secret123"}
        )
        assert response.status_code == 503

        # New registrations are blocked outright during maintenance.
        response = client.post(
            "/api/auth/register", json={"name": "Blocked", "email": "blocked@example.com", "password": "secret123"}
        )
        assert response.status_code == 503

        # The super admin can still log in.
        response = client.post("/api/auth/login", json={"email": "super@example.com", "password": "secret123"})
        assert response.status_code == 200
    finally:
        _set_maintenance_mode(False)


def test_feature_flags_and_system_settings_round_trip_for_super_admin(client):
    super_headers = auth_headers(client, name="Super", email="super@example.com")

    flags = client.get("/api/super-admin/feature-flags", headers=super_headers).get_json()
    assert any(f["key"] == "ai_assistant" for f in flags)

    response = client.put(
        "/api/super-admin/feature-flags/ai_assistant", json={"enabled": True}, headers=super_headers
    )
    assert response.status_code == 200
    assert response.get_json()["flag"]["is_enabled"] is True

    response = client.put(
        "/api/super-admin/system-settings", json={"app_name": "My Tracker"}, headers=super_headers
    )
    assert response.status_code == 200
    assert response.get_json()["settings"]["app_name"] == "My Tracker"
