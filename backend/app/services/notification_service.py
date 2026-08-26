from datetime import date, datetime, timedelta, timezone

from app.models import bill as bill_model
from app.models import budget as budget_model
from app.models import notification as notification_model
from app.models import transaction as transaction_model

BILL_REMINDER_WINDOW_DAYS = 3


def _generate_budget_alerts(user_id):
    year_month = datetime.now(timezone.utc).strftime("%Y-%m")
    budgets = budget_model.get_budgets_by_user(user_id)
    spending = transaction_model.get_category_spending_for_month(user_id, year_month)

    for b in budgets:
        spent = spending.get(b["category"], 0)
        if spent <= b["monthly_limit"]:
            continue
        ref_key = f"budget:{b['category']}:{year_month}"
        if notification_model.exists_by_ref(user_id, ref_key):
            continue
        notification_model.create_notification(
            user_id,
            "budget_exceeded",
            f"Over budget on {b['category']}",
            f"You've spent {spent:.2f} against a {b['monthly_limit']:.2f} limit this month.",
            ref_key,
        )


def _generate_bill_reminders(user_id):
    cutoff = (date.today() + timedelta(days=BILL_REMINDER_WINDOW_DAYS)).isoformat()
    for bill in bill_model.get_upcoming_unpaid(user_id, cutoff):
        ref_key = f"bill:{bill['id']}:{bill['due_date']}"
        if notification_model.exists_by_ref(user_id, ref_key):
            continue
        overdue = bill["due_date"] < date.today().isoformat()
        notification_model.create_notification(
            user_id,
            "bill_due",
            f"{'Overdue' if overdue else 'Upcoming'}: {bill['name']}",
            f"{bill['amount']:.2f} due on {bill['due_date']}.",
            ref_key,
        )


def generate_notifications(user):
    """Lazily materializes alerts the same way recurring transactions are
    caught up — no cron job, just checked whenever the user asks for them."""
    if user.get("notify_budget_alerts", True):
        _generate_budget_alerts(user["id"])
    if user.get("notify_bill_reminders", True):
        _generate_bill_reminders(user["id"])


def get_notifications(user):
    generate_notifications(user)
    return notification_model.get_notifications_by_user(user["id"])


def get_unread_count(user):
    generate_notifications(user)
    return notification_model.get_unread_count(user["id"])


def mark_read(notification_id, user_id):
    notification_model.mark_read(notification_id, user_id)


def mark_all_read(user_id):
    notification_model.mark_all_read(user_id)


def delete_notification(notification_id, user_id):
    notification_model.delete_notification(notification_id, user_id)
