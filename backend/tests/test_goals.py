from conftest import auth_headers


def test_create_update_and_delete_goal(client):
    headers = auth_headers(client)
    response = client.post(
        "/api/goals",
        json={"name": "Emergency Fund", "target_amount": 1000, "target_date": "2026-12-31"},
        headers=headers,
    )
    assert response.status_code == 201
    goal_id = response.get_json()["goal"]["id"]

    response = client.put(
        f"/api/goals/{goal_id}",
        json={"name": "Emergency Fund v2", "target_amount": 1500, "target_date": "2027-01-31"},
        headers=headers,
    )
    assert response.status_code == 200
    updated = response.get_json()["goal"]
    assert updated["name"] == "Emergency Fund v2"
    assert updated["target_amount"] == 1500

    response = client.delete(f"/api/goals/{goal_id}", headers=headers)
    assert response.status_code == 200
    assert client.get("/api/goals", headers=headers).get_json() == []


def test_update_goal_not_found(client):
    headers = auth_headers(client)
    response = client.put(
        "/api/goals/999",
        json={"name": "Ghost", "target_amount": 100},
        headers=headers,
    )
    assert response.status_code == 400


def test_update_goal_rejects_zero_target(client):
    headers = auth_headers(client)
    created = client.post(
        "/api/goals", json={"name": "Trip", "target_amount": 500}, headers=headers
    )
    goal_id = created.get_json()["goal"]["id"]

    response = client.put(
        f"/api/goals/{goal_id}", json={"name": "Trip", "target_amount": 0}, headers=headers
    )
    assert response.status_code == 400
