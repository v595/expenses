import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone

import pyotp
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from app.config import Config
from app.models import activity_log as activity_log_model
from app.models import book as book_model
from app.models import system_setting as system_setting_model
from app.models import user as user_model
from app.services import email as email_service

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 6
MAX_AVATAR_LENGTH = 2_800_000  # ~2MB image, base64-encoded

# Sliding-window session length: every authenticated request pushes the
# token's expiry forward by this much (see login_required in routes/auth.py),
# so an active user is never logged out mid-session but a stolen/idle token
# stops working after this long of inactivity.
TOKEN_TTL = timedelta(days=7)

MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=15)

# Short-lived, stateless "you passed step 1, now give me your TOTP code"
# ticket — signed rather than stored, so no extra table/cleanup job is
# needed for it to expire on its own.
_TWO_FA_SALT = "2fa-pending-login"
TWO_FA_TICKET_TTL_SECONDS = 5 * 60


def _serializer():
    return URLSafeTimedSerializer(Config.SECRET_KEY)


def issue_2fa_ticket(user_id):
    return _serializer().dumps({"user_id": user_id}, salt=_TWO_FA_SALT)


def verify_2fa_ticket(ticket):
    try:
        data = _serializer().loads(ticket, salt=_TWO_FA_SALT, max_age=TWO_FA_TICKET_TTL_SECONDS)
    except (BadSignature, SignatureExpired):
        return None
    return data.get("user_id")


# Password reset tokens are signed the same way as the 2FA ticket — stateless,
# so no extra table/cleanup job — but with one addition: the token embeds a
# short fingerprint of the user's *current* password hash. Once the password
# actually changes (via this reset or any other path), the fingerprint no
# longer matches, so the token stops verifying on its own. That gives
# one-time-use semantics, and it means requesting a second reset email
# silently invalidates the first, for free.
_RESET_SALT = "password-reset"
RESET_TOKEN_TTL_SECONDS = 30 * 60


def _password_fingerprint(password_hash):
    return hashlib.sha256(password_hash.encode()).hexdigest()[:16]


def issue_password_reset_token(user):
    payload = {"user_id": user["id"], "pwd": _password_fingerprint(user["password_hash"])}
    return _serializer().dumps(payload, salt=_RESET_SALT)


def verify_password_reset_token(token):
    try:
        data = _serializer().loads(token, salt=_RESET_SALT, max_age=RESET_TOKEN_TTL_SECONDS)
    except (BadSignature, SignatureExpired):
        return None
    user = user_model.get_user_by_id(data.get("user_id"))
    if user is None or _password_fingerprint(user["password_hash"]) != data.get("pwd"):
        return None
    return user


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
        "totp_enabled": bool(user["totp_enabled"]) if "totp_enabled" in user.keys() else False,
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


def _now():
    return datetime.now(timezone.utc)


def _now_iso():
    return _now().strftime("%Y-%m-%d %H:%M:%S")


