from datetime import datetime, timezone

from conftest import auth_headers


def this_month_date(day="05"):
    return f"{datetime.now(timezone.utc).strftime('%Y-%m')}-{day}"


def test_set_and_list_budget_with_spending(client):
    headers = auth_headers(client)

    client.post("/api/budgets", json={"category": "Food", "monthly_limit": 500}, headers=headers)
    client.post(
        "/api/transactions",
        json={"amount": 150, "type": "expense", "category": "Food", "date": this_month_date()},
        headers=headers,
    )

    response = client.get("/api/budgets", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data == [{"category": "Food", "monthly_limit": 500, "spent": 150}]


def test_set_budget_upserts_on_same_category(client):
    headers = auth_headers(client)

    client.post("/api/budgets", json={"category": "Food", "monthly_limit": 500}, headers=headers)
    client.post("/api/budgets", json={"category": "Food", "monthly_limit": 800}, headers=headers)

    response = client.get("/api/budgets", headers=headers)
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["monthly_limit"] == 800


def test_set_budget_rejects_invalid_limit(client):
    headers = auth_headers(client)
    response = client.post(
        "/api/budgets", json={"category": "Food", "monthly_limit": -10}, headers=headers
    )
    assert response.status_code == 400


def test_delete_budget(client):
    headers = auth_headers(client)
    client.post("/api/budgets", json={"category": "Food", "monthly_limit": 500}, headers=headers)

    response = client.delete("/api/budgets/Food", headers=headers)
    assert response.status_code == 200

    response = client.get("/api/budgets", headers=headers)
    assert response.get_json() == []


def test_budgets_require_authentication(client):
    response = client.get("/api/budgets")
    assert response.status_code == 401
