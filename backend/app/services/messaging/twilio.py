"""Twilio driver — STUB.

There is no Twilio account behind this app yet, so nothing is sent. The
driver exists so that switching to real sending later is a config change
(`MESSAGING_DRIVER=twilio`) rather than a refactor. Credentials are read from
the environment at call time and never hardcoded."""

import os

from app.services.messaging.base import MessagingError, normalize_phone

NAME = "twilio"
REQUIRED_ENV_VARS = ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM")


def _credentials():
    return {key: os.environ.get(key) for key in REQUIRED_ENV_VARS}


def is_configured():
    return all(_credentials().values())


def send(phone, message):
    credentials = _credentials()
    missing = [key for key, value in credentials.items() if not value]
    if missing:
        raise MessagingError(
            "Twilio is not configured — set "
            + ", ".join(REQUIRED_ENV_VARS)
            + f" in the backend environment (missing: {', '.join(missing)}). "
            "Until then leave MESSAGING_DRIVER unset to use the zero-config "
            "WhatsApp click-to-chat driver."
        )

    number = normalize_phone(phone)
    if not number:
        raise MessagingError("A phone number is required to send a message")

    # TODO: perform the real send — POST to
    # https://api.twilio.com/2010-04-01/Accounts/<sid>/Messages.json with
    # HTTP basic auth (sid, auth token) and form fields From/To/Body, then
    # map Twilio's response back onto {"driver", "status", "link"}.
    # Left unimplemented on purpose: there is no Twilio account to test
    # against, and adding one would mean new pip dependencies/credentials.
    raise MessagingError(
        "Twilio sending is not implemented yet — credentials are read, but the "
        "outbound API call is still a TODO. Use MESSAGING_DRIVER=wa_link.",
        status_code=501,
    )
