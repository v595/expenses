from datetime import date as date_cls

from app.models import activity_log as activity_log_model
from app.models import ledger_entry as ledger_entry_model
from app.models import party as party_model
from app.models import reminder as reminder_model
from app.models.orm import now_iso
from app.services import book_service, messaging
from app.services.errors import not_found
from app.services.messaging import MessagingError, templates

VALID_CHANNELS = ("whatsapp", "sms", "inapp")
DEFAULT_CHANNEL = "whatsapp"
# Channels that go out through a messaging driver; "inapp" never leaves the app.
DRIVEN_CHANNELS = ("whatsapp", "sms")


def _today():
    return date_cls.today().isoformat()


def get_pending_dues(user_id, book_id=None, overdue_only=False, as_of=None):
    """The "payment pending" list: every party in the book that currently owes
    the user money — i.e. a POSITIVE balance, which per
    ledger_entry_model.describe_balance means "You'll get".

    With overdue_only, narrows to parties whose earliest `given` entry carries
    a due_date already in the past (relative to `as_of`, default today)."""
    book = book_service.resolve_book(book_id, user_id)
    as_of = as_of or _today()

    parties = party_model.get_parties_by_user(user_id, book_id=book["id"])
    party_ids = [p["id"] for p in parties]
    balances = ledger_entry_model.get_balances_for_parties(party_ids, user_id)
    due_dates = ledger_entry_model.get_earliest_due_dates(party_ids, user_id)

    dues = []
    for party in parties:
        balance = balances.get(party["id"], 0.0)
        if balance <= 0:
            continue

        due_date = due_dates.get(party["id"])
        is_overdue = bool(due_date) and due_date < as_of
        if overdue_only and not is_overdue:
            continue

        dues.append(
            {
                **party,
                **ledger_entry_model.describe_balance(balance),
                "due_date": due_date,
                "is_overdue": is_overdue,
                "days_overdue": _days_between(due_date, as_of) if is_overdue else 0,
            }
        )

    dues.sort(key=lambda d: (not d["is_overdue"], -d["balance"]))
    return {
        "book_id": book["id"],
        "book_name": book["name"],
        "as_of": as_of,
        "total_pending": round(sum(d["balance"] for d in dues), 2),
        "parties": dues,
    }


def _days_between(earlier, later):
    return (date_cls.fromisoformat(later) - date_cls.fromisoformat(earlier)).days


def create_reminder(user_id, data):
    """Records the reminder and asks the configured driver to prepare it. With
    the default `wa_link` driver nothing is actually sent — the response
    carries a wa.me link for the frontend to open, and the reminder stays
    'pending' until `mark_sent` confirms the user went through with it."""
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")

    party_id = data.get("party_id")
    if not isinstance(party_id, int) or isinstance(party_id, bool):
        raise ValueError("Party id is required")

    party = party_model.get_party_by_id(party_id, user_id)
    if party is None:
        raise not_found("Party not found")

    channel = data.get("channel") or DEFAULT_CHANNEL
    if channel not in VALID_CHANNELS:
        raise ValueError(f"Channel must be one of {', '.join(VALID_CHANNELS)}")

    message_override = data.get("message")
    if message_override is not None and not isinstance(message_override, str):
        raise ValueError("Message must be text")
    if message_override is not None and len(message_override) > templates.MAX_MESSAGE_LENGTH:
        raise ValueError(f"Message must be {templates.MAX_MESSAGE_LENGTH} characters or fewer")

    book = book_service.require_book(party["book_id"], user_id)
    balance = ledger_entry_model.get_balance_for_party(party["id"], user_id)

    if balance <= 0 and not message_override:
        raise ValueError("Nothing is pending against this party — write your own message to send one anyway")

    message = templates.reminder_message(party["name"], balance, book["name"], message_override)

    result = {"driver": None, "status": "pending", "link": None, "requires_user_action": False}
    if channel in DRIVEN_CHANNELS:
        if not party["phone"]:
            raise ValueError("This party has no phone number saved")
        try:
            result = messaging.send(party["phone"], message)
        except MessagingError as e:
            # Record the attempt as failed rather than losing it, then let the
            # route surface the driver's (actionable) message.
            reminder_model.create_reminder(
                user_id, book["id"], party["id"], channel, message, status="failed"
            )
            raise e

    reminder = reminder_model.create_reminder(
        user_id, book["id"], party["id"], channel, message, status=result["status"]
    )
    activity_log_model.log(
        user_id, "Created payment reminder", f"{party['name']} via {channel}"
    )
    return {
        **reminder,
        "party_name": party["name"],
        "party_phone": party["phone"],
        "driver": result["driver"],
        "link": result["link"],
        "requires_user_action": result["requires_user_action"],
        **ledger_entry_model.describe_balance(balance),
    }


def mark_sent(reminder_id, user_id):
    """Separate from creating the reminder on purpose: the default driver only
    hands the user a link, so the app can't know a message went out until the
    caller says so."""
    reminder = reminder_model.get_reminder_by_id(reminder_id, user_id)
    if reminder is None:
        raise not_found("Reminder not found")

    updated = reminder_model.set_status(reminder_id, user_id, "sent", sent_at=now_iso())
    activity_log_model.log(user_id, "Marked reminder sent", f"reminder #{reminder_id}")
    return updated


def get_history(user_id, book_id=None, party_id=None):
    book = book_service.resolve_book(book_id, user_id)
    if party_id is not None:
        # Scope-check before filtering by it, so another user's party id can't
        # be used to probe this book.
        if party_model.get_party_by_id(party_id, user_id) is None:
            raise not_found("Party not found")
    return reminder_model.get_reminders_by_user(user_id, book_id=book["id"], party_id=party_id)
