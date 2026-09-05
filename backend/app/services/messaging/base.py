"""Shared pieces every messaging driver builds on."""

import re


class MessagingError(Exception):
    """Raised when a message can't be prepared or sent. status_code tells the
    route what to return, mirroring auth_service.AuthError."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


_NON_PHONE_CHARS = re.compile(r"[^\d+]")


def normalize_phone(phone):
    """Storage format: digits, with at most one leading '+'.

    Everything a user might paste in — "+91 98765-43210", "(044) 2233 4455" —
    collapses to the same string, so the stored value and the wa.me link
    always agree. Returns None for anything with no digits at all."""
    if not phone or not isinstance(phone, str):
        return None
    stripped = phone.strip()
    has_plus = stripped.startswith("+")
    digits = _NON_PHONE_CHARS.sub("", stripped).replace("+", "")
    if not digits:
        return None
    return f"+{digits}" if has_plus else digits


def digits_only(phone):
    """wa.me wants the full international number with no '+', no spaces and
    no punctuation — just digits."""
    normalized = normalize_phone(phone)
    return normalized.lstrip("+") if normalized else None
