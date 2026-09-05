from app.models import activity_log as activity_log_model
from app.models import book as book_model
from app.services.errors import ServiceError, conflict, not_found

VALID_TYPES = ("business", "personal", "home", "daily")
DEFAULT_TYPE = "personal"
MAX_NAME_LENGTH = 60


def _validate(data):
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Name is required")
    if len(name.strip()) > MAX_NAME_LENGTH:
        raise ValueError(f"Name must be {MAX_NAME_LENGTH} characters or fewer")

    type_ = data.get("type") or DEFAULT_TYPE
    if type_ not in VALID_TYPES:
        raise ValueError(f"Type must be one of {', '.join(VALID_TYPES)}")

    color = data.get("color") or None
    if color is not None and (not isinstance(color, str) or len(color) > 20):
        raise ValueError("Color must be a short string (e.g. a hex code)")

    return name.strip(), type_, color


def get_books(user_id):
    """Listing also guarantees the "at least one book" invariant, so a user
    who signed up before Books existed still sees one."""
    book_model.ensure_default_book(user_id)
    return book_model.get_books_by_user(user_id)


def get_book(book_id, user_id):
    """Returns None for a book that doesn't exist OR belongs to someone else —
    routes turn that into a 404 either way."""
    return book_model.get_book_by_id(book_id, user_id)


def require_book(book_id, user_id):
    book = book_model.get_book_by_id(book_id, user_id)
    if book is None:
        raise not_found("Book not found")
    return book


def resolve_book(book_id, user_id):
    """The book a request is about: the one asked for, or the user's default
    when the caller didn't name one."""
    if book_id is not None:
        return require_book(book_id, user_id)
    return book_model.ensure_default_book(user_id)


def create_book(user_id, data):
    name, type_, color = _validate(data)

    if book_model.get_book_by_name(user_id, name) is not None:
        raise conflict("You already have a book with that name")

    # The very first book a user ever gets is automatically their default.
    is_default = book_model.count_books(user_id) == 0
    book = book_model.create_book(user_id, name, type_, color, is_default=is_default)
    activity_log_model.log(user_id, "Created book", f"{name} ({type_})")
    return book


def update_book(book_id, user_id, data):
    require_book(book_id, user_id)
    name, type_, color = _validate(data)

    clash = book_model.get_book_by_name(user_id, name)
    if clash is not None and clash["id"] != book_id:
        raise conflict("You already have a book with that name")

    updated = book_model.update_book(book_id, user_id, name, type_, color)
    activity_log_model.log(user_id, "Updated book", f"{name} ({type_})")
    return updated


def set_default_book(book_id, user_id):
    book = require_book(book_id, user_id)
    updated = book_model.set_default(book_id, user_id)
    activity_log_model.log(user_id, "Set default book", book["name"])
    return updated


def delete_book(book_id, user_id):
    """A user must never be left with zero books, so deleting the last one is
    rejected rather than silently recreating a replacement."""
    book = require_book(book_id, user_id)

    if book_model.count_books(user_id) <= 1:
        raise ServiceError(
            "You can't delete your only book — create another book first", 400
        )

    from app.models import party as party_model
    from app.models import transaction as transaction_model

    if party_model.count_parties_for_book(book_id, user_id) > 0:
        raise conflict("This book still has parties in it — delete them first")

    transaction_model.unassign_book(book_id, user_id)
    book_model.delete_book(book_id, user_id)

    # Deleting the default hands the flag to whichever book is left, keeping
    # exactly one default at all times.
    if book["is_default"]:
        remaining = book_model.get_books_by_user(user_id)
        if remaining:
            book_model.set_default(remaining[0]["id"], user_id)

    activity_log_model.log(user_id, "Deleted book", book["name"])
    return True
