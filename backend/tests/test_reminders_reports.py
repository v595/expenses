import pytest

from conftest import auth_headers
from test_parties_ledger import add_entry, make_party


@pytest.fixture(autouse=True)
def default_messaging_driver(monkeypatch):
    monkeypatch.delenv("MESSAGING_DRIVER", raising=False)


def test_pending_dues_lists_only_parties_who_owe_the_user(client):
    headers = auth_headers(client)

    owes_me = make_party(client, headers, name="Ravi")
    add_entry(client, headers, owes_me["id"], 1000, "given", due_date="2020-01-01")

    i_owe_them = make_party(client, headers, name="Wholesaler", type_="supplier")
    add_entry(client, headers, i_owe_them["id"], 2000, "got")

    settled = make_party(client, headers, name="Meena")
    add_entry(client, headers, settled["id"], 300, "given")
    add_entry(client, headers, settled["id"], 300, "got")

    dues = client.get("/api/reminders/pending", headers=headers).get_json()
    assert [p["name"] for p in dues["parties"]] == ["Ravi"]
    assert dues["total_pending"] == 1000
    assert dues["parties"][0]["is_overdue"] is True


def test_pending_dues_can_be_narrowed_to_overdue_only(client):
    headers = auth_headers(client)

    overdue = make_party(client, headers, name="Ravi")
    add_entry(client, headers, overdue["id"], 500, "given", due_date="2020-01-01")

    not_yet_due = make_party(client, headers, name="Sunil")
    add_entry(client, headers, not_yet_due["id"], 700, "given", due_date="2099-01-01")

    everyone = client.get("/api/reminders/pending", headers=headers).get_json()
    assert sorted(p["name"] for p in everyone["parties"]) == ["Ravi", "Sunil"]

    only_overdue = client.get("/api/reminders/pending?overdue_only=true", headers=headers).get_json()
    assert [p["name"] for p in only_overdue["parties"]] == ["Ravi"]


