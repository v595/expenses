import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Blueprint, current_app, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import role as role_model
from app.models import user as user_model
from app.services import admin_service, authz_service, feature_flag_service, system_settings_service
from app.services.settings_service import ALLOWED_CURRENCIES

admin_dashboard_bp = Blueprint("admin_dashboard", __name__)

SESSION_KEY = "dashboard_admin_id"
RESET_TOKEN_TTL = timedelta(minutes=30)

# In-memory reset-token store: token -> {"user_id": int, "expires": datetime}.
# There's no outbound email in this app, so a reset "sends" by logging the
# link server-side instead. Fine for a single-process dev app; an in-memory
# store means links don't survive a restart, which is an acceptable trade-off
# here since anyone can just request a new one.
_reset_tokens = {}


def _time_ago(timestamp_str):
    """Turns a stored 'YYYY-MM-DD HH:MM:SS' UTC timestamp into a short
    relative label, e.g. '3h ago' — mirrors the frontend's own timeAgo util."""
    if not timestamp_str:
        return "Never"
    try:
        then = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return timestamp_str
    seconds = (datetime.now(timezone.utc) - then).total_seconds()
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h ago"
    if seconds < 2592000:
        return f"{int(seconds // 86400)}d ago"
    return then.strftime("%b %d, %Y")


