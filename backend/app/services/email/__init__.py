"""Pluggable outbound-email drivers — same shape as app.services.messaging.

Which driver is used is decided by the EMAIL_DRIVER env var and defaults to
`console`, which needs no configuration at all: it logs the email instead of
sending it, so password reset works locally with zero setup. Set
EMAIL_DRIVER=smtp and the SMTP_* env vars (see services/email/smtp.py) to
send real mail through any SMTP-capable provider."""

import os

from app.services.email import console, smtp, templates
from app.services.email.base import EmailError

DEFAULT_DRIVER = "console"
DRIVERS = {
    console.NAME: console,
    smtp.NAME: smtp,
}

__all__ = [
    "DEFAULT_DRIVER",
    "DRIVERS",
    "EmailError",
    "get_driver",
    "get_driver_name",
    "send",
    "status",
    "templates",
]


def get_driver_name(name=None):
    # Read at call time (not import time) so tests and a restarted process
    # both pick up the current environment.
    return (name or os.environ.get("EMAIL_DRIVER") or DEFAULT_DRIVER).strip().lower()


def get_driver(name=None):
    key = get_driver_name(name)
    driver = DRIVERS.get(key)
    if driver is None:
        raise EmailError(
            f"Unknown email driver '{key}' — set EMAIL_DRIVER to one of {', '.join(sorted(DRIVERS))}."
        )
    return driver


def send(to_email, subject, body, driver=None):
    return get_driver(driver).send(to_email, subject, body)


def status():
    """Read-only diagnostic for the admin dashboard: which driver is active,
    and whether every registered driver currently has what it needs to send
    — never actually sends anything."""
    active = get_driver_name()
    return {
        "active_driver": active,
        "drivers": [
            {"name": name, "is_active": name == active, "is_configured": module.is_configured()}
            for name, module in sorted(DRIVERS.items())
        ],
    }