def test_create_reminder_returns_a_wa_me_link_and_stays_pending(client):
    headers = auth_headers(client)
    party = make_party(client, headers, name="Ravi", phone="+91 98765 43210")
    add_entry(client, headers, party["id"], 1500, "given")

    response = client.post("/api/reminders", json={"party_id": party["id"]}, headers=headers)
    assert response.status_code == 201
    reminder = response.get_json()["reminder"]

    assert reminder["channel"] == "whatsapp"
    assert reminder["driver"] == "wa_link"
    assert reminder["status"] == "pending"
    assert reminder["requires_user_action"] is True
    assert reminder["link"].startswith("https://wa.me/919876543210?text=")
    assert "Ravi" in reminder["message"] and "1,500.00" in reminder["message"]

    # Marking sent is a deliberate second step.
    response = client.post(f"/api/reminders/{reminder['id']}/sent", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["reminder"]["status"] == "sent"
    assert response.get_json()["reminder"]["sent_at"] is not None

    history = client.get("/api/reminders", headers=headers).get_json()
    assert len(history) == 1
    assert history[0]["status"] == "sent"
    assert history[0]["party_name"] == "Ravi"


def test_create_reminder_accepts_a_custom_message(client):
    headers = auth_headers(client)
    party = make_party(client, headers)
    add_entry(client, headers, party["id"], 100, "given")

    response = client.post(
        "/api/reminders",
        json={"party_id": party["id"], "message": "Bhai, payment please"},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.get_json()["reminder"]["message"] == "Bhai, payment please"


def test_create_reminder_rejects_a_party_with_nothing_pending(client):
    headers = auth_headers(client)
    party = make_party(client, headers)
    response = client.post("/api/reminders", json={"party_id": party["id"]}, headers=headers)
    assert response.status_code == 400


def test_create_reminder_needs_a_phone_number_for_whatsapp(client):
    headers = auth_headers(client)
    party = make_party(client, headers, phone=None)
    add_entry(client, headers, party["id"], 100, "given")

    response = client.post("/api/reminders", json={"party_id": party["id"]}, headers=headers)
    assert response.status_code == 400
    assert "phone" in response.get_json()["error"]


def test_reminder_via_unconfigured_twilio_surfaces_the_setup_error(client, monkeypatch):
    for env_var in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM"):
        monkeypatch.delenv(env_var, raising=False)
    monkeypatch.setenv("MESSAGING_DRIVER", "twilio")

    headers = auth_headers(client)
    party = make_party(client, headers)
    add_entry(client, headers, party["id"], 100, "given")

    response = client.post(
        "/api/reminders", json={"party_id": party["id"], "channel": "sms"}, headers=headers
    )
    assert response.status_code == 400
    assert "Twilio is not configured" in response.get_json()["error"]

    # The failed attempt is still recorded.
    history = client.get("/api/reminders", headers=headers).get_json()
    assert [r["status"] for r in history] == ["failed"]


def test_user_cannot_remind_or_read_reminders_for_another_users_party(client):
    alice = auth_headers(client, name="Alice", email="alice@example.com")
    party = make_party(client, alice)
    add_entry(client, alice, party["id"], 500, "given")
    reminder = client.post("/api/reminders", json={"party_id": party["id"]}, headers=alice).get_json()[
        "reminder"
    ]

    bob = auth_headers(client, name="Bob", email="bob@example.com")

    assert client.post("/api/reminders", json={"party_id": party["id"]}, headers=bob).status_code == 404
    assert client.post(f"/api/reminders/{reminder['id']}/sent", headers=bob).status_code == 404
    assert client.get("/api/reminders", headers=bob).get_json() == []
    assert client.get("/api/reminders/pending", headers=bob).get_json()["parties"] == []


def test_cashbook_groups_by_day_with_a_running_balance(client):
    headers = auth_headers(client)
    party = make_party(client, headers)

    add_entry(client, headers, party["id"], 1000, "given", date="2026-09-01")
    add_entry(client, headers, party["id"], 200, "got", date="2026-09-01")
    add_entry(client, headers, party["id"], 500, "got", date="2026-09-02")

    cashbook = client.get("/api/cashbook", headers=headers).get_json()
    assert cashbook["opening_balance"] == 0
    assert cashbook["closing_balance"] == 300
    assert cashbook["total_given"] == 1000
    assert cashbook["total_got"] == 700

    day_one, day_two = cashbook["days"]
    assert day_one["date"] == "2026-09-01"
    assert (day_one["given"], day_one["got"], day_one["net"]) == (1000, 200, 800)
    assert day_one["opening_balance"] == 0
    assert day_one["closing_balance"] == 800
    assert len(day_one["entries"]) == 2

    # Each day opens where the previous one closed.
    assert day_two["opening_balance"] == 800
    assert day_two["closing_balance"] == 300


def test_cashbook_start_date_becomes_the_opening_balance(client):
    headers = auth_headers(client)
    party = make_party(client, headers)
    add_entry(client, headers, party["id"], 1000, "given", date="2026-09-01")
    add_entry(client, headers, party["id"], 400, "got", date="2026-09-05")

    cashbook = client.get("/api/cashbook?start_date=2026-09-02", headers=headers).get_json()
    assert cashbook["opening_balance"] == 1000
    assert cashbook["closing_balance"] == 600
    assert [d["date"] for d in cashbook["days"]] == ["2026-09-05"]


def test_cashbook_and_reports_are_scoped_to_the_user(client):
    alice = auth_headers(client, name="Alice", email="alice@example.com")
    party = make_party(client, alice)
    add_entry(client, alice, party["id"], 1000, "given")

    bob = auth_headers(client, name="Bob", email="bob@example.com")
    assert client.get("/api/cashbook", headers=bob).get_json()["days"] == []
    assert client.get("/api/reports/parties/summary", headers=bob).get_json()["you_will_get"] == 0
    assert client.get(f"/api/reports/parties/{party['id']}/statement", headers=bob).status_code == 404


def test_receivables_payables_summary(client):
    headers = auth_headers(client)

    ravi = make_party(client, headers, name="Ravi")
    add_entry(client, headers, ravi["id"], 1000, "given")

    wholesaler = make_party(client, headers, name="Wholesaler", type_="supplier")
    add_entry(client, headers, wholesaler["id"], 2500, "got")
    add_entry(client, headers, wholesaler["id"], 500, "given")

    summary = client.get("/api/reports/parties/summary", headers=headers).get_json()
    assert summary["you_will_get"] == 1000
    assert summary["you_will_give"] == 2000
    assert summary["net"] == -1000
    assert summary["party_count"] == 2

    by_name = {p["name"]: p for p in summary["parties"]}
    assert by_name["Ravi"]["balance_direction"] == "you_will_get"
    assert by_name["Wholesaler"]["balance_direction"] == "you_will_give"


def test_party_statement_with_a_running_balance_and_date_range(client):
    headers = auth_headers(client)
    party = make_party(client, headers)
    add_entry(client, headers, party["id"], 1000, "given", date="2026-08-20")
    add_entry(client, headers, party["id"], 300, "got", date="2026-09-01")
    add_entry(client, headers, party["id"], 200, "got", date="2026-09-03")

    statement = client.get(
        f"/api/reports/parties/{party['id']}/statement?start_date=2026-09-01&end_date=2026-09-03",
        headers=headers,
    ).get_json()

    assert statement["opening_balance"] == 1000
    assert statement["total_got"] == 500
    assert statement["total_given"] == 0
    assert statement["closing_balance"] == 500
    assert statement["balance_direction"] == "you_will_get"
    assert [e["running_balance"] for e in statement["entries"]] == [700, 500]


def test_reports_reject_a_backwards_date_range(client):
    headers = auth_headers(client)
    response = client.get(
        "/api/reports/parties/summary?start_date=2026-09-10&end_date=2026-09-01", headers=headers
    )
    assert response.status_code == 400


def test_reminder_cashbook_and_report_routes_require_authentication(client):
    assert client.get("/api/reminders/pending").status_code == 401
    assert client.get("/api/reminders").status_code == 401
    assert client.post("/api/reminders", json={}).status_code == 401
    assert client.get("/api/cashbook").status_code == 401
    assert client.get("/api/reports/parties/summary").status_code == 401
