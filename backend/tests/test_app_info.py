def test_app_info_public_default(client):
    response = client.get("/api/app-info")
    assert response.status_code == 200
    assert response.get_json()["app_name"] == "Hisaab"


def test_app_info_reflects_updated_setting(client):
    from app.services import system_settings_service

    with client.application.app_context():
        system_settings_service.update_settings({"app_name": "MoneyWise"}, actor_id=None)

    response = client.get("/api/app-info")
    assert response.get_json()["app_name"] == "MoneyWise"
