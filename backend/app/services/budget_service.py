from datetime import datetime, timezone

from app.models import activity_log as activity_log_model
from app.models import budget as budget_model
from app.models import transaction as transaction_model


def get_budgets_with_spending(user_id):
    year_month = datetime.now(timezone.utc).strftime("%Y-%m")
    budgets = budget_model.get_budgets_by_user(user_id)
    spending = transaction_model.get_category_spending_for_month(user_id, year_month)

    return [
        {
            "category": b["category"],
            "monthly_limit": b["monthly_limit"],
            "spent": spending.get(b["category"], 0),
        }
        for b in budgets
    ]


def set_budget(user_id, data):
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")

    category = data.get("category")
    if not isinstance(category, str) or not category.strip():
        raise ValueError("Category is required")

    monthly_limit = data.get("monthly_limit")
    if not isinstance(monthly_limit, (int, float)) or isinstance(monthly_limit, bool):
        raise ValueError("Monthly limit must be a number")
    if monthly_limit <= 0:
        raise ValueError("Monthly limit must be greater than zero")

    budget_model.upsert_budget(user_id, category.strip(), float(monthly_limit))
    activity_log_model.log(user_id, "Set budget", f"{category.strip()} limit {float(monthly_limit):.2f}")


def delete_budget(user_id, category):
    budget_model.delete_budget(user_id, category)
    activity_log_model.log(user_id, "Deleted budget", category)
