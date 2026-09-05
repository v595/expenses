"""MSG91 driver — STUB.

Same story as the Twilio driver: no account exists yet, and Indian SMS also
requires DLT registration of the sender id and every template before a single
message can go out. Credentials are read from the environment at call time
and never hardcoded."""

import os

from app.services.messaging.base import MessagingError, normalize_phone

NAME = "msg91"
REQUIRED_ENV_VARS = ("MSG91_AUTH_KEY", "MSG91_SENDER_ID")


def _credentials():
    return {key: os.environ.get(key) for key in REQUIRED_ENV_VARS}


def is_configured():
    return all(_credentials().values())


def send(phone, message):
    credentials = _credentials()
    missing = [key for key, value in credentials.items() if not value]
    if missing:
        raise MessagingError(
            "MSG91 is not configured — set "
            + ", ".join(REQUIRED_ENV_VARS)
            + f" in the backend environment (missing: {', '.join(missing)}). "
            "Indian SMS also needs the sender id and message template "
            "registered on DLT. Until then leave MESSAGING_DRIVER unset to use "
            "the zero-config WhatsApp click-to-chat driver."
        )

    number = normalize_phone(phone)
    if not number:
        raise MessagingError("A phone number is required to send a message")

    # TODO: perform the real send — POST to https://control.msg91.com/api/v5/flow/
    # with the authkey header, the DLT-approved template id and the recipient
    # variables, then map the response back onto {"driver", "status", "link"}.
    # Left unimplemented on purpose: no MSG91 account and no DLT registration.
    raise MessagingError(
        "MSG91 sending is not implemented yet — credentials are read, but the "
        "outbound API call is still a TODO. Use MESSAGING_DRIVER=wa_link.",
        status_code=501,
    )
