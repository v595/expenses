class ServiceError(Exception):
    """Raised by a service when a business rule fails in a way that maps to a
    specific HTTP status other than a plain 400 — a missing/other-user row
    (404), a uniqueness clash (409), a rule like "you can't delete your last
    book" (400). Same shape as auth_service.AuthError, so routes handle it the
    same way: `jsonify({"error": e.message}), e.status_code`.

    Plain validation failures keep raising ValueError, exactly as the older
    services do; routes map those to 400."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def not_found(message):
    """404 rather than 403 for someone else's row — a user must not be able to
    tell the difference between "doesn't exist" and "isn't yours", the same
    way transaction_service.get_transaction does it."""
    return ServiceError(message, 404)


def conflict(message):
    return ServiceError(message, 409)
