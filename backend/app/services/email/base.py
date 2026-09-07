"""Shared pieces every email driver builds on."""


class EmailError(Exception):
    """Raised when an email can't be prepared or sent. status_code tells the
    route what to return, mirroring auth_service.AuthError."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
