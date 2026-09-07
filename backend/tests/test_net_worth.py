from conftest import auth_headers
from app.services import feature_flag_service


def _add_account(client, headers, name, type_, balance):
    return client.post(
        "/api/accounts", json={"name": name, "type": type_, "balance": balance}, headers=headers
    )


def test_net_worth_subtracts_loans_from_assets(client):
    headers = auth_headers(client)
    _add_account(client, headers, "Savings", "savings", 100000)
    _add_account(client, headers, "Stocks", "investment", 50000)
    _add_account(client, headers, "Car Loan", "loan", 30000)

    response = client.get("/api/accounts/net-worth", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["assets"] == 150000
    assert data["liabilities"] == 30000
    assert data["net_worth"] == 120000
    assert data["by_type"]["loan"] == 30000
    assert data["by_type"]["investment"] == 50000


def test_net_worth_with_no_accounts(client):
    headers = auth_headers(client)
    response = client.get("/api/accounts/net-worth", headers=headers)
    data = response.get_json()
    assert data == {"assets": 0.0, "liabilities": 0.0, "net_worth": 0.0, "by_type": {}}


def test_account_accepts_investment_and_loan_types(client):
    headers = auth_headers(client)
    response = _add_account(client, headers, "401k", "investment", 1000)
    assert response.status_code == 201
    response = _add_account(client, headers, "Mortgage", "loan", 200000)
    assert response.status_code == 201


def test_net_worth_returns_404_when_feature_flag_disabled(client):
    headers = auth_headers(client)
    with client.application.app_context():
        feature_flag_service.set_enabled("net_worth", False, actor_id=None)
    try:
        response = client.get("/api/accounts/net-worth", headers=headers)
        assert response.status_code == 404
    finally:
        with client.application.app_context():
            feature_flag_service.set_enabled("net_worth", True, actor_id=None)


def test_feature_flags_endpoint_lists_shipped_flags_enabled(client):
    headers = auth_headers(client)
    response = client.get("/api/feature-flags", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["net_worth"] is True
    assert data["receipt_scanner"] is True
    assert data["ai_assistant"] is False  # not built yet, stays off
