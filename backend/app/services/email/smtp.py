"""Generic SMTP driver — works with any provider that exposes an SMTP relay
(Gmail app password, SendGrid, Resend, Mailgun, Postmark, your own mail
server...), so there's one driver to maintain instead of one per provider.
Uses only the standard library (smtplib), so no new dependency is needed to
turn this on. Reads credentials from the environment at call time and
refuses, with an actionable message, until they're set."""

import os
import smtplib
from email.message import EmailMessage

from app.services.email.base import EmailError

NAME = "smtp"
REQUIRED_ENV_VARS = ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD")


def _config():
    return {
        "host": os.environ.get("SMTP_HOST"),
        "port": os.environ.get("SMTP_PORT", "587"),
        "user": os.environ.get("SMTP_USER"),
        "password": os.environ.get("SMTP_PASSWORD"),
        "from_addr": os.environ.get("SMTP_FROM") or os.environ.get("SMTP_USER"),
    }


def is_configured():
    cfg = _config()
    return bool(cfg["host"] and cfg["user"] and cfg["password"] and cfg["from_addr"])


def send(to_email, subject, body):
    cfg = _config()
    if not is_configured():
        raise EmailError(
            "Email sending is not configured — set SMTP_HOST, SMTP_USER, SMTP_PASSWORD "
            "(and optionally SMTP_PORT, SMTP_FROM) in the backend environment. Until then "
            "leave EMAIL_DRIVER unset to use the zero-config console driver."
        )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = cfg["from_addr"]
    message["To"] = to_email
    message.set_content(body)

    try:
        with smtplib.SMTP(cfg["host"], int(cfg["port"]), timeout=10) as server:
            server.starttls()
            server.login(cfg["user"], cfg["password"])
            server.send_message(message)
    except (smtplib.SMTPException, OSError) as e:
        raise EmailError(f"Could not send email: {e}", status_code=502) from e

    return {"driver": NAME, "status": "sent"}
