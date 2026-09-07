from conftest import auth_headers


def test_create_update_and_delete_category(client):
    headers = auth_headers(client)
    response = client.post(
        "/api/categories",
        json={"name": "Groceries", "type": "expense", "color": "#4f46e5"},
        headers=headers,
    )
    assert response.status_code == 201
    category_id = response.get_json()["category"]["id"]

    response = client.put(
        f"/api/categories/{category_id}",
        json={"name": "Groceries & Household", "color": "#0891b2"},
        headers=headers,
    )
    assert response.status_code == 200
    updated = response.get_json()["category"]
    assert updated["name"] == "Groceries & Household"
    assert updated["color"] == "#0891b2"

    response = client.delete(f"/api/categories/{category_id}", headers=headers)
    assert response.status_code == 200
    assert client.get("/api/categories", headers=headers).get_json() == []


def test_update_category_not_found(client):
    headers = auth_headers(client)
    response = client.put(
        "/api/categories/999", json={"name": "Ghost"}, headers=headers
    )
    assert response.status_code == 400


def test_update_category_rejects_duplicate_name(client):
    headers = auth_headers(client)
    client.post("/api/categories", json={"name": "Rent", "type": "expense"}, headers=headers)
    second = client.post("/api/categories", json={"name": "Utilities", "type": "expense"}, headers=headers)
    second_id = second.get_json()["category"]["id"]

    response = client.put(
        f"/api/categories/{second_id}", json={"name": "Rent"}, headers=headers
    )
    assert response.status_code == 400
