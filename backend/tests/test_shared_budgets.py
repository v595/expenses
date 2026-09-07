from conftest import auth_headers, register


def test_share_budget_and_see_it_from_the_other_account(client):
    owner_headers = auth_headers(client)  # alice@example.com
    client.post("/api/budgets", json={"category": "Groceries", "monthly_limit": 500}, headers=owner_headers)

    register(client, name="Bob", email="bob@example.com", password="secret123")
    bob_login = client.post(
        "/api/auth/login", json={"email": "bob@example.com", "password": "secret123"}
    )
    bob_headers = {"Authorization": f"Bearer {bob_login.get_json()['token']}"}

    response = client.post(
        "/api/budgets/Groceries/share", json={"email": "bob@example.com"}, headers=owner_headers
    )
    assert response.status_code == 201

    response = client.get("/api/budgets/shared-with-me", headers=bob_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["category"] == "Groceries"
    assert data[0]["monthly_limit"] == 500
    assert data[0]["owner_name"] == "Alice"


def test_shared_budget_reflects_owner_spending(client):
    owner_headers = auth_headers(client)
    client.post("/api/budgets", json={"category": "Groceries", "monthly_limit": 500}, headers=owner_headers)
    client.post(
        "/api/transactions",
        json={"amount": 120, "type": "expense", "category": "Groceries", "date": "2026-09-07"},
        headers=owner_headers,
    )

    register(client, name="Bob", email="bob@example.com", password="secret123")
    bob_login = client.post("/api/auth/login", json={"email": "bob@example.com", "password": "secret123"})
    bob_headers = {"Authorization": f"Bearer {bob_login.get_json()['token']}"}

    client.post("/api/budgets/Groceries/share", json={"email": "bob@example.com"}, headers=owner_headers)

    response = client.get("/api/budgets/shared-with-me", headers=bob_headers)
    assert response.get_json()[0]["spent"] == 120


def test_share_rejects_unknown_email(client):
    headers = auth_headers(client)
    client.post("/api/budgets", json={"category": "Groceries", "monthly_limit": 500}, headers=headers)

    response = client.post(
        "/api/budgets/Groceries/share", json={"email": "nobody@example.com"}, headers=headers
    )
    assert response.status_code == 404


def test_share_rejects_self(client):
    headers = auth_headers(client)
    client.post("/api/budgets", json={"category": "Groceries", "monthly_limit": 500}, headers=headers)

    response = client.post(
        "/api/budgets/Groceries/share", json={"email": "alice@example.com"}, headers=headers
    )
    assert response.status_code == 400


def test_share_rejects_duplicate(client):
    headers = auth_headers(client)
    client.post("/api/budgets", json={"category": "Groceries", "monthly_limit": 500}, headers=headers)
    register(client, name="Bob", email="bob@example.com", password="secret123")

    client.post("/api/budgets/Groceries/share", json={"email": "bob@example.com"}, headers=headers)
    response = client.post(
        "/api/budgets/Groceries/share", json={"email": "bob@example.com"}, headers=headers
    )
    assert response.status_code == 409


def test_unshare_budget(client):
    owner_headers = auth_headers(client)
    client.post("/api/budgets", json={"category": "Groceries", "monthly_limit": 500}, headers=owner_headers)
    register(client, name="Bob", email="bob@example.com", password="secret123")
    bob_login = client.post("/api/auth/login", json={"email": "bob@example.com", "password": "secret123"})
    bob_headers = {"Authorization": f"Bearer {bob_login.get_json()['token']}"}
    bob_id = client.get("/api/auth/me", headers=bob_headers).get_json()["user"]["id"]

    client.post("/api/budgets/Groceries/share", json={"email": "bob@example.com"}, headers=owner_headers)
    response = client.delete(f"/api/budgets/Groceries/share/{bob_id}", headers=owner_headers)
    assert response.status_code == 200

    assert client.get("/api/budgets/shared-with-me", headers=bob_headers).get_json() == []


def test_shared_with_me_empty_by_default(client):
    headers = auth_headers(client)
    response = client.get("/api/budgets/shared-with-me", headers=headers)
    assert response.get_json() == []


def test_deleting_shared_with_user_does_not_break_owner(client):
    """Regression: deleting the account a budget was shared with used to
    leave an orphan budget_shares row — make sure the cascade clears it and
    the owner's own budget listing still works fine afterward."""
    owner_headers = auth_headers(client)
    client.post("/api/budgets", json={"category": "Groceries", "monthly_limit": 500}, headers=owner_headers)
    register(client, name="Bob", email="bob@example.com", password="secret123")
    bob_login = client.post("/api/auth/login", json={"email": "bob@example.com", "password": "secret123"})
    bob_headers = {"Authorization": f"Bearer {bob_login.get_json()['token']}"}

    client.post("/api/budgets/Groceries/share", json={"email": "bob@example.com"}, headers=owner_headers)

    response = client.delete("/api/settings/account", headers=bob_headers)
    assert response.status_code == 200

    response = client.get("/api/budgets", headers=owner_headers)
    assert response.status_code == 200
    assert response.get_json()[0]["category"] == "Groceries"


def test_deleting_owner_does_not_break_shared_with_user(client):
    owner_headers = auth_headers(client)
    client.post("/api/budgets", json={"category": "Groceries", "monthly_limit": 500}, headers=owner_headers)
    register(client, name="Bob", email="bob@example.com", password="secret123")
    bob_login = client.post("/api/auth/login", json={"email": "bob@example.com", "password": "secret123"})
    bob_headers = {"Authorization": f"Bearer {bob_login.get_json()['token']}"}

    client.post("/api/budgets/Groceries/share", json={"email": "bob@example.com"}, headers=owner_headers)

    response = client.delete("/api/settings/account", headers=owner_headers)
    assert response.status_code == 200

    response = client.get("/api/budgets/shared-with-me", headers=bob_headers)
    assert response.status_code == 200
    assert response.get_json() == []


def test_share_nonexistent_budget(client):
    headers = auth_headers(client)
    register(client, name="Bob", email="bob@example.com", password="secret123")
    response = client.post(
        "/api/budgets/Nope/share", json={"email": "bob@example.com"}, headers=headers
    )
    assert response.status_code == 404
