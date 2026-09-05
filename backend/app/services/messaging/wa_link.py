"""WhatsApp click-to-chat driver — the default, and the only one that works
with zero configuration.

It sends nothing itself. It builds a `https://wa.me/<digits>?text=<encoded>`
URL that the frontend opens; WhatsApp then shows the user the pre-filled
message and *they* tap Send. That's why `send()` reports status "pending":
the reminder only becomes "sent" once the caller confirms it was opened —
see `reminder_service.mark_sent`.

Deliberately chosen over a real SMS/WhatsApp API for now: an actual provider
needs an account (and, for Indian SMS, DLT registration), neither of which
exists yet."""

from urllib.parse import quote

from app.services.messaging.base import MessagingError, digits_only

NAME = "wa_link"
BASE_URL = "https://wa.me"


def is_configured():
    """Nothing to configure — that's the whole point of this driver."""
    return True


def build_link(phone, message):
    number = digits_only(phone)
    if not number:
        raise MessagingError("A phone number is required to build a WhatsApp link")
    # safe="" so every reserved character (including '/', '&' and '?') in the
    # message body is percent-encoded rather than ending the query string.
    return f"{BASE_URL}/{number}?text={quote(message or '', safe='')}"


def send(phone, message):
    return {
        "driver": NAME,
        "status": "pending",
        "link": build_link(phone, message),
        # The caller has to open the link and let the user press Send; only
        # then should the reminder be marked sent.
        "requires_user_action": True,
    }
