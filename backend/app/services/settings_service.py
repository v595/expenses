from app.models import user as user_model
from app.services.auth_service import to_public_user

ALLOWED_CURRENCIES = ("USD", "EUR", "GBP", "INR", "JPY", "AUD", "CAD")


def update_settings(user, data):
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")

    currency = data.get("currency", user.get("currency") or "USD")
    if currency not in ALLOWED_CURRENCIES:
        raise ValueError(f"Currency must be one of {', '.join(ALLOWED_CURRENCIES)}")

    notify_budget_alerts = data.get("notify_budget_alerts", user.get("notify_budget_alerts", True))
    if not isinstance(notify_budget_alerts, bool):
        raise ValueError("notify_budget_alerts must be true or false")

    notify_bill_reminders = data.get("notify_bill_reminders", user.get("notify_bill_reminders", True))
    if not isinstance(notify_bill_reminders, bool):
        raise ValueError("notify_bill_reminders must be true or false")

    updated = user_model.update_settings(
        user["id"], currency, int(notify_budget_alerts), int(notify_bill_reminders)
    )
    return to_public_user(updated)


def delete_account(user_id):
    user_model.delete_user(user_id)
