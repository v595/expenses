"""Zero-config default: doesn't send anything, just logs the email. This is
what makes password reset work out of the box in dev — the reset link shows
up in the backend's own console/log output instead of an inbox. Set
EMAIL_DRIVER=smtp (and the SMTP_* env vars) to actually send mail.

Uses current_app.logger (not a standalone `logging.getLogger(...)`) — the
same logger the admin dashboard's own reset-link logging already uses.
A bare module logger has no handler until something configures one, so its
INFO records get silently dropped by Python's logging "handler of last
resort"; current_app.logger is already wired up by Flask/Werkzeug."""

from flask import current_app

NAME = "console"


def is_configured():
    return True  # needs nothing


def send(to_email, subject, body):
    current_app.logger.info("EMAIL to=%s subject=%r\n%s", to_email, subject, body)
    return {"driver": NAME, "status": "logged"}
