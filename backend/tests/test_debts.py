from conftest import auth_headers


def test_create_update_and_delete_debt(client):
    headers = auth_headers(client)
    response = client.post(
        "/api/debts",
        json={"name": "Credit Card", "balance": 5000, "interest_rate": 24, "min_payment": 150},
        headers=headers,
    )
    assert response.status_code == 201
    debt_id = response.get_json()["debt"]["id"]

    response = client.put(
        f"/api/debts/{debt_id}",
        json={"name": "Credit Card (paid down)", "balance": 4000, "interest_rate": 22, "min_payment": 150},
        headers=headers,
    )
    assert response.status_code == 200
    updated = response.get_json()["debt"]
    assert updated["balance"] == 4000
    assert updated["interest_rate"] == 22

    response = client.delete(f"/api/debts/{debt_id}", headers=headers)
    assert response.status_code == 200
    assert client.get("/api/debts", headers=headers).get_json() == []


def test_create_debt_rejects_min_payment_over_balance(client):
    headers = auth_headers(client)
    response = client.post(
        "/api/debts",
        json={"name": "Loan", "balance": 100, "interest_rate": 10, "min_payment": 500},
        headers=headers,
    )
    assert response.status_code == 400


def test_update_debt_not_found(client):
    headers = auth_headers(client)
    response = client.put(
        "/api/debts/999",
        json={"name": "Ghost", "balance": 100, "interest_rate": 10, "min_payment": 10},
        headers=headers,
    )
    assert response.status_code == 400


def test_payoff_plan_avalanche_prioritizes_highest_interest(client):
    headers = auth_headers(client)
    client.post(
        "/api/debts",
        json={"name": "Card A (low rate)", "balance": 1000, "interest_rate": 10, "min_payment": 50},
        headers=headers,
    )
    client.post(
        "/api/debts",
        json={"name": "Card B (high rate)", "balance": 1000, "interest_rate": 25, "min_payment": 50},
        headers=headers,
    )

    response = client.post(
        "/api/debts/payoff-plan",
        json={"extra_payment": 200, "strategy": "avalanche"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["months_to_debt_free"] > 0

    by_name = {d["name"]: d for d in data["debts"]}
    # The higher-rate card should get the extra payment first and finish sooner.
    assert by_name["Card B (high rate)"]["payoff_month"] <= by_name["Card A (low rate)"]["payoff_month"]


def test_payoff_plan_snowball_prioritizes_smallest_balance(client):
    headers = auth_headers(client)
    client.post(
        "/api/debts",
        json={"name": "Big Balance", "balance": 5000, "interest_rate": 15, "min_payment": 100},
        headers=headers,
    )
    client.post(
        "/api/debts",
        json={"name": "Small Balance", "balance": 500, "interest_rate": 15, "min_payment": 50},
        headers=headers,
    )

    response = client.post(
        "/api/debts/payoff-plan",
        json={"extra_payment": 200, "strategy": "snowball"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.get_json()
    by_name = {d["name"]: d for d in data["debts"]}
    assert by_name["Small Balance"]["payoff_month"] < by_name["Big Balance"]["payoff_month"]


def test_payoff_plan_with_no_debts(client):
    headers = auth_headers(client)
    response = client.post(
        "/api/debts/payoff-plan", json={"extra_payment": 100, "strategy": "avalanche"}, headers=headers
    )
    assert response.status_code == 200
    assert response.get_json()["months_to_debt_free"] == 0


def test_payoff_plan_rejects_invalid_strategy(client):
    headers = auth_headers(client)
    response = client.post(
        "/api/debts/payoff-plan", json={"extra_payment": 100, "strategy": "bogus"}, headers=headers
    )
    assert response.status_code == 400
