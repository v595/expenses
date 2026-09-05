"""Default text for outbound reminders. Callers may always pass their own
message instead — this is only what the app composes when they don't."""

DEFAULT_REMINDER_TEMPLATE = (
    "Hi {party}, this is a reminder that ₹{amount} is pending against your "
    "account with {book}. Please arrange the payment. Thank you."
)

MAX_MESSAGE_LENGTH = 1000


def format_amount(amount):
    return f"{float(amount or 0):,.2f}"


def reminder_message(party_name, amount, book_name, template=None):
    """Composes the reminder body. `template` (if given) may use the same
    {party} / {amount} / {book} placeholders; a template with no placeholders
    is simply returned as-is."""
    text = template or DEFAULT_REMINDER_TEMPLATE
    try:
        return text.format(party=party_name, amount=format_amount(amount), book=book_name)
    except (IndexError, KeyError, ValueError):
        # A caller-supplied message containing a stray brace isn't a template
        # at all — send it exactly as typed rather than failing the request.
        return text
