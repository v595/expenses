from app.models import account as account_model
from app.models import activity_log as activity_log_model

VALID_TYPES = ("cash", "bank", "card", "savings", "investment", "loan", "other")
# Which of the above count as a liability for net worth (assets - liabilities)
# rather than an asset. Everything else is treated as an asset.
LIABILITY_TYPES = ("loan",)
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
    account = account_model.create_account(user_id, name, type_, balance, color)
    activity_log_model.log(user_id, "Created account", f"{name} ({type_})")
    return account


def update_account(account_id, user_id, data):
    name, type_, _balance, color = _validate(data, require_all=False)
    updated = account_model.update_account(account_id, user_id, name, type_, color)
    if updated is None:
        raise ValueError("Account not found")
    activity_log_model.log(user_id, "Updated account", name)
    return updated


def get_net_worth(user_id):
    """Assets (cash/bank/card/savings/investment/other) minus liabilities
    (loan) — a `loan` account's balance is "how much you still owe", entered
    as a positive number and paid down over time the same way any other
    account balance changes, so it subtracts here rather than adds."""
    accounts = account_model.get_accounts_by_user(user_id)

    by_type = {}
    assets = 0.0
    liabilities = 0.0
    for account in accounts:
        by_type.setdefault(account["type"], 0.0)
        by_type[account["type"]] += account["balance"]
        if account["type"] in LIABILITY_TYPES:
            liabilities += account["balance"]
        else:
            assets += account["balance"]

    return {
        "assets": round(assets, 2),
        "liabilities": round(liabilities, 2),
        "net_worth": round(assets - liabilities, 2),
        "by_type": {k: round(v, 2) for k, v in by_type.items()},
    }


def delete_account(account_id, user_id):
    account = account_model.get_account_by_id(account_id, user_id)
    account_model.delete_account(account_id, user_id)
    if account:
        activity_log_model.log(user_id, "Deleted account", account["name"])
