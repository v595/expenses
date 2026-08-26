from datetime import datetime

from app.models import goal as goal_model

MAX_NAME_LENGTH = 80


def get_goals(user_id):
    return goal_model.get_goals_by_user(user_id)


def create_goal(user_id, data):
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Name is required")
    if len(name.strip()) > MAX_NAME_LENGTH:
        raise ValueError(f"Name must be {MAX_NAME_LENGTH} characters or fewer")

    target_amount = data.get("target_amount")
    if not isinstance(target_amount, (int, float)) or isinstance(target_amount, bool):
        raise ValueError("Target amount must be a number")
    if target_amount <= 0:
        raise ValueError("Target amount must be greater than zero")

    target_date = data.get("target_date") or None
    if target_date is not None:
        if not isinstance(target_date, str):
            raise ValueError("Target date must be text")
        try:
            datetime.strptime(target_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Target date must be a valid date in YYYY-MM-DD format")

    return goal_model.create_goal(user_id, name.strip(), float(target_amount), target_date)


def add_funds(goal_id, user_id, data):
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")

    amount = data.get("amount")
    if not isinstance(amount, (int, float)) or isinstance(amount, bool):
        raise ValueError("Amount must be a number")
    if amount <= 0:
        raise ValueError("Amount must be greater than zero")

    updated = goal_model.add_funds(goal_id, user_id, float(amount))
    if updated is None:
        raise ValueError("Goal not found")
    return updated


def delete_goal(goal_id, user_id):
    goal_model.delete_goal(goal_id, user_id)
