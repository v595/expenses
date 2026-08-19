from conftest import auth_headers


def test_dashboard_summary_calculations(client):
    headers = auth_headers(client)

    client.post(
        "/api/transactions",
        json={"amount": 1000, "type": "income", "category": "Salary", "date": "2026-08-01"},
        headers=headers,
    )
    client.post(
        "/api/transactions",
        json={"amount": 100, "type": "expense", "category": "Food", "date": "2026-08-02"},
        headers=headers,
    )
    client.post(
        "/api/transactions",
        json={"amount": 50, "type": "expense", "category": "Food", "date": "2026-08-03"},
        headers=headers,
    )

    response = client.get("/api/dashboard/summary", headers=headers)
    assert response.status_code == 200
    data = response.get_json()

    assert data["income"] == 1000
    assert data["expenses"] == 150
    assert data["balance"] == 850
    assert data["transaction_count"] == 3
    assert data["top_category"]["category"] == "Food"
    assert data["top_category"]["total"] == 150


def test_dashboard_requires_authentication(client):
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 401


def test_dashboard_with_no_transactions_is_all_zero(client):
    headers = auth_headers(client)
    response = client.get("/api/dashboard/summary", headers=headers)
    data = response.get_json()
    assert data["income"] == 0
    assert data["expenses"] == 0
    assert data["balance"] == 0
    assert data["transaction_count"] == 0
    assert data["top_category"] is None
