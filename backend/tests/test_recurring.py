from datetime import date, timedelta

from conftest import auth_headers


def test_create_and_list_recurring(client):
    headers = auth_headers(client)
    response = client.post(
        "/api/recurring",
        json={
            "amount": 500,
            "type": "expense",
            "category": "Rent",
            "frequency": "monthly",
            "start_date": "2026-01-01",
        },
        headers=headers,
    )
    assert response.status_code == 201

    response = client.get("/api/recurring", headers=headers)
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["category"] == "Rent"
    assert data[0]["next_date"] == "2026-01-01"


def test_materializes_due_transaction_on_transaction_list(client):
    headers = auth_headers(client)
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    client.post(
        "/api/recurring",
        json={
            "amount": 200,
            "type": "expense",
            "category": "Subscription",
            "frequency": "weekly",
            "start_date": yesterday,
        },
        headers=headers,
    )

    response = client.get("/api/transactions", headers=headers)
    transactions = response.get_json()
    assert len(transactions) == 1
    assert transactions[0]["category"] == "Subscription"
    assert transactions[0]["date"] == yesterday

    # The rule's next_date should have advanced past today, so a second fetch
    # doesn't create a duplicate transaction for the same due date.
    response = client.get("/api/transactions", headers=headers)
    assert len(response.get_json()) == 1


def test_materializes_multiple_missed_occurrences(client):
    headers = auth_headers(client)
    three_weeks_ago = (date.today() - timedelta(days=21)).isoformat()
    client.post(
        "/api/recurring",
        json={
            "amount": 50,
            "type": "expense",
            "category": "Weekly Snack",
            "frequency": "weekly",
            "start_date": three_weeks_ago,
        },
        headers=headers,
    )

    response = client.get("/api/transactions", headers=headers)
    transactions = response.get_json()
    # 21, 14, and 7 days ago were missed, plus today's occurrence lands exactly on the cycle.
    assert len(transactions) == 4


def test_delete_recurring(client):
    headers = auth_headers(client)
    response = client.post(
        "/api/recurring",
        json={
            "amount": 500,
            "type": "income",
            "category": "Freelance",
            "frequency": "monthly",
            "start_date": "2099-01-01",
        },
        headers=headers,
    )
    recurring_id = response.get_json()["recurring"]["id"]

    response = client.delete(f"/api/recurring/{recurring_id}", headers=headers)
    assert response.status_code == 200
    assert client.get("/api/recurring", headers=headers).get_json() == []


def test_recurring_requires_authentication(client):
    response = client.get("/api/recurring")
    assert response.status_code == 401


def test_create_recurring_rejects_invalid_frequency(client):
    headers = auth_headers(client)
    response = client.post(
        "/api/recurring",
        json={
            "amount": 500,
            "type": "expense",
            "category": "Rent",
            "frequency": "daily",
            "start_date": "2026-01-01",
        },
        headers=headers,
    )
    assert response.status_code == 400
