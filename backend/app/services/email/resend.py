"""Resend driver — sends over HTTPS (api.resend.com), not a raw SMTP socket.

Exists because most PaaS hosts, Render included, block outbound SMTP ports
entirely to stop their platform being used as a spam relay — smtp.py's
"Network is unreachable" is that block, not a credentials problem, and no
amount of correct SMTP config gets through it. An HTTPS POST isn't blocked.

Uses `requests` (already a dependency for the Google/Facebook sign-in
verification calls), so no new package is needed to turn this on."""

import os

import requests

from app.services.email.base import EmailError

NAME = "resend"
API_URL = "https://api.resend.com/emails"
# Resend's own shared testing sender — works immediately with no domain
# verification, but can only deliver to the email address on the Resend
# account itself. Verify a real domain in Resend and set RESEND_FROM to
# send to anyone once ready for real users.
DEFAULT_FROM = "onboarding@resend.dev"


def _config():
    return {
        "api_key": os.environ.get("RESEND_API_KEY"),
        "from_addr": os.environ.get("RESEND_FROM") or DEFAULT_FROM,
    }


def is_configured():
    return bool(_config()["api_key"])


def send(to_email, subject, body):
    cfg = _config()
    if not cfg["api_key"]:
        raise EmailError(
            "Email sending is not configured — set RESEND_API_KEY (get one free at "
            "resend.com) in the backend environment. Until then leave EMAIL_DRIVER "
            "unset to use the zero-config console driver."
        )

    try:
        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {cfg['api_key']}"},
            json={"from": cfg["from_addr"], "to": [to_email], "subject": subject, "text": body},
            timeout=10,
        )
    except requests.RequestException as e:
        raise EmailError(f"Could not reach Resend: {e}", status_code=502) from e

    if not response.ok:
        raise EmailError(f"Resend rejected the email ({response.status_code}): {response.text}", status_code=502)

    return {"driver": NAME, "status": "sent"}
