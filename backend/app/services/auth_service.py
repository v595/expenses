import re
import secrets
from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from app.models import activity_log as activity_log_model
from app.models import system_setting as system_setting_model
from app.models import user as user_model

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 6
MAX_AVATAR_LENGTH = 2_800_000  # ~2MB image, base64-encoded


class AuthError(Exception):
    """Raised for any auth failure. status_code tells the route what to return."""

    def __init__(self, message, status_code):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def to_public_user(user):
    """Strip sensitive fields (password_hash, token) before sending a user to the client."""
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "created_at": user["created_at"],
        "avatar": user["avatar"] if "avatar" in user.keys() else None,
        "is_admin": bool(user["is_admin"]) if "is_admin" in user.keys() else False,
        "currency": user["currency"] if "currency" in user.keys() and user["currency"] else "USD",
        "notify_budget_alerts": bool(user["notify_budget_alerts"])
        if "notify_budget_alerts" in user.keys()
        else True,
        "notify_bill_reminders": bool(user["notify_bill_reminders"])
        if "notify_bill_reminders" in user.keys()
        else True,
        "role_id": user["role_id"] if "role_id" in user.keys() else None,
        "role_name": user["role_name"] if "role_name" in user.keys() else None,
        "is_suspended": bool(user["is_suspended"]) if "is_suspended" in user.keys() else False,
        "last_login_at": user["last_login_at"] if "last_login_at" in user.keys() else None,
    }


def _validate_register_data(data):
    if not isinstance(data, dict):
        raise AuthError("Request body must be a JSON object", 400)

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        raise AuthError("Name is required", 400)

    email = data.get("email")
    if not isinstance(email, str) or not EMAIL_PATTERN.match(email):
        raise AuthError("A valid email is required", 400)

    password = data.get("password")
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise AuthError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters", 400)

    return {"name": name.strip(), "email": email.strip().lower(), "password": password}


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def is_maintenance_mode():
    return system_setting_model.get("maintenance_mode", "false") == "true"


def register(data):
    if is_maintenance_mode():
        raise AuthError("The platform is temporarily down for maintenance", 503)

    clean = _validate_register_data(data)

    if user_model.get_user_by_email(clean["email"]):
        raise AuthError("Email is already registered", 409)

    password_hash = generate_password_hash(clean["password"])
    user = user_model.create_user(clean["name"], clean["email"], password_hash)
    user_model.promote_first_user_if_no_admin()
    user = user_model.get_user_by_id(user["id"])

    token = secrets.token_hex(32)
    user_model.set_user_token(user["id"], token)
    user_model.record_login(user["id"], _now_iso())
    activity_log_model.log(user["id"], "Registered")

    return to_public_user(user), token


def login(data):
    if not isinstance(data, dict):
        raise AuthError("Request body must be a JSON object", 400)

    email = data.get("email")
    password = data.get("password")
    if not isinstance(email, str) or not isinstance(password, str):
        raise AuthError("Email and password are required", 400)

    email_clean = email.strip().lower()
    user = user_model.get_user_by_email(email_clean)
    if user is None or not check_password_hash(user["password_hash"], password):
        activity_log_model.log(
            user["id"] if user else None,
            "Failed login attempt",
            email_clean,
            entity_type="security",
        )
        raise AuthError("Invalid email or password", 401)

    if user.get("is_suspended"):
        activity_log_model.log(user["id"], "Login rejected (account suspended)", entity_type="security")
        raise AuthError("This account has been suspended", 403)

    if is_maintenance_mode() and not user.get("is_admin"):
        raise AuthError("The platform is temporarily down for maintenance", 503)

    token = secrets.token_hex(32)
    user_model.set_user_token(user["id"], token)
    user_model.record_login(user["id"], _now_iso())
    activity_log_model.log(user["id"], "Logged in")

    return to_public_user(user), token


def update_profile(user, data):
    if not isinstance(data, dict):
        raise AuthError("Request body must be a JSON object", 400)

    updated = user

    name = data.get("name")
    if name is not None:
        if not isinstance(name, str) or not name.strip():
            raise AuthError("Name cannot be empty", 400)
        updated = user_model.update_name(user["id"], name.strip())
        activity_log_model.log(user["id"], "Updated profile name", name.strip())

    avatar = data.get("avatar")
    if avatar is not None:
        if not isinstance(avatar, str) or not avatar.startswith("data:image/"):
            raise AuthError("Avatar must be an image", 400)
        if len(avatar) > MAX_AVATAR_LENGTH:
            raise AuthError("Image is too large (max ~2MB)", 400)
        updated = user_model.update_avatar(user["id"], avatar)
        activity_log_model.log(user["id"], "Updated profile picture")

    new_password = data.get("new_password")
    if new_password is not None:
        current_password = data.get("current_password")
        if not isinstance(current_password, str) or not check_password_hash(
            user["password_hash"], current_password
        ):
            raise AuthError("Current password is incorrect", 401)
        if not isinstance(new_password, str) or len(new_password) < MIN_PASSWORD_LENGTH:
            raise AuthError(f"New password must be at least {MIN_PASSWORD_LENGTH} characters", 400)
        user_model.update_password(user["id"], generate_password_hash(new_password))
        activity_log_model.log(user["id"], "Changed password")

    return to_public_user(updated)


def logout(user):
    user_model.set_user_token(user["id"], None)
    activity_log_model.log(user["id"], "Logged out")


def get_user_from_token(token):
    if not token:
        return None
    return user_model.get_user_by_token(token)
