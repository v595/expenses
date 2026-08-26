from datetime import datetime

from app.models import bill as bill_model
from app.services.recurring_service import _advance

VALID_FREQUENCIES = ("none", "weekly", "monthly", "yearly")
MAX_NAME_LENGTH = 80


def get_bills(user_id):
    return bill_model.get_bills_by_user(user_id)


def create_bill(user_id, data):
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Name is required")
    if len(name.strip()) > MAX_NAME_LENGTH:
        raise ValueError(f"Name must be {MAX_NAME_LENGTH} characters or fewer")

    amount = data.get("amount")
    if not isinstance(amount, (int, float)) or isinstance(amount, bool):
        raise ValueError("Amount must be a number")
    if amount <= 0:
        raise ValueError("Amount must be greater than zero")

    due_date = data.get("due_date")
    if not isinstance(due_date, str):
        raise ValueError("Due date is required")
    try:
        datetime.strptime(due_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Due date must be a valid date in YYYY-MM-DD format")

    repeat_frequency = data.get("repeat_frequency") or "none"
    if repeat_frequency not in VALID_FREQUENCIES:
        raise ValueError(f"Repeat frequency must be one of {', '.join(VALID_FREQUENCIES)}")

    return bill_model.create_bill(
        user_id, name.strip(), float(amount), due_date, repeat_frequency
    )


def pay_bill(bill_id, user_id):
    bill = bill_model.get_bill_by_id(bill_id, user_id)
    if bill is None:
        raise ValueError("Bill not found")

    bill_model.mark_paid(bill_id, user_id)

    if bill["repeat_frequency"] and bill["repeat_frequency"] != "none":
        next_date = _advance(bill["due_date"], bill["repeat_frequency"])
        bill_model.reschedule(bill_id, next_date)

    return bill_model.get_bill_by_id(bill_id, user_id)


def delete_bill(bill_id, user_id):
    bill_model.delete_bill(bill_id, user_id)
