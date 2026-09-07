import pyotp
from conftest import register


def _login_dashboard(client, email="alice@example.com", password="secret123"):
    register(client, email=email, password=password)  # first user -> auto SUPER_ADMIN
    response = client.post("/admin/login", data={"email": email, "password": password})
    assert response.status_code == 302


def _make_admin_with_2fa(client):
    """Registers the first user (auto-promoted to admin), enables 2FA on
    it via the JSON API, and returns (email, password, totp_secret)."""
    email, password = "alice@example.com", "secret123"
    reg = register(client, email=email, password=password)
    headers = {"Authorization": f"Bearer {reg.get_json()['token']}"}

    setup = client.post("/api/auth/2fa/setup", headers=headers)
    secret = setup.get_json()["secret"]
    code = pyotp.TOTP(secret).now()
    client.post("/api/auth/2fa/enable", json={"code": code}, headers=headers)

    return email, password, secret


def test_admin_login_without_2fa_goes_straight_to_dashboard(client):
    email, password = "alice@example.com", "secret123"
    register(client, email=email, password=password)

    response = client.post(
        "/admin/login", data={"email": email, "password": password}, follow_redirects=False
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/admin"


def test_admin_login_with_2fa_does_not_establish_session(client):
    email, password, _secret = _make_admin_with_2fa(client)

    response = client.post("/admin/login", data={"email": email, "password": password})
    assert response.status_code == 200
    assert b"6-digit code" in response.data

    # Password alone must not be enough to reach the dashboard.
    dashboard = client.get("/admin", follow_redirects=False)
    assert dashboard.status_code == 302
    assert dashboard.headers["Location"] == "/admin/login"


def test_admin_login_2fa_correct_code_logs_in(client):
    email, password, secret = _make_admin_with_2fa(client)

    login = client.post("/admin/login", data={"email": email, "password": password})
    # Extract the hidden ticket field from the rendered form.
    html = login.data.decode()
    ticket = html.split('name="ticket" value="')[1].split('"')[0]

    response = client.post(
        "/admin/login/2fa", data={"ticket": ticket, "code": pyotp.TOTP(secret).now()}, follow_redirects=False
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/admin"

    dashboard = client.get("/admin")
    assert dashboard.status_code == 200


def test_admin_login_2fa_wrong_code_rejected(client):
    email, password, _secret = _make_admin_with_2fa(client)

    login = client.post("/admin/login", data={"email": email, "password": password})
    html = login.data.decode()
    ticket = html.split('name="ticket" value="')[1].split('"')[0]

    response = client.post("/admin/login/2fa", data={"ticket": ticket, "code": "000000"})
    assert response.status_code == 200
    assert b"Invalid authentication code" in response.data

    dashboard = client.get("/admin", follow_redirects=False)
    assert dashboard.status_code == 302


def test_admin_login_2fa_bad_ticket_rejected(client):
    _make_admin_with_2fa(client)

    response = client.post("/admin/login/2fa", data={"ticket": "not-a-real-ticket", "code": "123456"})
    assert response.status_code == 200
    assert b"expired" in response.data


def test_dashboard_search_filters_users(client):
    _login_dashboard(client)
    register(client, name="Bob Smith", email="bob@example.com", password="secret123")
    register(client, name="Carol Jones", email="carol@example.com", password="secret123")

    response = client.get("/admin?q=Bob")
    assert response.status_code == 200
    assert b"bob@example.com" in response.data
    # Name-only check would false-positive on the unfiltered Recent Activity
    # feed, which also lists Carol's registration — email is table-only.
    assert b"carol@example.com" not in response.data


def test_dashboard_role_filter(client):
    _login_dashboard(client)
    register(client, name="Regular User", email="regular@example.com", password="secret123")

    response = client.get("/admin?role=SUPER_ADMIN")
    assert b"regular@example.com" not in response.data
    assert b"alice@example.com" in response.data

    response = client.get("/admin?role=USER")
    assert b"regular@example.com" in response.data
    assert b"alice@example.com" not in response.data


def test_dashboard_status_filter_suspended(client):
    _login_dashboard(client)
    reg = register(client, name="Suspended Guy", email="suspended@example.com", password="secret123")
    suspended_id = reg.get_json()["user"]["id"]

    client.post(f"/admin/users/{suspended_id}/suspend")

    response = client.get("/admin?status=suspended")
    assert b"suspended@example.com" in response.data
    assert b"alice@example.com" not in response.data


def test_dashboard_pagination(client):
    _login_dashboard(client)
    for i in range(30):
        register(client, name=f"User{i}", email=f"user{i}@example.com", password="secret123")

    page1 = client.get("/admin?page=1")
    page2 = client.get("/admin?page=2")
    assert page1.status_code == 200 and page2.status_code == 200
    assert page1.data != page2.data


def test_export_users_csv(client):
    _login_dashboard(client)
    register(client, name="Export Me", email="exportme@example.com", password="secret123")

    response = client.get("/admin/users/export.csv")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/csv")
    body = response.data.decode()
    assert "Export Me" in body
    assert "exportme@example.com" in body


def test_edit_admin_profile(client):
    _login_dashboard(client)
    reg = register(client, name="Target Admin", email="targetadmin@example.com", password="secret123")
    target_id = reg.get_json()["user"]["id"]
    client.post(f"/admin/users/{target_id}/role", data={"role": "ADMIN"})

    response = client.post(
        f"/admin/admins/{target_id}/edit", data={"name": "Renamed Admin", "email": "renamed@example.com"}
    )
    assert response.status_code == 302

    admins = client.get("/admin/admins")
    assert b"Renamed Admin" in admins.data
    assert b"renamed@example.com" in admins.data


def test_edit_admin_rejects_duplicate_email(client):
    _login_dashboard(client)
    register(client, name="Other", email="other@example.com", password="secret123")
    reg = register(client, name="Target Admin", email="targetadmin@example.com", password="secret123")
    target_id = reg.get_json()["user"]["id"]
    client.post(f"/admin/users/{target_id}/role", data={"role": "ADMIN"})

    response = client.post(
        f"/admin/admins/{target_id}/edit", data={"name": "Target Admin", "email": "other@example.com"}
    )
    assert response.status_code == 200
    assert b"already registered" in response.data


def test_reset_admin_password_shows_link(client):
    _login_dashboard(client)
    reg = register(client, name="Target Admin", email="targetadmin@example.com", password="secret123")
    target_id = reg.get_json()["user"]["id"]
    client.post(f"/admin/users/{target_id}/role", data={"role": "ADMIN"})

    response = client.post(f"/admin/admins/{target_id}/reset-password")
    assert response.status_code == 200
    assert b"Password reset link" in response.data
    assert b"Target Admin" in response.data


def test_change_user_role(client):
    _login_dashboard(client)
    reg = register(client, name="Future Admin", email="futureadmin@example.com", password="secret123")
    target_id = reg.get_json()["user"]["id"]

    response = client.post(f"/admin/users/{target_id}/role", data={"role": "ADMIN"})
    assert response.status_code == 302

    admins = client.get("/admin/admins")
    assert b"Future Admin" in admins.data


def test_change_role_to_admin_requires_admins_update_permission(client):
    """A role with users.update but not admins.update must not be able to
    promote someone to ADMIN through the shared change-role endpoint."""
    from app.models import role as role_model
    from app.models import user as user_model
    from app.services import admin_service

    _login_dashboard(client)  # Alice, SUPER_ADMIN
    reg = register(client, name="Target", email="target@example.com", password="secret123")
    target_id = reg.get_json()["user"]["id"]

    with client.application.app_context():
        admin_role = role_model.get_role_by_name("ADMIN")
        role_model.set_role_permissions(admin_role["id"], ["users.update"])  # no admins.update

        limited_admin = user_model.create_user("Limited", "limited@example.com", "x")
        user_model.set_role(limited_admin["id"], admin_role["id"])
        limited_admin = user_model.get_user_by_id(limited_admin["id"])

        try:
            admin_service.change_user_role(target_id, "ADMIN", limited_admin)
            assert False, "expected ValueError"
        except ValueError as e:
            assert "permission" in str(e)


def test_audit_log_search_filters(client):
    _login_dashboard(client)
    register(client, name="Searchable Person", email="searchable@example.com", password="secret123")

    response = client.get("/admin/audit-logs?scope=all&q=Searchable")
    assert response.status_code == 200
    assert b"Searchable Person" in response.data


def test_audit_log_date_range_excludes_out_of_range(client):
    _login_dashboard(client)

    response = client.get("/admin/audit-logs?scope=all&start_date=2099-01-01")
    assert response.status_code == 200
    # Everything happened "now" (well before 2099), so nothing should match.
    assert b"alice@example.com" not in response.data or b"No matching" in response.data


def test_audit_log_export_csv(client):
    _login_dashboard(client)
    response = client.get("/admin/audit-logs/export.csv?scope=all")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/csv")
    assert b"When,User,Action,Details" in response.data


def test_security_events_export_csv(client):
    register(client, email="alice@example.com", password="secret123")  # first user -> auto SUPER_ADMIN
    client.post("/admin/login", data={"email": "alice@example.com", "password": "wrong"})  # generates an event, not yet logged in
    client.post("/admin/login", data={"email": "alice@example.com", "password": "secret123"})  # now log in for real

    response = client.get("/admin/security-events/export.csv")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/csv")
    assert b"Failed admin login attempt" in response.data


def test_audit_log_pagination(client):
    _login_dashboard(client)
    for i in range(60):
        register(client, name=f"Bulk{i}", email=f"bulk{i}@example.com", password="secret123")

    page1 = client.get("/admin/audit-logs?scope=all&page=1")
    page2 = client.get("/admin/audit-logs?scope=all&page=2")
    assert page1.status_code == 200 and page2.status_code == 200
    assert page1.data != page2.data


def test_change_own_role_rejected(client):
    _login_dashboard(client)

    from app.models import user as user_model
    from app.services import admin_service

    with client.application.app_context():
        alice = user_model.get_user_by_email("alice@example.com")
        try:
            admin_service.change_user_role(alice["id"], "ADMIN", alice)
            assert False, "expected ValueError"
        except ValueError as e:
            assert "own role" in str(e)
