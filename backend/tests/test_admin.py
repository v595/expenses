import os
import sqlite3

from tests.conftest import auth_headers, register


def test_non_admin_gets_404_on_admin_routes(client):
    # The first-ever registered user is auto-promoted to admin, so register
    # someone ahead of Alice to make sure she's the non-admin one.
    auth_headers(client, name="Admin", email="admin@example.com")
    headers = auth_headers(client, name="Alice", email="alice@example.com")

    assert client.get("/api/admin/stats", headers=headers).status_code == 404
    assert client.get("/api/admin/users", headers=headers).status_code == 404
    assert client.delete("/api/admin/users/1", headers=headers).status_code == 404


def test_first_registered_user_is_admin_and_can_view_stats(client):
    # The very first account ever registered is auto-promoted to admin.
    headers = auth_headers(client, name="Admin", email="admin@example.com")

    stats_response = client.get("/api/admin/stats", headers=headers)
    assert stats_response.status_code == 200
    stats = stats_response.get_json()
    assert stats["user_count"] == 1

    users_response = client.get("/api/admin/users", headers=headers)
    assert users_response.status_code == 200
    users = users_response.get_json()
    assert len(users) == 1
    assert users[0]["email"] == "admin@example.com"


def test_admin_delete_user_records_actor_and_target_on_activity_log(client):
    admin_headers = auth_headers(client, name="Admin", email="admin@example.com")
    other_response = register(client, name="Bob", email="bob@example.com")
    other_id = other_response.get_json()["user"]["id"]

    delete_response = client.delete(f"/api/admin/users/{other_id}", headers=admin_headers)
    assert delete_response.status_code == 200

    admin_id = client.get("/api/auth/me", headers=admin_headers).get_json()["user"]["id"]

    conn = sqlite3.connect(os.environ["DATABASE_PATH"])
    row = conn.execute(
        "SELECT actor_id, target_user_id, entity_type, entity_id FROM activity_logs "
        "WHERE action = 'Deleted user (admin action)' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    assert row is not None
    assert row == (admin_id, other_id, "user", other_id)


def test_admin_cannot_delete_own_account_via_admin_route(client):
    admin_headers = auth_headers(client, name="Admin", email="admin@example.com")
    admin_id = client.get("/api/auth/me", headers=admin_headers).get_json()["user"]["id"]

    response = client.delete(f"/api/admin/users/{admin_id}", headers=admin_headers)
    assert response.status_code == 400