def _parse_iso(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def is_maintenance_mode():
    return system_setting_model.get("maintenance_mode", "false") == "true"


def _issue_session(user):
    """Common tail of every login path: clears lockout state, mints a fresh
    bearer token with a sliding expiry, and records the login. If the account
    has 2FA turned on, no token is issued yet — the caller gets a short-lived
    ticket instead and must complete `verify_two_factor` with a TOTP code."""
    if user.get("totp_enabled"):
        return {"requires_two_factor": True, "ticket": issue_2fa_ticket(user["id"])}

    return _finish_login(user)


def _finish_login(user):
    book_model.ensure_default_book(user["id"])
    user_model.reset_failed_logins(user["id"])

    token = secrets.token_hex(32)
    expires_at = (_now() + TOKEN_TTL).strftime("%Y-%m-%d %H:%M:%S")
    user_model.set_user_token(user["id"], token, expires_at)
    user_model.record_login(user["id"], _now_iso())

    fresh = user_model.get_user_by_id(user["id"])
    return {"user": to_public_user(fresh), "token": token}


def register(data):
    if is_maintenance_mode():
        raise AuthError("The platform is temporarily down for maintenance", 503)

    clean = _validate_register_data(data)

    if user_model.get_user_by_email(clean["email"]):
        raise AuthError("Email is already registered", 409)

    password_hash = generate_password_hash(clean["password"])
    user = user_model.create_user(clean["name"], clean["email"], password_hash)
    user_model.promote_first_user_if_no_admin()
    book_model.ensure_default_book(user["id"])
    user = user_model.get_user_by_id(user["id"])

    token = secrets.token_hex(32)
    expires_at = (_now() + TOKEN_TTL).strftime("%Y-%m-%d %H:%M:%S")
    user_model.set_user_token(user["id"], token, expires_at)
    user_model.record_login(user["id"], _now_iso())
    activity_log_model.log(user["id"], "Registered")

    fresh = user_model.get_user_by_id(user["id"])
    return to_public_user(fresh), token


def request_password_reset(email):
    if not isinstance(email, str) or not EMAIL_PATTERN.match(email):
        raise AuthError("A valid email is required", 400)

    user = user_model.get_user_by_email(email.strip().lower())
    # Deliberately silent for an unknown email or an account with no local
    # password (social-only sign-in) — responding differently would let
    # anyone probe which emails have an account here.
    if user is not None and not user.get("is_suspended"):
        token = issue_password_reset_token(user)
        reset_url = f"{Config.FRONTEND_URL}/reset-password?token={token}"
        subject, body = email_service.templates.password_reset_email(user["name"], reset_url)
        email_service.send(user["email"], subject, body)
        activity_log_model.log(user["id"], "Requested password reset", entity_type="security")


def reset_password(token, new_password):
    if not isinstance(new_password, str) or len(new_password) < MIN_PASSWORD_LENGTH:
        raise AuthError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters", 400)

    user = verify_password_reset_token(token) if isinstance(token, str) else None
    if user is None:
        raise AuthError("This reset link is invalid or has expired", 400)

    user_model.update_password(user["id"], generate_password_hash(new_password))
    # Force re-login everywhere — a password reset (often prompted by a
    # compromised account) shouldn't leave an old session still valid.
    user_model.set_user_token(user["id"], None)
    activity_log_model.log(user["id"], "Reset password via email link", entity_type="security")


def login(data):
    if not isinstance(data, dict):
        raise AuthError("Request body must be a JSON object", 400)

    email = data.get("email")
    password = data.get("password")
    if not isinstance(email, str) or not isinstance(password, str):
        raise AuthError("Email and password are required", 400)

    email_clean = email.strip().lower()
    user = user_model.get_user_by_email(email_clean)

    locked_until = _parse_iso(user.get("locked_until")) if user else None
    if locked_until and _now() < locked_until:
        minutes_left = max(1, int((locked_until - _now()).total_seconds() // 60) + 1)
        activity_log_model.log(user["id"], "Login rejected (account locked)", entity_type="security")
        raise AuthError(
            f"Too many failed attempts. Try again in {minutes_left} minute(s).", 429
        )

    if user is None or not check_password_hash(user["password_hash"], password):
        if user is not None:
            attempts = user_model.register_failed_login(user["id"])
            if attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
                new_lock = (_now() + LOCKOUT_DURATION).strftime("%Y-%m-%d %H:%M:%S")
                user_model.register_failed_login(user["id"], locked_until=new_lock)
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

    result = _issue_session(user)
    if result.get("requires_two_factor"):
        activity_log_model.log(user["id"], "Password verified, awaiting 2FA code", entity_type="security")
        return result

    activity_log_model.log(user["id"], "Logged in")
    return result


def verify_totp_code(user, code):
    """Shared by every 2FA check point (bearer-token login, admin dashboard
    login, enable/disable) — the one place that knows how to check a code
    against a user's secret."""
    return bool(user.get("totp_secret")) and pyotp.TOTP(user["totp_secret"]).verify(
        (code or "").strip() if isinstance(code, str) else "", valid_window=1
    )


def verify_two_factor(ticket, code):
    user_id = verify_2fa_ticket(ticket) if isinstance(ticket, str) else None
    if user_id is None:
        raise AuthError("This sign-in attempt has expired. Please log in again.", 401)

    user = user_model.get_user_by_id(user_id)
    if user is None or not user.get("totp_enabled"):
        raise AuthError("This sign-in attempt has expired. Please log in again.", 401)

    if not verify_totp_code(user, code):
        activity_log_model.log(user["id"], "Failed 2FA verification", entity_type="security")
        raise AuthError("Invalid authentication code", 401)

    result = _finish_login(user)
    activity_log_model.log(user["id"], "Logged in (2FA)")
    return result


def _login_or_create_from_social(profile):
    """Shared by Google/Facebook sign-in: log in if an account with this
    email already exists (linking the social login to it), otherwise create
    one. Social accounts get a random, never-typed password hash — they
    simply can't log in with a password until they set one from Profile."""
    if is_maintenance_mode():
        raise AuthError("The platform is temporarily down for maintenance", 503)

    email = profile["email"]
    user = user_model.get_user_by_email(email)

    if user is None:
        password_hash = generate_password_hash(secrets.token_urlsafe(32))
        created = user_model.create_user(profile["name"], email, password_hash)
        user_model.promote_first_user_if_no_admin()
        user = user_model.get_user_by_id(created["id"])
        activity_log_model.log(user["id"], "Registered via social sign-in")

    if user.get("is_suspended"):
        raise AuthError("This account has been suspended", 403)

    result = _issue_session(user)
    if result.get("requires_two_factor"):
        activity_log_model.log(user["id"], "Social sign-in verified, awaiting 2FA code", entity_type="security")
        return result

    activity_log_model.log(user["id"], "Logged in via social sign-in")
    return result


def login_with_google(access_token):
    from app.services import social_auth_service

    profile = social_auth_service.verify_google_access_token(access_token)
    return _login_or_create_from_social(profile)


def login_with_facebook(access_token):
    from app.services import social_auth_service

    profile = social_auth_service.verify_facebook_access_token(access_token)
    return _login_or_create_from_social(profile)


def login_with_firebase(id_token):
    """Handles both Firebase sign-in methods (email/password and Google) —
    Firebase itself already checked the password or the Google identity, so
    all that's left is verifying its token and mapping to our own user."""
    from app.firebase import verify_firebase_id_token

    if not id_token or not isinstance(id_token, str):
        raise AuthError("Missing Firebase ID token", 400)

    try:
        decoded = verify_firebase_id_token(id_token)
    except Exception as e:
        raise AuthError("Could not verify Firebase credential", 401) from e

    email = decoded.get("email")
    if not email:
        raise AuthError("Your Firebase account has no email attached", 401)

    name = decoded.get("name") or email.split("@")[0]
    return _login_or_create_from_social({"email": email.strip().lower(), "name": name})


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
    user = user_model.get_user_by_token(token)
    if user is None:
        return None

    expires_at = _parse_iso(user.get("token_expires_at"))
    if expires_at is not None and _now() >= expires_at:
        # Expired: clear it so the dead token can't be reused, and treat
        # this request as unauthenticated.
        user_model.set_user_token(user["id"], None)
        return None

    # Sliding window: every authenticated request extends the session, so an
    # actively-used token never expires mid-work.
    new_expiry = (_now() + TOKEN_TTL).strftime("%Y-%m-%d %H:%M:%S")
    user_model.touch_token_expiry(user["id"], new_expiry)
    return user


TOTP_ISSUER = "Hisaab"


def setup_two_factor(user):
    """Generates (and persists) a fresh TOTP secret for the user, not yet
    enabled — `enable_two_factor` must verify a code against it first. Safe
    to call again before enabling (e.g. user reloads the setup screen); each
    call rotates the secret so only the most recently shown QR code works."""
    secret = pyotp.random_base32()
    user_model.set_totp_secret(user["id"], secret)
    uri = pyotp.TOTP(secret).provisioning_uri(name=user["email"], issuer_name=TOTP_ISSUER)
    return {"secret": secret, "otpauth_url": uri}


def enable_two_factor(user, code):
    secret = user.get("totp_secret")
    if not secret:
        raise AuthError("Start setup first", 400)
    if not isinstance(code, str) or not pyotp.TOTP(secret).verify(code.strip(), valid_window=1):
        raise AuthError("Invalid authentication code", 400)

    updated = user_model.set_totp_enabled(user["id"], True)
    activity_log_model.log(user["id"], "Enabled two-factor authentication")
    return to_public_user(updated)


def disable_two_factor(user, password, code):
    if not isinstance(password, str) or not check_password_hash(user["password_hash"], password):
        raise AuthError("Current password is incorrect", 401)
    secret = user.get("totp_secret")
    if secret and (not isinstance(code, str) or not pyotp.TOTP(secret).verify(code.strip(), valid_window=1)):
        raise AuthError("Invalid authentication code", 400)

    updated = user_model.set_totp_enabled(user["id"], False)
    activity_log_model.log(user["id"], "Disabled two-factor authentication")
    return to_public_user(updated)
