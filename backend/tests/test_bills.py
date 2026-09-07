from conftest import auth_headers


def test_create_update_and_delete_bill(client):
    headers = auth_headers(client)
    response = client.post(
        "/api/bills",
        json={"name": "Electricity", "amount": 100, "due_date": "2026-01-15", "bill_type": "electricity"},
        headers=headers,
    )
    assert response.status_code == 201
    bill_id = response.get_json()["bill"]["id"]

    response = client.put(
        f"/api/bills/{bill_id}",
        json={
            "name": "Electricity (revised)",
            "amount": 120,
            "due_date": "2026-01-20",
            "repeat_frequency": "monthly",
            "bill_type": "electricity",
        },
        headers=headers,
    )
    assert response.status_code == 200
    updated = response.get_json()["bill"]
    assert updated["name"] == "Electricity (revised)"
    assert updated["amount"] == 120
    assert updated["repeat_frequency"] == "monthly"

    response = client.delete(f"/api/bills/{bill_id}", headers=headers)
    assert response.status_code == 200
    assert client.get("/api/bills", headers=headers).get_json() == []


def test_update_bill_not_found(client):
    headers = auth_headers(client)
    response = client.put(
        "/api/bills/999",
        json={"name": "Ghost", "amount": 10, "due_date": "2026-01-01"},
        headers=headers,
    )
    assert response.status_code == 400


def test_update_bill_rejects_invalid_type(client):
    headers = auth_headers(client)
    created = client.post(
        "/api/bills", json={"name": "Rent", "amount": 500, "due_date": "2026-01-01"}, headers=headers
    )
    bill_id = created.get_json()["bill"]["id"]

    response = client.put(
        f"/api/bills/{bill_id}",
        json={"name": "Rent", "amount": 500, "due_date": "2026-01-01", "bill_type": "not-a-type"},
        headers=headers,
    )
    assert response.status_code == 400
