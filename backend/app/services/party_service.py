from app.models import activity_log as activity_log_model
from app.models import ledger_entry as ledger_entry_model
from app.models import party as party_model
from app.models import reminder as reminder_model
from app.services import book_service
from app.services.errors import conflict, not_found
from app.services.messaging import normalize_phone

VALID_TYPES = ("customer", "supplier")
MAX_NAME_LENGTH = 80
MAX_NOTE_LENGTH = 255


def _validate(data):
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Name is required")
    if len(name.strip()) > MAX_NAME_LENGTH:
        raise ValueError(f"Name must be {MAX_NAME_LENGTH} characters or fewer")

    type_ = data.get("type")
    if type_ not in VALID_TYPES:
        raise ValueError("Type must be 'customer' or 'supplier'")

    phone_input = data.get("phone")
    if phone_input is not None and not isinstance(phone_input, str):
        raise ValueError("Phone must be text")
    phone = normalize_phone(phone_input)
    if phone_input and phone is None:
        raise ValueError("Phone must contain digits")
    if phone is not None and len(phone) > 20:
        raise ValueError("Phone number is too long")

    note = data.get("note") or None
    if note is not None and (not isinstance(note, str) or len(note) > MAX_NOTE_LENGTH):
        raise ValueError(f"Note must be {MAX_NOTE_LENGTH} characters or fewer")

    return name.strip(), phone, type_, note


def _with_balance(party, balance):
    """Every party the API hands back carries its balance in the one labelled
    shape defined by ledger_entry_model.describe_balance."""
    return {**party, **ledger_entry_model.describe_balance(balance)}


def get_parties(user_id, book_id=None, type_=None):
    if type_ and type_ not in VALID_TYPES:
        raise ValueError("Type filter must be 'customer' or 'supplier'")

    book = book_service.resolve_book(book_id, user_id)
    parties = party_model.get_parties_by_user(user_id, book_id=book["id"], type_=type_)
    balances = ledger_entry_model.get_balances_for_parties([p["id"] for p in parties], user_id)
    return [_with_balance(p, balances.get(p["id"], 0.0)) for p in parties]


def require_party(party_id, user_id):
    party = party_model.get_party_by_id(party_id, user_id)
    if party is None:
        raise not_found("Party not found")
    return party


def get_party(party_id, user_id):
    """One party with its full ledger and current balance."""
    party = require_party(party_id, user_id)
    balance = ledger_entry_model.get_balance_for_party(party_id, user_id)
    return {
        **_with_balance(party, balance),
        "entries": ledger_entry_model.get_entries_for_party(party_id, user_id),
    }


def get_party_balance(party_id, user_id):
    return ledger_entry_model.get_balance_for_party(party_id, user_id)


def create_party(user_id, data):
    name, phone, type_, note = _validate(data)
    book = book_service.resolve_book((data or {}).get("book_id"), user_id)

    if party_model.get_party_by_name(user_id, book["id"], name, type_) is not None:
        raise conflict(f"This book already has a {type_} called '{name}'")

    party = party_model.create_party(user_id, book["id"], name, phone, type_, note)
    activity_log_model.log(user_id, "Created party", f"{name} ({type_}) in {book['name']}")
    return _with_balance(party, 0.0)


def update_party(party_id, user_id, data):
    existing = require_party(party_id, user_id)
    name, phone, type_, note = _validate(data)

    clash = party_model.get_party_by_name(user_id, existing["book_id"], name, type_)
    if clash is not None and clash["id"] != party_id:
        raise conflict(f"This book already has a {type_} called '{name}'")

    updated = party_model.update_party(party_id, user_id, name, phone, type_, note)
    activity_log_model.log(user_id, "Updated party", f"{name} ({type_})")
    return _with_balance(updated, ledger_entry_model.get_balance_for_party(party_id, user_id))


def delete_party(party_id, user_id):
    """Removing a party takes its ledger and reminders with it — they have no
    meaning without the party they were recorded against."""
    party = require_party(party_id, user_id)

    reminder_model.delete_reminders_for_party(party_id, user_id)
    ledger_entry_model.delete_entries_for_party(party_id, user_id)
    party_model.delete_party(party_id, user_id)

    activity_log_model.log(user_id, "Deleted party", f"{party['name']} ({party['type']})")
    return True
