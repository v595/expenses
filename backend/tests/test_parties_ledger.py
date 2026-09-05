from conftest import auth_headers


def make_party(client, headers, name="Ravi", type_="customer", phone="+91 98765 43210"):
    response = client.post(
        "/api/parties", json={"name": name, "type": type_, "phone": phone}, headers=headers
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["party"]


def add_entry(client, headers, party_id, amount, direction, date="2026-09-01", **extra):
    response = client.post(
        "/api/ledger",
        json={"party_id": party_id, "amount": amount, "direction": direction, "date": date, **extra},
        headers=headers,
    )
    assert response.status_code == 201, response.get_json()
    return response.get_json()["entry"]


def test_party_lands_in_the_default_book_with_a_zero_balance(client):
    headers = auth_headers(client)
    default_book = client.get("/api/books", headers=headers).get_json()[0]

    party = make_party(client, headers)
    assert party["book_id"] == default_book["id"]
    assert party["balance"] == 0
    assert party["balance_direction"] == "settled"
    # Phone is normalised to digits with a single leading '+'.
    assert party["phone"] == "+919876543210"


def test_positive_balance_means_you_will_get(client):
    """`given` to a customer = goods/credit handed over, so they owe you."""
    headers = auth_headers(client)
    party = make_party(client, headers)

    add_entry(client, headers, party["id"], 1000, "given")
    add_entry(client, headers, party["id"], 400, "got")

    detail = client.get(f"/api/parties/{party['id']}", headers=headers).get_json()
    assert detail["balance"] == 600
    assert detail["balance_direction"] == "you_will_get"
    assert detail["balance_label"] == "You'll get"
    assert detail["balance_abs"] == 600
    assert len(detail["entries"]) == 2


def test_negative_balance_means_you_will_give(client):
    """The mirror case: more came in than went out, so you owe the party."""
    headers = auth_headers(client)
    party = make_party(client, headers, name="Wholesaler", type_="supplier")

    add_entry(client, headers, party["id"], 2000, "got")
    add_entry(client, headers, party["id"], 750, "given")

    detail = client.get(f"/api/parties/{party['id']}", headers=headers).get_json()
    assert detail["balance"] == -1250
    assert detail["balance_direction"] == "you_will_give"
    assert detail["balance_label"] == "You'll give"
    assert detail["balance_abs"] == 1250


def test_balance_returns_to_settled_when_fully_paid(client):
    headers = auth_headers(client)
    party = make_party(client, headers)

    add_entry(client, headers, party["id"], 500, "given")
    add_entry(client, headers, party["id"], 500, "got")

    listed = client.get("/api/parties", headers=headers).get_json()
    assert listed[0]["balance"] == 0
    assert listed[0]["balance_direction"] == "settled"


def test_parties_can_be_filtered_by_type(client):
    headers = auth_headers(client)
    make_party(client, headers, name="Ravi", type_="customer")
    make_party(client, headers, name="Wholesaler", type_="supplier")

    customers = client.get("/api/parties?type=customer", headers=headers).get_json()
    assert [p["name"] for p in customers] == ["Ravi"]

    assert client.get("/api/parties?type=alien", headers=headers).status_code == 400


def test_party_validation_and_duplicates(client):
    headers = auth_headers(client)
    make_party(client, headers, name="Ravi")

    assert client.post("/api/parties", json={"name": "X", "type": "vendor"}, headers=headers).status_code == 400
    assert client.post("/api/parties", json={"name": "", "type": "customer"}, headers=headers).status_code == 400

    duplicate = client.post("/api/parties", json={"name": "Ravi", "type": "customer"}, headers=headers)
    assert duplicate.status_code == 409


def test_ledger_entry_update_and_delete_move_the_balance(client):
    headers = auth_headers(client)
    party = make_party(client, headers)
    entry = add_entry(client, headers, party["id"], 1000, "given")

    response = client.put(
        f"/api/ledger/{entry['id']}",
        json={"amount": 250, "direction": "got", "date": "2026-09-02"},
        headers=headers,
    )
    assert response.status_code == 200

    detail = client.get(f"/api/parties/{party['id']}", headers=headers).get_json()
    assert detail["balance"] == -250

    assert client.delete(f"/api/ledger/{entry['id']}", headers=headers).status_code == 200
    detail = client.get(f"/api/parties/{party['id']}", headers=headers).get_json()
    assert detail["balance"] == 0


def test_ledger_entry_validation(client):
    headers = auth_headers(client)
    party = make_party(client, headers)

    for bad in (
        {"party_id": party["id"], "amount": 0, "direction": "given", "date": "2026-09-01"},
        {"party_id": party["id"], "amount": -5, "direction": "given", "date": "2026-09-01"},
        {"party_id": party["id"], "amount": 10, "direction": "sideways", "date": "2026-09-01"},
        {"party_id": party["id"], "amount": 10, "direction": "given", "date": "01-09-2026"},
        {"party_id": party["id"], "amount": 10, "direction": "given"},
        {"amount": 10, "direction": "given", "date": "2026-09-01"},
    ):
        assert client.post("/api/ledger", json=bad, headers=headers).status_code == 400, bad


def test_ledger_listing_requires_a_party(client):
    headers = auth_headers(client)
    assert client.get("/api/ledger", headers=headers).status_code == 400


def test_user_cannot_reach_another_users_party_or_ledger(client):
    alice = auth_headers(client, name="Alice", email="alice@example.com")
    party = make_party(client, alice)
    entry = add_entry(client, alice, party["id"], 900, "given")

    bob = auth_headers(client, name="Bob", email="bob@example.com")

    # Party: invisible, unreadable, unmodifiable — 404 rather than 403.
    assert client.get("/api/parties", headers=bob).get_json() == []
    assert client.get(f"/api/parties/{party['id']}", headers=bob).status_code == 404
    assert client.put(
        f"/api/parties/{party['id']}", json={"name": "Hijacked", "type": "customer"}, headers=bob
    ).status_code == 404
    assert client.delete(f"/api/parties/{party['id']}", headers=bob).status_code == 404

    # Ledger: can't list, can't append to, can't edit or delete.
    assert client.get(f"/api/ledger?party_id={party['id']}", headers=bob).status_code == 404
    assert client.post(
        "/api/ledger",
        json={"party_id": party["id"], "amount": 1, "direction": "got", "date": "2026-09-01"},
        headers=bob,
    ).status_code == 404
    assert client.put(
        f"/api/ledger/{entry['id']}",
        json={"amount": 1, "direction": "got", "date": "2026-09-01"},
        headers=bob,
    ).status_code == 404
    assert client.delete(f"/api/ledger/{entry['id']}", headers=bob).status_code == 404

    # Alice's ledger is exactly as she left it.
    detail = client.get(f"/api/parties/{party['id']}", headers=alice).get_json()
    assert detail["balance"] == 900
    assert len(detail["entries"]) == 1


def test_deleting_a_party_removes_its_ledger(client):
    headers = auth_headers(client)
    party = make_party(client, headers)
    entry = add_entry(client, headers, party["id"], 100, "given")

    assert client.delete(f"/api/parties/{party['id']}", headers=headers).status_code == 200
    assert client.get(f"/api/parties/{party['id']}", headers=headers).status_code == 404
    assert client.delete(f"/api/ledger/{entry['id']}", headers=headers).status_code == 404


def test_parties_and_ledger_require_authentication(client):
    assert client.get("/api/parties").status_code == 401
    assert client.get("/api/ledger?party_id=1").status_code == 401
    assert client.post("/api/ledger", json={}).status_code == 401