def dashboard_admin_required(f):
    """Session-cookie auth for the server-rendered dashboard — separate from
    the bearer-token auth the JSON API uses, since a plain browser navigation
    to a URL has no way to attach an Authorization header."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        user_id = session.get(SESSION_KEY)
        user = user_model.get_user_by_id(user_id) if user_id else None
        if user is None or not user.get("is_admin"):
            session.pop(SESSION_KEY, None)
            return redirect(url_for("admin_dashboard.login"))
        return f(*args, **kwargs)

    return wrapper


def dashboard_permission_required(permission_key):
    """Same session auth as dashboard_admin_required, plus a specific
    permission — renders a 403 page rather than redirecting, since the user
    IS a logged-in admin, just not one allowed to see this page."""

    def decorator(f):
        @wraps(f)
        @dashboard_admin_required
        def wrapper(*args, **kwargs):
            user = user_model.get_user_by_id(session[SESSION_KEY])
            if not authz_service.has_permission(user, permission_key):
                return _render("admin_forbidden.html", None), 403
            return f(*args, **kwargs)

        return wrapper

    return decorator


def _build_nav(user):
    def has(key):
        return authz_service.has_permission(user, key)

    sections = [
        {
            "label": "Overview",
            "links": [{"key": "dashboard", "title": "Dashboard", "url": url_for("admin_dashboard.dashboard")}],
        }
    ]

    security_items = []
    if has("audit_logs.view"):
        security_items.append(
            {"key": "audit-logs", "title": "Audit Logs", "url": url_for("admin_dashboard.audit_logs")}
        )
        security_items.append(
            {"key": "security-events", "title": "Security Events", "url": url_for("admin_dashboard.security_events")}
        )
    if security_items:
        sections.append({"label": "Security", "links": security_items})

    admin_items = []
    if has("admins.view"):
        admin_items.append({"key": "admins", "title": "Admins", "url": url_for("admin_dashboard.admins")})
    if has("roles.view"):
        admin_items.append({"key": "roles", "title": "Roles & Permissions", "url": url_for("admin_dashboard.roles")})
    if admin_items:
        sections.append({"label": "Administration", "links": admin_items})

    system_items = []
    if has("feature_flags.view"):
        system_items.append(
            {"key": "feature-flags", "title": "Feature Flags", "url": url_for("admin_dashboard.feature_flags")}
        )
    if has("settings.view"):
        system_items.append(
            {"key": "system-settings", "title": "System Settings", "url": url_for("admin_dashboard.system_settings")}
        )
    if has("system_health.view"):
        system_items.append(
            {"key": "system-health", "title": "System Health", "url": url_for("admin_dashboard.system_health")}
        )
    if system_items:
        sections.append({"label": "System", "links": system_items})

    return sections


def _render(template, active_nav, **context):
    user = user_model.get_user_by_id(session[SESSION_KEY])
    return render_template(
        template,
        nav_sections=_build_nav(user),
        active_nav=active_nav,
        admin_name=user["name"],
        admin_avatar=user["name"][:1].upper(),
        admin_role=user.get("role_name") or "Admin",
        current_admin_id=session[SESSION_KEY],
        current_admin=user,
        **context,
    )


@admin_dashboard_bp.route("/admin/login", methods=["GET", "POST"])
def login():
    if session.get(SESSION_KEY):
        return redirect(url_for("admin_dashboard.dashboard"))

    error = None
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        user = user_model.get_user_by_email(email)
        if user and check_password_hash(user["password_hash"], password):
            if user.get("is_suspended"):
                error = "This account has been suspended."
            elif user.get("is_admin"):
                session[SESSION_KEY] = user["id"]
                user_model.record_login(user["id"], datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
                return redirect(url_for("admin_dashboard.dashboard"))
            else:
                error = "That account doesn't have admin access."
        else:
            error = "Invalid email or password."

    return render_template("admin_login.html", error=error)


@admin_dashboard_bp.route("/admin/logout")
def logout():
    session.pop(SESSION_KEY, None)
    return redirect(url_for("admin_dashboard.login"))


@admin_dashboard_bp.route("/admin/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if session.get(SESSION_KEY):
        return redirect(url_for("admin_dashboard.dashboard"))

    message = None
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        user = user_model.get_user_by_email(email)
        if user and user.get("is_admin") and not user.get("is_suspended"):
            token = secrets.token_urlsafe(32)
            _reset_tokens[token] = {
                "user_id": user["id"],
                "expires": datetime.now(timezone.utc) + RESET_TOKEN_TTL,
            }
            reset_url = url_for("admin_dashboard.reset_password", token=token, _external=True)
            current_app.logger.info("Admin password reset link for %s: %s", email, reset_url)
        # Same message whether or not the account exists, so this page can't be
        # used to check which emails have admin access.
        message = "If that email has admin access, a reset link has been printed to the server console."

    return render_template("admin_forgot_password.html", message=message)


@admin_dashboard_bp.route("/admin/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    entry = _reset_tokens.get(token)
    if not entry or entry["expires"] < datetime.now(timezone.utc):
        _reset_tokens.pop(token, None)
        return render_template("admin_reset_password.html", expired=True, error=None)

    error = None
    if request.method == "POST":
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""
        if len(password) < 6:
            error = "Password must be at least 6 characters."
        elif password != confirm:
            error = "Passwords don't match."
        else:
            user_model.update_password(entry["user_id"], generate_password_hash(password))
            _reset_tokens.pop(token, None)
            return redirect(url_for("admin_dashboard.login"))

    return render_template("admin_reset_password.html", expired=False, error=error)


@admin_dashboard_bp.route("/admin")
@dashboard_admin_required
def dashboard():
    search = (request.args.get("q") or "").strip()
    stats = admin_service.get_stats()
    users = admin_service.list_users(search=search or None)

    for u in users:
        u["last_login_label"] = _time_ago(u["last_login_at"])

    max_signups = max((m["count"] for m in stats["signups_by_month"]), default=1) or 1

    activity = admin_service.get_recent_activity(50)
    for a in activity:
        a["time_label"] = _time_ago(a["created_at"])

    return _render(
        "admin_dashboard.html",
        "dashboard",
        stats=stats,
        users=users,
        activity=activity,
        max_signups=max_signups,
        search=search,
    )


@admin_dashboard_bp.route("/admin/users/<int:user_id>/activity")
@dashboard_admin_required
def user_activity(user_id):
    user = admin_service.get_user(user_id)
    if user is None:
        return redirect(url_for("admin_dashboard.dashboard"))

    activity = admin_service.get_user_activity(user_id, 200)
    for a in activity:
        a["time_label"] = _time_ago(a["created_at"])

    return _render("admin_user_activity.html", "dashboard", target_user=user, activity=activity)


@admin_dashboard_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@dashboard_admin_required
def delete_user(user_id):
    try:
        admin_service.delete_user(user_id, session[SESSION_KEY])
    except ValueError:
        pass  # tried to delete their own account — silently ignored on this view
    return redirect(url_for("admin_dashboard.dashboard"))


@admin_dashboard_bp.route("/admin/users/<int:user_id>/suspend", methods=["POST"])
@dashboard_permission_required("users.suspend")
def suspend_user(user_id):
    current_admin = user_model.get_user_by_id(session[SESSION_KEY])
    try:
        admin_service.suspend_user(user_id, current_admin)
    except ValueError:
        pass
    return redirect(url_for("admin_dashboard.dashboard"))


@admin_dashboard_bp.route("/admin/users/<int:user_id>/activate", methods=["POST"])
@dashboard_permission_required("users.suspend")
def activate_user(user_id):
    current_admin = user_model.get_user_by_id(session[SESSION_KEY])
    try:
        admin_service.activate_user(user_id, current_admin)
    except ValueError:
        pass
    return redirect(url_for("admin_dashboard.dashboard"))


@admin_dashboard_bp.route("/admin/admins")
@dashboard_permission_required("admins.view")
def admins():
    admin_list = admin_service.list_admins()
    return _render("admin_admins.html", "admins", admins=admin_list, error=None)


@admin_dashboard_bp.route("/admin/admins/new", methods=["GET", "POST"])
@dashboard_permission_required("admins.create")
def new_admin():
    current_admin = user_model.get_user_by_id(session[SESSION_KEY])
    error = None
    if request.method == "POST":
        try:
            admin_service.create_admin_user(
                request.form.get("name"),
                request.form.get("email"),
                request.form.get("password"),
                request.form.get("role"),
                current_admin,
            )
            return redirect(url_for("admin_dashboard.admins"))
        except ValueError as e:
            error = str(e)

    return _render(
        "admin_new_admin.html",
        "admins",
        error=error,
        can_create_super_admin=authz_service.is_super_admin(current_admin),
    )


@admin_dashboard_bp.route("/admin/admins/<int:user_id>/disable", methods=["POST"])
@dashboard_permission_required("admins.disable")
def disable_admin(user_id):
    current_admin = user_model.get_user_by_id(session[SESSION_KEY])
    try:
        admin_service.disable_admin(user_id, current_admin)
    except ValueError:
        pass
    return redirect(url_for("admin_dashboard.admins"))


@admin_dashboard_bp.route("/admin/admins/<int:user_id>/activate", methods=["POST"])
@dashboard_permission_required("admins.disable")
def activate_admin(user_id):
    current_admin = user_model.get_user_by_id(session[SESSION_KEY])
    try:
        admin_service.activate_admin(user_id, current_admin)
    except ValueError:
        pass
    return redirect(url_for("admin_dashboard.admins"))


@admin_dashboard_bp.route("/admin/roles", methods=["GET", "POST"])
@dashboard_permission_required("roles.view")
def roles():
    current_admin = user_model.get_user_by_id(session[SESSION_KEY])
    can_manage = authz_service.has_permission(current_admin, "roles.manage")
    error = None

    if request.method == "POST":
        if not can_manage:
            return _render("admin_forbidden.html", "roles"), 403
        role_id = int(request.form.get("role_id"))
        selected_keys = request.form.getlist("permission")
        role_model.set_role_permissions(role_id, selected_keys)
        return redirect(url_for("admin_dashboard.roles"))

    return _render(
        "admin_roles.html",
        "roles",
        role_list=role_model.list_roles_with_counts(),
        all_permissions=authz_service.PERMISSIONS,
        can_manage=can_manage,
        error=error,
    )


@admin_dashboard_bp.route("/admin/feature-flags", methods=["GET"])
@dashboard_permission_required("feature_flags.view")
def feature_flags():
    current_admin = user_model.get_user_by_id(session[SESSION_KEY])
    return _render(
        "admin_feature_flags.html",
        "feature-flags",
        flags=feature_flag_service.list_flags(),
        can_manage=authz_service.has_permission(current_admin, "feature_flags.manage"),
    )


@admin_dashboard_bp.route("/admin/feature-flags/<key>/toggle", methods=["POST"])
@dashboard_permission_required("feature_flags.manage")
def toggle_feature_flag(key):
    current_admin = user_model.get_user_by_id(session[SESSION_KEY])
    enabled = request.form.get("enabled") == "true"
    try:
        feature_flag_service.set_enabled(key, not enabled, current_admin["id"])
    except ValueError:
        pass
    return redirect(url_for("admin_dashboard.feature_flags"))


@admin_dashboard_bp.route("/admin/system-settings", methods=["GET", "POST"])
@dashboard_permission_required("settings.view")
def system_settings():
    current_admin = user_model.get_user_by_id(session[SESSION_KEY])
    can_manage = authz_service.has_permission(current_admin, "settings.manage")
    error = None

    if request.method == "POST":
        if not can_manage:
            return _render("admin_forbidden.html", "system-settings"), 403
        try:
            system_settings_service.update_settings(
                {
                    "app_name": request.form.get("app_name"),
                    "default_currency": request.form.get("default_currency"),
                    "maintenance_mode": request.form.get("maintenance_mode") == "on",
                },
                current_admin["id"],
            )
        except ValueError as e:
            error = str(e)

    return _render(
        "admin_system_settings.html",
        "system-settings",
        settings=system_settings_service.get_all(),
        can_manage=can_manage,
        error=error,
        currencies=ALLOWED_CURRENCIES,
    )


@admin_dashboard_bp.route("/admin/system-health")
@dashboard_permission_required("system_health.view")
def system_health():
    return _render("admin_system_health.html", "system-health", health=admin_service.get_system_health())


@admin_dashboard_bp.route("/admin/audit-logs")
@dashboard_permission_required("audit_logs.view")
def audit_logs():
    admin_only = request.args.get("scope", "admin") == "admin"
    entries = admin_service.get_audit_log(limit=200, admin_actions_only=admin_only)
    for e in entries:
        e["time_label"] = _time_ago(e["created_at"])
    return _render("admin_audit_logs.html", "audit-logs", entries=entries, admin_only=admin_only)


@admin_dashboard_bp.route("/admin/security-events")
@dashboard_permission_required("audit_logs.view")
def security_events():
    entries = admin_service.get_security_events(limit=200)
    for e in entries:
        e["time_label"] = _time_ago(e["created_at"])
    return _render("admin_security_events.html", "security-events", entries=entries)
