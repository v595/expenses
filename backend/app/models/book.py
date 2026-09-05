from app.extensions import db
from app.models.orm import Book, now_iso

DEFAULT_BOOK_NAME = "My Book"
DEFAULT_BOOK_TYPE = "personal"


def get_books_by_user(user_id):
    rows = (
        db.session.query(Book)
        .filter_by(user_id=user_id)
        .order_by(Book.is_default.desc(), Book.name)
        .all()
    )
    return [b.to_dict() for b in rows]


def get_book_by_id(book_id, user_id):
    book = db.session.query(Book).filter_by(id=book_id, user_id=user_id).first()
    return book.to_dict() if book else None


def get_book_by_name(user_id, name):
    book = db.session.query(Book).filter_by(user_id=user_id, name=name).first()
    return book.to_dict() if book else None


def get_default_book(user_id):
    book = (
        db.session.query(Book)
        .filter_by(user_id=user_id, is_default=True)
        .order_by(Book.id)
        .first()
    )
    return book.to_dict() if book else None


def count_books(user_id):
    return db.session.query(Book).filter_by(user_id=user_id).count()


def create_book(user_id, name, type_, color=None, is_default=False):
    book = Book(
        user_id=user_id,
        name=name,
        type=type_,
        is_default=is_default,
        color=color,
        created_at=now_iso(),
    )
    db.session.add(book)
    db.session.commit()
    return book.to_dict()


def ensure_default_book(user_id):
    """Every user must always have at least one book, so this lazily creates
    "My Book" for anyone who has none. Cheap (one COUNT) and idempotent, so
    it's called on the login/registration paths the same way
    `user_model.promote_first_user_if_no_admin` is — the invariant then holds
    immediately rather than waiting for the user to open the Books screen."""
    existing = db.session.query(Book).filter_by(user_id=user_id).order_by(Book.id).first()
    if existing is not None:
        # Also self-heal the "exactly one default" invariant if a book exists
        # but none of them is flagged as the default.
        if db.session.query(Book).filter_by(user_id=user_id, is_default=True).count() == 0:
            existing.is_default = True
            db.session.commit()
        return existing.to_dict()
    return create_book(user_id, DEFAULT_BOOK_NAME, DEFAULT_BOOK_TYPE, is_default=True)


def update_book(book_id, user_id, name, type_, color):
    book = db.session.query(Book).filter_by(id=book_id, user_id=user_id).first()
    if book is None:
        return None
    book.name = name
    book.type = type_
    book.color = color
    db.session.commit()
    return book.to_dict()


def set_default(book_id, user_id):
    """Flips the default onto this book and clears it off every other book of
    the same user, so there is always exactly one default."""
    book = db.session.query(Book).filter_by(id=book_id, user_id=user_id).first()
    if book is None:
        return None
    db.session.query(Book).filter(Book.user_id == user_id, Book.id != book_id).update(
        {Book.is_default: False}
    )
    book.is_default = True
    db.session.commit()
    return book.to_dict()


def delete_book(book_id, user_id):
    db.session.query(Book).filter_by(id=book_id, user_id=user_id).delete()
    db.session.commit()
