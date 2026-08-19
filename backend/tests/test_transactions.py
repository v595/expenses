from conftest import auth_headers, register

SAMPLE_TRANSACTION = {
    "amount": 500,
    "type": "expense",
    "category": "Food",
    "description": "Lunch",
    "date": "2026-08-19",
}


def test_create_transaction(client):
    headers = auth_headers(client)
    response = client.post("/api/transactions", json=SAMPLE_TRANSACTION, headers=headers)
    assert response.status_code == 201
    transaction = response.get_json()["transaction"]
    assert transaction["amount"] == 500
    assert transaction["category"] == "Food"


def test_create_transaction_invalid_amount_rejected(client):
    headers = auth_headers(client)
    bad = {**SAMPLE_TRANSACTION, "amount": -5}
    response = client.post("/api/transactions", json=bad, headers=headers)
    assert response.status_code == 400


def test_create_transaction_invalid_type_rejected(client):
    headers = auth_headers(client)
    bad = {**SAMPLE_TRANSACTION, "type": "savings"}
    response = client.post("/api/transactions", json=bad, headers=headers)
    assert response.status_code == 400


def test_transactions_require_authentication(client):
    response = client.get("/api/transactions")
    assert response.status_code == 401


def test_read_update_delete_flow(client):
    headers = auth_headers(client)
    created = client.post(
        "/api/transactions", json=SAMPLE_TRANSACTION, headers=headers
    ).get_json()["transaction"]
    txn_id = created["id"]

    # Read
    response = client.get(f"/api/transactions/{txn_id}", headers=headers)
    assert response.status_code == 200

    # Update
    updated = {**SAMPLE_TRANSACTION, "amount": 750}
    response = client.put(f"/api/transactions/{txn_id}", json=updated, headers=headers)
    assert response.status_code == 200
    assert response.get_json()["transaction"]["amount"] == 750

    # Delete
    response = client.delete(f"/api/transactions/{txn_id}", headers=headers)
    assert response.status_code == 200

    # Confirm it's gone
    response = client.get(f"/api/transactions/{txn_id}", headers=headers)
    assert response.status_code == 404


def test_user_cannot_access_another_users_transaction(client):
    alice_headers = auth_headers(client, name="Alice", email="alice@example.com")
    created = client.post(
        "/api/transactions", json=SAMPLE_TRANSACTION, headers=alice_headers
    ).get_json()["transaction"]
    txn_id = created["id"]

    bob_headers = auth_headers(client, name="Bob", email="bob@example.com")

    assert client.get(f"/api/transactions/{txn_id}", headers=bob_headers).status_code == 404
    assert (
        client.put(f"/api/transactions/{txn_id}", json=SAMPLE_TRANSACTION, headers=bob_headers).status_code
        == 404
    )
    assert client.delete(f"/api/transactions/{txn_id}", headers=bob_headers).status_code == 404

    # Alice's transaction is untouched
    assert client.get(f"/api/transactions/{txn_id}", headers=alice_headers).status_code == 200
