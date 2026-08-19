from datetime import datetime

from app.models import transaction as transaction_model

VALID_TYPES = ("income", "expense")
MAX_DESCRIPTION_LENGTH = 255


def validate_transaction_data(data):
    """Returns a cleaned dict of fields, or raises ValueError with a message."""
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")

    amount = data.get("amount")
    if not isinstance(amount, (int, float)) or isinstance(amount, bool):
        raise ValueError("Amount must be a number")
    if amount <= 0:
        raise ValueError("Amount must be greater than zero")

    type_ = data.get("type")
    if type_ not in VALID_TYPES:
        raise ValueError("Type must be 'income' or 'expense'")

    category = data.get("category")
    if not isinstance(category, str) or not category.strip():
        raise ValueError("Category is required")

    date = data.get("date")
    if not isinstance(date, str):
        raise ValueError("Date is required")
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Date must be a valid date in YYYY-MM-DD format")

    description = data.get("description") or ""
    if not isinstance(description, str):
        raise ValueError("Description must be text")
    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise ValueError(f"Description must be {MAX_DESCRIPTION_LENGTH} characters or fewer")

    return {
        "amount": float(amount),
        "type": type_,
        "category": category.strip(),
        "description": description.strip(),
        "date": date,
    }


def create_transaction(data, user_id):
    clean = validate_transaction_data(data)
    return transaction_model.create_transaction(
        user_id,
        clean["amount"],
        clean["type"],
        clean["category"],
        clean["description"],
        clean["date"],
    )


def get_transactions(user_id, category=None, type_=None, start_date=None, end_date=None, search=None):
    if type_ and type_ not in VALID_TYPES:
        raise ValueError("Type filter must be 'income' or 'expense'")

    for date_value in (start_date, end_date):
        if date_value:
            try:
                datetime.strptime(date_value, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Date filters must be in YYYY-MM-DD format")

    return transaction_model.get_transactions_by_user(
        user_id,
        category=category,
        type_=type_,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )


def get_transaction(transaction_id, user_id):
    """Returns None if the transaction doesn't exist OR belongs to a different user.
    Treating both cases the same way (a 404) avoids revealing that a transaction
    exists at all to a user who doesn't own it."""
    transaction = transaction_model.get_transaction_by_id(transaction_id)
    if transaction is None or transaction["user_id"] != user_id:
        return None
    return transaction


def update_transaction(transaction_id, data, user_id):
    if get_transaction(transaction_id, user_id) is None:
        return None
    clean = validate_transaction_data(data)
    return transaction_model.update_transaction(
        transaction_id,
        clean["amount"],
        clean["type"],
        clean["category"],
        clean["description"],
        clean["date"],
    )


def delete_transaction(transaction_id, user_id):
    if get_transaction(transaction_id, user_id) is None:
        return False
    transaction_model.delete_transaction(transaction_id)
    return True
