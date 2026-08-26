from app.models import activity_log as activity_log_model
from app.models import category as category_model

MAX_NAME_LENGTH = 60


def get_categories(user_id):
    return category_model.get_categories_by_user(user_id)


def create_category(user_id, data):
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Name is required")
    if len(name.strip()) > MAX_NAME_LENGTH:
        raise ValueError(f"Name must be {MAX_NAME_LENGTH} characters or fewer")

    type_ = data.get("type")
    if type_ not in ("income", "expense"):
        raise ValueError("Type must be 'income' or 'expense'")

    color = data.get("color") or None
    if color is not None and (not isinstance(color, str) or len(color) > 20):
        raise ValueError("Color must be a short string (e.g. a hex code)")

    name = name.strip()
    existing = [c for c in category_model.get_categories_by_user(user_id) if c["name"] == name and c["type"] == type_]
    if existing:
        raise ValueError("That category already exists")

    category = category_model.create_category(user_id, name, type_, color)
    activity_log_model.log(user_id, "Created category", f"{name} ({type_})")
    return category


def delete_category(category_id, user_id):
    category_model.delete_category(category_id, user_id)
    activity_log_model.log(user_id, "Deleted category", f"#{category_id}")
