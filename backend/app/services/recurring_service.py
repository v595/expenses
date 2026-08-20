import calendar
from datetime import date, datetime, timedelta

from app.models import recurring as recurring_model
from app.models import transaction as transaction_model

VALID_FREQUENCIES = ("weekly", "monthly", "yearly")
MAX_DESCRIPTION_LENGTH = 255


def _add_months(d, months):
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _advance(date_str, frequency):
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    if frequency == "weekly":
        d = d + timedelta(days=7)
    elif frequency == "monthly":
        d = _add_months(d, 1)
    else:
        d = _add_months(d, 12)
    return d.isoformat()


def materialize_due(user_id):
    """Turns any recurring rule whose next_date has arrived into real transactions,
    catching up on every date missed since the app was last opened (no real cron
    exists here, so this runs lazily whenever the user's data is fetched)."""
    today = date.today().isoformat()
    for rule in recurring_model.get_due_recurring(user_id, today):
        next_date = rule["next_date"]
        while next_date <= today:
            transaction_model.create_transaction(
                user_id, rule["amount"], rule["type"], rule["category"], rule["description"], next_date
            )
            next_date = _advance(next_date, rule["frequency"])
        recurring_model.update_next_date(rule["id"], next_date)


def get_recurring(user_id):
    return recurring_model.get_recurring_by_user(user_id)


def create_recurring(data, user_id):
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")

    amount = data.get("amount")
    if not isinstance(amount, (int, float)) or isinstance(amount, bool):
        raise ValueError("Amount must be a number")
    if amount <= 0:
        raise ValueError("Amount must be greater than zero")

    type_ = data.get("type")
    if type_ not in ("income", "expense"):
        raise ValueError("Type must be 'income' or 'expense'")

    category = data.get("category")
    if not isinstance(category, str) or not category.strip():
        raise ValueError("Category is required")

    frequency = data.get("frequency")
    if frequency not in VALID_FREQUENCIES:
        raise ValueError("Frequency must be 'weekly', 'monthly', or 'yearly'")

    start_date = data.get("start_date")
    if not isinstance(start_date, str):
        raise ValueError("Start date is required")
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Start date must be a valid date in YYYY-MM-DD format")

    description = data.get("description") or ""
    if not isinstance(description, str):
        raise ValueError("Description must be text")
    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise ValueError(f"Description must be {MAX_DESCRIPTION_LENGTH} characters or fewer")

    return recurring_model.create_recurring(
        user_id, float(amount), type_, category.strip(), description.strip(), frequency, start_date
    )


def delete_recurring(recurring_id, user_id):
    recurring_model.delete_recurring(recurring_id, user_id)
