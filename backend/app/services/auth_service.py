import re
import secrets

from werkzeug.security import check_password_hash, generate_password_hash

from app.models import user as user_model

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 6


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


def register(data):
    clean = _validate_register_data(data)

    if user_model.get_user_by_email(clean["email"]):
        raise AuthError("Email is already registered", 409)

    password_hash = generate_password_hash(clean["password"])
    user = user_model.create_user(clean["name"], clean["email"], password_hash)

    token = secrets.token_hex(32)
    user_model.set_user_token(user["id"], token)

    return to_public_user(user), token


def login(data):
    if not isinstance(data, dict):
        raise AuthError("Request body must be a JSON object", 400)

    email = data.get("email")
    password = data.get("password")
    if not isinstance(email, str) or not isinstance(password, str):
        raise AuthError("Email and password are required", 400)

    user = user_model.get_user_by_email(email.strip().lower())
    if user is None or not check_password_hash(user["password_hash"], password):
        raise AuthError("Invalid email or password", 401)

    token = secrets.token_hex(32)
    user_model.set_user_token(user["id"], token)

    return to_public_user(user), token


def logout(user):
    user_model.set_user_token(user["id"], None)


def get_user_from_token(token):
    if not token:
        return None
    return user_model.get_user_by_token(token)
