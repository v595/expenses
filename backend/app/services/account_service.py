from app.models import account as account_model

VALID_TYPES = ("cash", "bank", "card", "savings", "other")
MAX_NAME_LENGTH = 60


def _validate(data, require_all=True):
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Name is required")
    if len(name.strip()) > MAX_NAME_LENGTH:
        raise ValueError(f"Name must be {MAX_NAME_LENGTH} characters or fewer")

    type_ = data.get("type", "cash")
    if type_ not in VALID_TYPES:
        raise ValueError(f"Type must be one of {', '.join(VALID_TYPES)}")

    color = data.get("color") or None
    if color is not None and (not isinstance(color, str) or len(color) > 20):
        raise ValueError("Color must be a short string (e.g. a hex code)")

    balance = data.get("balance", 0) if require_all else 0
    if not isinstance(balance, (int, float)) or isinstance(balance, bool):
        raise ValueError("Starting balance must be a number")

    return name.strip(), type_, float(balance), color


def get_accounts(user_id):
    return account_model.get_accounts_by_user(user_id)


def create_account(user_id, data):
    name, type_, balance, color = _validate(data)
    return account_model.create_account(user_id, name, type_, balance, color)


def update_account(account_id, user_id, data):
    name, type_, _balance, color = _validate(data, require_all=False)
    updated = account_model.update_account(account_id, user_id, name, type_, color)
    if updated is None:
        raise ValueError("Account not found")
    return updated


def delete_account(account_id, user_id):
    account_model.delete_account(account_id, user_id)
