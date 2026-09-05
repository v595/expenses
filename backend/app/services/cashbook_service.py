"""Day-wise cash view of a book.

Every figure here is the ledger sign convention applied over time: a day's
net is sum(given) - sum(got) for that day, and the running balance carries
forward, so the closing balance of one day is the opening balance of the
next. Positive still means "You'll get" — see
`app.models.ledger_entry.describe_balance`."""

from datetime import datetime

from app.models import ledger_entry as ledger_entry_model
from app.services import book_service


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


def get_cashbook(user_id, book_id=None, start_date=None, end_date=None):
    book = book_service.resolve_book(book_id, user_id)
    start_date = _parse_date(start_date, "Start date")
    end_date = _parse_date(end_date, "End date")
    if start_date and end_date and start_date > end_date:
        raise ValueError("Start date must be on or before end date")

    entries = ledger_entry_model.get_entries_for_book(
        book["id"], user_id, start_date=start_date, end_date=end_date
    )

    # Anything before the window is already history: it doesn't get its own
    # row, it just sets the opening balance the first shown day starts from.
    opening_balance = 0.0
    if start_date:
        opening_balance = ledger_entry_model.get_balance_for_book(
            book["id"], user_id, before_date=start_date
        )

    days = []
    running = opening_balance
    for entry in entries:
        if not days or days[-1]["date"] != entry["date"]:
            days.append(
                {
                    "date": entry["date"],
                    "opening_balance": round(running, 2),
                    "given": 0.0,
                    "got": 0.0,
                    "net": 0.0,
                    "closing_balance": round(running, 2),
                    "entries": [],
                }
            )

        day = days[-1]
        day["entries"].append(entry)
        if entry["direction"] == ledger_entry_model.GIVEN:
            day["given"] = round(day["given"] + entry["amount"], 2)
        else:
            day["got"] = round(day["got"] + entry["amount"], 2)

        running += ledger_entry_model.signed_amount(entry["amount"], entry["direction"])
        day["net"] = round(day["given"] - day["got"], 2)
        day["closing_balance"] = round(running, 2)

    return {
        "book_id": book["id"],
        "book_name": book["name"],
        "start_date": start_date,
        "end_date": end_date,
        "opening_balance": round(opening_balance, 2),
        "closing_balance": round(running, 2),
        "total_given": round(sum(d["given"] for d in days), 2),
        "total_got": round(sum(d["got"] for d in days), 2),
        "days": days,
        **ledger_entry_model.describe_balance(running),
    }
