"""Party reports: a single party's statement, and the book-wide
receivables/payables summary.

Both are just the one balance convention rolled up differently — positive is
"You'll get" (a receivable), negative is "You'll give" (a payable). See
`app.models.ledger_entry`."""

from datetime import datetime

from app.models import ledger_entry as ledger_entry_model
from app.models import party as party_model
from app.services import book_service, party_service


def _parse_date(value, field_label):
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_label} must be a date in YYYY-MM-DD format")
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"{field_label} must be a valid date in YYYY-MM-DD format")
    return value


def _validate_range(start_date, end_date):
    start_date = _parse_date(start_date, "Start date")
    end_date = _parse_date(end_date, "End date")
    if start_date and end_date and start_date > end_date:
        raise ValueError("Start date must be on or before end date")
    return start_date, end_date


def get_statement(party_id, user_id, start_date=None, end_date=None):
    """A party's account statement: what they owed coming into the window,
    every entry in it with a running balance, and where they end up."""
    party = party_service.require_party(party_id, user_id)
    start_date, end_date = _validate_range(start_date, end_date)

    opening_balance = 0.0
    if start_date:
        opening_balance = ledger_entry_model.get_balance_for_party(
            party["id"], user_id, before_date=start_date
        )

    entries = ledger_entry_model.get_entries_for_party(
        party["id"], user_id, start_date=start_date, end_date=end_date
    )

    running = opening_balance
    total_given = 0.0
    total_got = 0.0
    rows = []
    for entry in entries:
        running += ledger_entry_model.signed_amount(entry["amount"], entry["direction"])
        if entry["direction"] == ledger_entry_model.GIVEN:
            total_given += entry["amount"]
        else:
            total_got += entry["amount"]
        rows.append({**entry, "running_balance": round(running, 2)})

    return {
        "party": {
            "id": party["id"],
            "name": party["name"],
            "phone": party["phone"],
            "type": party["type"],
            "book_id": party["book_id"],
        },
        "start_date": start_date,
        "end_date": end_date,
        "opening_balance": round(opening_balance, 2),
        "closing_balance": round(running, 2),
        "total_given": round(total_given, 2),
        "total_got": round(total_got, 2),
        "entries": rows,
        **ledger_entry_model.describe_balance(running),
    }


def get_summary(user_id, book_id=None, start_date=None, end_date=None):
    """Receivables vs payables for a whole book.

    `you_will_get` sums the positive balances (parties who owe the user) and
    `you_will_give` the magnitude of the negative ones (parties the user
    owes), so both figures are reported as positive numbers and `net` is the
    difference."""
    book = book_service.resolve_book(book_id, user_id)
    start_date, end_date = _validate_range(start_date, end_date)

    parties = party_model.get_parties_by_user(user_id, book_id=book["id"])
    balances = ledger_entry_model.get_balances_for_parties(
        [p["id"] for p in parties], user_id, start_date=start_date, end_date=end_date
    )

    rows = []
    you_will_get = 0.0
    you_will_give = 0.0
    for party in parties:
        balance = balances.get(party["id"], 0.0)
        if balance > 0:
            you_will_get += balance
        elif balance < 0:
            you_will_give += -balance
        rows.append({**party, **ledger_entry_model.describe_balance(balance)})

    rows.sort(key=lambda r: -r["balance"])

    return {
        "book_id": book["id"],
        "book_name": book["name"],
        "start_date": start_date,
        "end_date": end_date,
        "you_will_get": round(you_will_get, 2),
        "you_will_give": round(you_will_give, 2),
        "net": round(you_will_get - you_will_give, 2),
        "party_count": len(rows),
        "parties": rows,
    }
