from datetime import datetime

from app.models import activity_log as activity_log_model
from app.models import ledger_entry as ledger_entry_model
from app.models import party as party_model
from app.services.errors import not_found

VALID_DIRECTIONS = ledger_entry_model.VALID_DIRECTIONS
MAX_DESCRIPTION_LENGTH = 255


def _parse_date(value, field_label, required=True):
    if value is None or value == "":
        if required:
            raise ValueError(f"{field_label} is required")
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_label} must be a date in YYYY-MM-DD format")
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"{field_label} must be a valid date in YYYY-MM-DD format")
    return value


def _validate(data):
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")

    amount = data.get("amount")
    if not isinstance(amount, (int, float)) or isinstance(amount, bool):
        raise ValueError("Amount must be a number")
    if amount <= 0:
        raise ValueError("Amount must be greater than zero")

    direction = data.get("direction")
    if direction not in VALID_DIRECTIONS:
        raise ValueError("Direction must be 'given' or 'got'")

    description = data.get("description") or ""
    if not isinstance(description, str):
        raise ValueError("Description must be text")
    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise ValueError(f"Description must be {MAX_DESCRIPTION_LENGTH} characters or fewer")

    date = _parse_date(data.get("date"), "Date")
    due_date = _parse_date(data.get("due_date"), "Due date", required=False)

    return {
        "amount": float(amount),
        "direction": direction,
        "description": description.strip(),
        "date": date,
        "due_date": due_date,
    }


def _require_party(party_id, user_id):
    """Ledger entries inherit their user and book from the party, so this is
    also the ownership check: another user's party is simply not found."""
    if not isinstance(party_id, int) or isinstance(party_id, bool):
        raise ValueError("Party id is required")
    party = party_model.get_party_by_id(party_id, user_id)
    if party is None:
        raise not_found("Party not found")
    return party


def _describe(entry, party):
    return {**entry, "party_name": party["name"], "party_type": party["type"]}


def get_entries(party_id, user_id, start_date=None, end_date=None):
    party = _require_party(party_id, user_id)
    start_date = _parse_date(start_date, "Start date", required=False)
    end_date = _parse_date(end_date, "End date", required=False)

    entries = ledger_entry_model.get_entries_for_party(
        party["id"], user_id, start_date=start_date, end_date=end_date
    )
    balance = ledger_entry_model.get_balance_for_party(party["id"], user_id)
    return {
        "party_id": party["id"],
        "party_name": party["name"],
        "party_type": party["type"],
        "book_id": party["book_id"],
        "entries": entries,
        **ledger_entry_model.describe_balance(balance),
    }


def create_entry(user_id, data):
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")

    party = _require_party(data.get("party_id"), user_id)
    clean = _validate(data)

    entry = ledger_entry_model.create_entry(
        user_id,
        party["book_id"],
        party["id"],
        clean["amount"],
        clean["direction"],
        clean["description"],
        clean["date"],
        clean["due_date"],
    )
    activity_log_model.log(
        user_id,
        "Created ledger entry",
        f"{party['name']}: {clean['direction']} {clean['amount']:.2f}",
    )
    return _describe(entry, party)


def update_entry(entry_id, user_id, data):
    existing = ledger_entry_model.get_entry_by_id(entry_id, user_id)
    if existing is None:
        raise not_found("Ledger entry not found")

    clean = _validate(data)
    party = _require_party(existing["party_id"], user_id)

    updated = ledger_entry_model.update_entry(
        entry_id,
        user_id,
        clean["amount"],
        clean["direction"],
        clean["description"],
        clean["date"],
        clean["due_date"],
    )
    activity_log_model.log(
        user_id,
        "Updated ledger entry",
        f"{party['name']}: {clean['direction']} {clean['amount']:.2f}",
    )
    return _describe(updated, party)


def delete_entry(entry_id, user_id):
    existing = ledger_entry_model.get_entry_by_id(entry_id, user_id)
    if existing is None:
        raise not_found("Ledger entry not found")

    ledger_entry_model.delete_entry(entry_id, user_id)
    activity_log_model.log(
        user_id,
        "Deleted ledger entry",
        f"{existing['direction']} {existing['amount']:.2f}",
    )
    return True
