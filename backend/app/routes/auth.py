from functools import wraps

from flask import Blueprint, g, jsonify, request

from app.services import authz_service, auth_service
from app.services.auth_service import AuthError

auth_bp = Blueprint("auth", __name__)


def _extract_token():
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[len("Bearer "):]
    return None


def login_required(f):
    """Looks up the user for the request's token and stashes it on flask.g.
    Returns 401 if there's no valid token, 403 if the account is suspended,
    503 if the platform is in maintenance mode and this user isn't an admin.
    Use on any route that needs a logged-in user."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        user = auth_service.get_user_from_token(_extract_token())
        if user is None:
            return jsonify({"error": "Authentication required"}), 401
        if user.get("is_suspended"):
            return jsonify({"error": "This account has been suspended"}), 403
        if auth_service.is_maintenance_mode() and not user.get("is_admin"):
            return jsonify({"error": "The platform is temporarily down for maintenance"}), 503
        g.current_user = user
        return f(*args, **kwargs)

    return wrapper


def admin_required(f):
    """Same as login_required, but also requires the user's is_admin flag.
    Returns 404 (not 403) for non-admins, so the admin API surface doesn't
    even reveal its own existence to a regular user. Kept for the
    pre-existing /api/admin/* routes; newer admin/super-admin routes use
    require_permission below, which returns proper 401/403 codes."""

    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if not g.current_user.get("is_admin"):
            return jsonify({"error": "Not found"}), 404
        return f(*args, **kwargs)

    return wrapper


def require_permission(permission_key):
    """Enforces a specific admin permission (see authz_service.PERMISSIONS).
    401 if not logged in, 403 if logged in but lacking the permission —
    distinct from admin_required's deliberate 404-obscurity, since these
    routes are meant to be testably distinguishable per the RBAC test suite."""

    def decorator(f):
        @wraps(f)
        @login_required
        def wrapper(*args, **kwargs):
            if not authz_service.has_permission(g.current_user, permission_key):
                return jsonify({"error": "Forbidden"}), 403
            return f(*args, **kwargs)

        return wrapper

    return decorator


def require_super_admin(f):
    """Hard role check (not just a permission grant) for the handful of
    actions that must never be reachable by a plain ADMIN, no matter how the
    permissions editor is configured — e.g. creating another SUPER_ADMIN."""

    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if not authz_service.is_super_admin(g.current_user):
            return jsonify({"error": "Forbidden"}), 403
        return f(*args, **kwargs)

    return wrapper


@auth_bp.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)
    try:
        user, token = auth_service.register(data)
    except AuthError as e:
        return jsonify({"error": e.message}), e.status_code
    return jsonify({"message": "Registered successfully", "user": user, "token": token}), 201


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    try:
        user, token = auth_service.login(data)
    except AuthError as e:
        return jsonify({"error": e.message}), e.status_code
    return jsonify({"message": "Logged in successfully", "user": user, "token": token}), 200


@auth_bp.route("/api/auth/google", methods=["POST"])
def google_login():
    data = request.get_json(silent=True) or {}
    try:
        user, token = auth_service.login_with_google(data.get("accessToken"))
    except AuthError as e:
        return jsonify({"error": e.message}), e.status_code
    return jsonify({"message": "Logged in successfully", "user": user, "token": token}), 200


@auth_bp.route("/api/auth/facebook", methods=["POST"])
def facebook_login():
    data = request.get_json(silent=True) or {}
    try:
        user, token = auth_service.login_with_facebook(data.get("accessToken"))
    except AuthError as e:
        return jsonify({"error": e.message}), e.status_code
    return jsonify({"message": "Logged in successfully", "user": user, "token": token}), 200


@auth_bp.route("/api/auth/firebase", methods=["POST"])
def firebase_login():
    data = request.get_json(silent=True) or {}
    try:
        user, token = auth_service.login_with_firebase(data.get("idToken"))
    except AuthError as e:
        return jsonify({"error": e.message}), e.status_code
    return jsonify({"message": "Logged in successfully", "user": user, "token": token}), 200


@auth_bp.route("/api/auth/me", methods=["GET"])
@login_required
def me():
    return jsonify({"user": auth_service.to_public_user(g.current_user)}), 200


@auth_bp.route("/api/auth/me", methods=["PUT"])
@login_required
def update_me():
    data = request.get_json(silent=True)
    try:
        user = auth_service.update_profile(g.current_user, data)
    except AuthError as e:
        return jsonify({"error": e.message}), e.status_code
    return jsonify({"message": "Profile updated successfully", "user": user}), 200


@auth_bp.route("/api/auth/logout", methods=["POST"])
@login_required
def logout():
    auth_service.logout(g.current_user)
    return jsonify({"message": "Logged out successfully"}), 200
