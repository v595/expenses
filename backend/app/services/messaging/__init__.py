"""Pluggable outbound-messaging drivers.

Which driver is used is decided by the MESSAGING_DRIVER env var and defaults
to `wa_link`, which needs no configuration at all: it builds a WhatsApp
click-to-chat link for the user to open, rather than sending anything. The
`twilio` and `msg91` drivers are stubs that read their credentials from the
environment and refuse, with an actionable message, until those are set."""

import os

from app.services.messaging import msg91, templates, twilio, wa_link
from app.services.messaging.base import MessagingError, digits_only, normalize_phone

DEFAULT_DRIVER = "wa_link"
DRIVERS = {
    wa_link.NAME: wa_link,
    twilio.NAME: twilio,
    msg91.NAME: msg91,
}

__all__ = [
    "DEFAULT_DRIVER",
    "DRIVERS",
    "MessagingError",
    "digits_only",
    "get_driver",
    "get_driver_name",
    "normalize_phone",
    "send",
    "templates",
]


def get_driver_name(name=None):
    # Read at call time (not import time) so tests and a restarted process
    # both pick up the current environment.
    return (name or os.environ.get("MESSAGING_DRIVER") or DEFAULT_DRIVER).strip().lower()


def get_driver(name=None):
    key = get_driver_name(name)
    driver = DRIVERS.get(key)
    if driver is None:
        raise MessagingError(
            f"Unknown messaging driver '{key}' — set MESSAGING_DRIVER to one of "
            f"{', '.join(sorted(DRIVERS))}."
        )
    return driver


def send(phone, message, driver=None):
    """Hands the message to the configured driver. Returns
    {"driver", "status", "link", "requires_user_action"} — `link` is the
    wa.me URL for the default driver and None for anything that really sends.
    Raises MessagingError if the driver isn't usable."""
    return get_driver(driver).send(phone, message)
