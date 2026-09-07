from datetime import datetime, timezone

from app.models import activity_log as activity_log_model
from app.models import budget as budget_model
from app.models import budget_share as budget_share_model
from app.models import transaction as transaction_model
from app.models import user as user_model
from app.services.errors import conflict, not_found


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


def share_budget(owner_user_id, category, data):
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")

    email = data.get("email")
    if not isinstance(email, str) or not email.strip():
        raise ValueError("Email is required")

    budget = budget_model.get_budget_by_user_and_category(owner_user_id, category)
    if budget is None:
        raise not_found("Budget not found")

    target = user_model.get_user_by_email(email.strip().lower())
    if target is None:
        raise not_found("No account with that email")
    if target["id"] == owner_user_id:
        raise ValueError("You can't share a budget with yourself")

    if budget_share_model.get_share(budget["id"], target["id"]) is not None:
        raise conflict("Already shared with that person")

    budget_share_model.create_share(budget["id"], owner_user_id, target["id"])
    activity_log_model.log(owner_user_id, "Shared budget", f"{category} with {target['email']}")
    return {"category": category, "shared_with_email": target["email"], "shared_with_name": target["name"]}


def get_budget_shares(owner_user_id, category):
    budget = budget_model.get_budget_by_user_and_category(owner_user_id, category)
    if budget is None:
        raise not_found("Budget not found")

    shares = budget_share_model.get_shares_for_budget(budget["id"])
    result = []
    for share in shares:
        user = user_model.get_user_by_id(share["shared_with_user_id"])
        if user:
            result.append({"user_id": user["id"], "name": user["name"], "email": user["email"]})
    return result


def unshare_budget(owner_user_id, category, shared_with_user_id):
    budget = budget_model.get_budget_by_user_and_category(owner_user_id, category)
    if budget is None:
        raise not_found("Budget not found")
    budget_share_model.delete_share(budget["id"], shared_with_user_id)
    activity_log_model.log(owner_user_id, "Unshared budget", category)


def get_budgets_shared_with_me(user_id):
    """Every budget shared with this user, each with the owner's current
    spending against it (this month) — the same read the owner sees, minus
    the ability to edit or delete."""
    year_month = datetime.now(timezone.utc).strftime("%Y-%m")
    shared = budget_share_model.get_budgets_shared_with_user(user_id)

    spending_by_owner = {}
    result = []
    for row in shared:
        owner_id = row["owner_user_id"]
        if owner_id not in spending_by_owner:
            spending_by_owner[owner_id] = transaction_model.get_category_spending_for_month(owner_id, year_month)
        result.append(
            {
                **row,
                "spent": spending_by_owner[owner_id].get(row["category"], 0),
            }
        )
    return result
