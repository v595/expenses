from conftest import register


def _login_dashboard(client, email="alice@example.com", password="secret123"):
    register(client, email=email, password=password)  # first user -> auto SUPER_ADMIN
    response = client.post("/admin/login", data={"email": email, "password": password})
    assert response.status_code == 302


def test_send_test_notification_creates_notification_for_self(client):
    _login_dashboard(client)

    response = client.post("/admin/diagnostics/test-notification")
    assert response.status_code == 200
    assert b"Test notification sent" in response.data

    from app.models import user as user_model
    from app.services import notification_service

    with client.application.app_context():
        alice = user_model.get_user_by_email("alice@example.com")
        notifications = notification_service.get_notifications(alice)
        assert any(n["type"] == "admin_test" for n in notifications)


def test_messaging_status_shows_wa_link_active_and_configured(client):
    _login_dashboard(client)

    response = client.get("/admin/system-settings")
    assert response.status_code == 200
    assert b"wa_link" in response.data
    assert b"Active" in response.data


def test_get_messaging_status_service_shape(client):
    from app.services import admin_service

    with client.application.app_context():
        status = admin_service.get_messaging_status()
    assert status["active_driver"] == "wa_link"
    names = {d["name"] for d in status["drivers"]}
    assert names == {"wa_link", "twilio", "msg91"}
    wa_link = next(d for d in status["drivers"] if d["name"] == "wa_link")
    assert wa_link["is_configured"] is True
    assert wa_link["is_active"] is True
