from conftest import auth_headers


def _add_transaction(client, headers, date, amount=499, description="Netflix", category="Entertainment"):
    return client.post(
        "/api/transactions",
        json={
            "amount": amount,
            "type": "expense",
            "category": category,
            "description": description,
            "date": date,
        },
        headers=headers,
    )


def test_detects_recurring_charge_across_months(client):
    headers = auth_headers(client)
    _add_transaction(client, headers, "2026-01-05")
    _add_transaction(client, headers, "2026-02-05")
    _add_transaction(client, headers, "2026-03-05")

    response = client.get("/api/dashboard/subscriptions", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["description"] == "Netflix"
    assert data[0]["times_seen"] == 3
    assert data[0]["months_seen"] == 3
    assert data[0]["amount"] == 499
    assert data[0]["estimated_yearly_cost"] == 499 * 12


def test_single_occurrence_not_flagged(client):
    headers = auth_headers(client)
    _add_transaction(client, headers, "2026-01-05")

    response = client.get("/api/dashboard/subscriptions", headers=headers)
    assert response.get_json() == []


def test_already_tracked_recurring_not_flagged(client):
    headers = auth_headers(client)
    _add_transaction(client, headers, "2026-01-05")
    _add_transaction(client, headers, "2026-02-05")

    client.post(
        "/api/recurring",
        json={
            "amount": 499,
            "type": "expense",
            "category": "Entertainment",
            "frequency": "monthly",
            "start_date": "2026-03-05",
        },
        headers=headers,
    )

    response = client.get("/api/dashboard/subscriptions", headers=headers)
    assert response.get_json() == []


def test_different_amounts_under_same_description_not_merged(client):
    headers = auth_headers(client)
    _add_transaction(client, headers, "2026-01-05", amount=499)
    _add_transaction(client, headers, "2026-02-05", amount=1200)

    response = client.get("/api/dashboard/subscriptions", headers=headers)
    # Neither cluster has 2 occurrences on its own, so nothing is flagged.
    assert response.get_json() == []


def test_no_description_transactions_ignored(client):
    headers = auth_headers(client)
    _add_transaction(client, headers, "2026-01-05", description="")
    _add_transaction(client, headers, "2026-02-05", description="")

    response = client.get("/api/dashboard/subscriptions", headers=headers)
    assert response.get_json() == []
