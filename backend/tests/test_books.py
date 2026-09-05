from conftest import auth_headers


def test_registration_creates_a_default_book(client):
    headers = auth_headers(client)
    books = client.get("/api/books", headers=headers).get_json()

    assert len(books) == 1
    assert books[0]["name"] == "My Book"
    assert books[0]["type"] == "personal"
    assert books[0]["is_default"] is True


def test_books_require_authentication(client):
    assert client.get("/api/books").status_code == 401


def test_create_update_and_set_default_book(client):
    headers = auth_headers(client)

    response = client.post("/api/books", json={"name": "Shop", "type": "business"}, headers=headers)
    assert response.status_code == 201
    book = response.get_json()["book"]
    assert book["type"] == "business"
    # The first book was already the default, so a second one isn't.
    assert book["is_default"] is False

    response = client.put(
        f"/api/books/{book['id']}", json={"name": "Main Shop", "type": "daily"}, headers=headers
    )
    assert response.status_code == 200
    assert response.get_json()["book"]["name"] == "Main Shop"

    response = client.post(f"/api/books/{book['id']}/default", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["book"]["is_default"] is True

    # Exactly one default at a time.
    books = client.get("/api/books", headers=headers).get_json()
    assert [b["is_default"] for b in books].count(True) == 1


def test_create_book_rejects_invalid_type(client):
    headers = auth_headers(client)
    response = client.post("/api/books", json={"name": "Nope", "type": "spaceship"}, headers=headers)
    assert response.status_code == 400


def test_create_book_rejects_duplicate_name(client):
    headers = auth_headers(client)
    client.post("/api/books", json={"name": "Shop"}, headers=headers)
    response = client.post("/api/books", json={"name": "Shop"}, headers=headers)
    assert response.status_code == 409


def test_cannot_delete_the_last_remaining_book(client):
    headers = auth_headers(client)
    books = client.get("/api/books", headers=headers).get_json()

    response = client.delete(f"/api/books/{books[0]['id']}", headers=headers)
    assert response.status_code == 400
    assert "only book" in response.get_json()["error"]

    # Still there.
    assert len(client.get("/api/books", headers=headers).get_json()) == 1


def test_deleting_a_book_is_allowed_once_a_second_one_exists(client):
    headers = auth_headers(client)
    second = client.post("/api/books", json={"name": "Shop"}, headers=headers).get_json()["book"]

    assert client.delete(f"/api/books/{second['id']}", headers=headers).status_code == 200
    assert len(client.get("/api/books", headers=headers).get_json()) == 1


def test_deleting_the_default_book_hands_the_flag_to_a_survivor(client):
    headers = auth_headers(client)
    second = client.post("/api/books", json={"name": "Shop"}, headers=headers).get_json()["book"]
    client.post(f"/api/books/{second['id']}/default", headers=headers)

    assert client.delete(f"/api/books/{second['id']}", headers=headers).status_code == 200

    books = client.get("/api/books", headers=headers).get_json()
    assert len(books) == 1
    assert books[0]["is_default"] is True


def test_user_cannot_touch_another_users_book(client):
    alice = auth_headers(client, name="Alice", email="alice@example.com")
    alice_book = client.post("/api/books", json={"name": "Shop"}, headers=alice).get_json()["book"]

    bob = auth_headers(client, name="Bob", email="bob@example.com")

    assert client.put(f"/api/books/{alice_book['id']}", json={"name": "Hijacked"}, headers=bob).status_code == 404
    assert client.post(f"/api/books/{alice_book['id']}/default", headers=bob).status_code == 404
    assert client.delete(f"/api/books/{alice_book['id']}", headers=bob).status_code == 404

    # Bob only ever sees his own book, and Alice's is untouched.
    assert [b["name"] for b in client.get("/api/books", headers=bob).get_json()] == ["My Book"]
    assert "Shop" in [b["name"] for b in client.get("/api/books", headers=alice).get_json()]
