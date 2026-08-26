from datetime import datetime

from app.models import account as account_model
from app.models import activity_log as activity_log_model
from app.models import tag as tag_model
from app.models import transaction as transaction_model
from app.services import tag_service

VALID_TYPES = ("income", "expense")
MAX_DESCRIPTION_LENGTH = 255
MAX_RECEIPT_LENGTH = 2_800_000  # ~2MB image, base64-encoded


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

    account_id = data.get("account_id")
    if account_id is not None and (not isinstance(account_id, int) or isinstance(account_id, bool)):
        raise ValueError("Account id must be a number")

    receipt = data.get("receipt")
    if receipt is not None:
        if not isinstance(receipt, str) or not receipt.startswith("data:image/"):
            raise ValueError("Receipt must be an image")
        if len(receipt) > MAX_RECEIPT_LENGTH:
            raise ValueError("Receipt image is too large (max ~2MB)")

    tags = data.get("tags")

    return {
        "amount": float(amount),
        "type": type_,
        "category": category.strip(),
        "description": description.strip(),
        "date": date,
        "account_id": account_id,
        "receipt": receipt,
        "tags": tags,
    }


def _balance_delta(amount, type_):
    return amount if type_ == "income" else -amount


def _attach_extras(transaction):
    transaction["tags"] = tag_model.get_tags_for_transaction(transaction["id"])
    return transaction


def create_transaction(data, user_id):
    clean = validate_transaction_data(data)

    if clean["account_id"] is not None and account_model.get_account_by_id(clean["account_id"], user_id) is None:
        raise ValueError("Account not found")

    transaction = transaction_model.create_transaction(
        user_id,
        clean["amount"],
        clean["type"],
        clean["category"],
        clean["description"],
        clean["date"],
        clean["account_id"],
        clean["receipt"],
    )

    if clean["account_id"] is not None:
        account_model.adjust_balance(clean["account_id"], _balance_delta(clean["amount"], clean["type"]))

    tag_ids = tag_service.resolve_tag_names(user_id, clean["tags"])
    tag_model.set_tags_for_transaction(transaction["id"], tag_ids)

    activity_log_model.log(
        user_id, "Created transaction", f"{clean['category']} {clean['amount']:.2f} ({clean['type']})"
    )
    return _attach_extras(transaction)


def get_transactions(user_id, category=None, type_=None, start_date=None, end_date=None, search=None, tag_id=None):
    if type_ and type_ not in VALID_TYPES:
        raise ValueError("Type filter must be 'income' or 'expense'")

    for date_value in (start_date, end_date):
        if date_value:
            try:
                datetime.strptime(date_value, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Date filters must be in YYYY-MM-DD format")

    transactions = transaction_model.get_transactions_by_user(
        user_id,
        category=category,
        type_=type_,
        start_date=start_date,
        end_date=end_date,
        search=search,
        tag_id=tag_id,
    )

    tags_by_transaction = tag_model.get_tags_for_transactions([t["id"] for t in transactions])
    for t in transactions:
        t["tags"] = tags_by_transaction.get(t["id"], [])
    return transactions


def get_transaction(transaction_id, user_id):
    """Returns None if the transaction doesn't exist OR belongs to a different user.
    Treating both cases the same way (a 404) avoids revealing that a transaction
    exists at all to a user who doesn't own it."""
    transaction = transaction_model.get_transaction_by_id(transaction_id)
    if transaction is None or transaction["user_id"] != user_id:
        return None
    return _attach_extras(transaction)


def update_transaction(transaction_id, data, user_id):
    existing = transaction_model.get_transaction_by_id(transaction_id)
    if existing is None or existing["user_id"] != user_id:
        return None

    clean = validate_transaction_data(data)

    if clean["account_id"] is not None and account_model.get_account_by_id(clean["account_id"], user_id) is None:
        raise ValueError("Account not found")

    if existing["account_id"] is not None:
        account_model.adjust_balance(
            existing["account_id"], -_balance_delta(existing["amount"], existing["type"])
        )

    updated = transaction_model.update_transaction(
        transaction_id,
        clean["amount"],
        clean["type"],
        clean["category"],
        clean["description"],
        clean["date"],
        clean["account_id"],
        clean["receipt"] if clean["receipt"] is not None else existing["receipt"],
    )

    if clean["account_id"] is not None:
        account_model.adjust_balance(clean["account_id"], _balance_delta(clean["amount"], clean["type"]))

    tag_ids = tag_service.resolve_tag_names(user_id, clean["tags"])
    tag_model.set_tags_for_transaction(transaction_id, tag_ids)

    activity_log_model.log(
        user_id, "Updated transaction", f"{clean['category']} {clean['amount']:.2f} ({clean['type']})"
    )
    return _attach_extras(updated)


def delete_transaction(transaction_id, user_id):
    existing = transaction_model.get_transaction_by_id(transaction_id)
    if existing is None or existing["user_id"] != user_id:
        return False

    if existing["account_id"] is not None:
        account_model.adjust_balance(
            existing["account_id"], -_balance_delta(existing["amount"], existing["type"])
        )

    transaction_model.delete_transaction(transaction_id)
    activity_log_model.log(
        user_id, "Deleted transaction", f"{existing['category']} {existing['amount']:.2f}"
    )
    return True


def bulk_import(user_id, rows):
    """Used by CSV import: validates each row independently so one bad row
    doesn't block the rest of the file, and reports back what happened."""
    if not isinstance(rows, list):
        raise ValueError("Request body must be a list of rows")

    imported = 0
    errors = []
    for index, row in enumerate(rows):
        try:
            clean = validate_transaction_data(row)
        except ValueError as e:
            errors.append({"row": index + 1, "error": str(e)})
            continue
        transaction_model.create_transaction(
            user_id, clean["amount"], clean["type"], clean["category"], clean["description"], clean["date"]
        )
        imported += 1

    if imported:
        activity_log_model.log(user_id, "Imported transactions via CSV", f"{imported} row(s)")
    return {"imported": imported, "errors": errors}
