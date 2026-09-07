import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Blueprint, current_app, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import limiter
from app.models import activity_log as activity_log_model
from app.models import role as role_model
from app.models import user as user_model
from app.services import admin_service, auth_service, authz_service, feature_flag_service, system_settings_service
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


def _establish_admin_session(user):
    session[SESSION_KEY] = user["id"]
    user_model.record_login(user["id"], datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))


@admin_dashboard_bp.route("/admin/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
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
                activity_log_model.log(
                    user["id"], "Login rejected (account suspended)", entity_type="security"
                )
                error = "This account has been suspended."
            elif user.get("is_admin"):
                if user.get("totp_enabled"):
                    # Password alone doesn't establish the session — the
                    # admin dashboard must honor 2FA exactly like the main
                    # app's login, since admin accounts are the highest-value
                    # target in the whole system.
                    activity_log_model.log(
                        user["id"], "Admin password verified, awaiting 2FA code", entity_type="security"
                    )
                    ticket = auth_service.issue_2fa_ticket(user["id"])
                    return render_template("admin_login_2fa.html", ticket=ticket, error=None)
                _establish_admin_session(user)
                activity_log_model.log(user["id"], "Logged in to admin dashboard")
                return redirect(url_for("admin_dashboard.dashboard"))
            else:
                error = "That account doesn't have admin access."
        else:
            activity_log_model.log(
                user["id"] if user else None,
                "Failed admin login attempt",
                email,
                entity_type="security",
            )
            error = "Invalid email or password."

    return render_template("admin_login.html", error=error)


@admin_dashboard_bp.route("/admin/login/2fa", methods=["POST"])
@limiter.limit("10 per minute")
def login_2fa():
    if session.get(SESSION_KEY):
        return redirect(url_for("admin_dashboard.dashboard"))

    ticket = request.form.get("ticket") or ""
    code = request.form.get("code") or ""

    user_id = auth_service.verify_2fa_ticket(ticket)
    user = user_model.get_user_by_id(user_id) if user_id else None

    if user is None or not user.get("totp_enabled"):
        # The ticket expired (5 minutes) or was tampered with — send them
        # back to start rather than showing a dead form with no way forward.
        return render_template(
            "admin_login_2fa.html", ticket=None, error="This sign-in attempt has expired. Please log in again."
        )

    if user.get("is_suspended") or not user.get("is_admin"):
        return redirect(url_for("admin_dashboard.login"))

    if not auth_service.verify_totp_code(user, code):
        activity_log_model.log(user["id"], "Failed admin 2FA verification", entity_type="security")
        return render_template(
            "admin_login_2fa.html", ticket=ticket, error="Invalid authentication code."
        )

    _establish_admin_session(user)
    activity_log_model.log(user["id"], "Logged in to admin dashboard (2FA)")
    return redirect(url_for("admin_dashboard.dashboard"))


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


def _user_list_params():
    """Query params shared by the dashboard table and its CSV export, so
    "export what I'm currently looking at" actually matches."""
    search = (request.args.get("q") or "").strip()
    role = (request.args.get("role") or "").strip().upper()
    if role not in admin_service.VALID_ROLE_NAMES:
        role = None
    status = (request.args.get("status") or "").strip().lower()
    if status not in ("online", "offline", "suspended"):
        status = None
    sort = request.args.get("sort") or "name"
    if sort not in admin_service.USER_SORT_COLUMNS:
        sort = "name"
    direction = "desc" if request.args.get("dir") == "desc" else "asc"
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except ValueError:
        page = 1
    return {"search": search, "role": role, "status": status, "sort": sort, "direction": direction, "page": page}


@admin_dashboard_bp.route("/admin")
@dashboard_admin_required
def dashboard():
    params = _user_list_params()
    stats = admin_service.get_stats()
    users = admin_service.list_users(
        search=params["search"] or None,
        role=params["role"],
        status=params["status"],
        sort=params["sort"],
        direction=params["direction"],
        page=params["page"],
    )
    total_users = admin_service.count_users(search=params["search"] or None, role=params["role"], status=params["status"])
    total_pages = max((total_users + admin_service.USER_PAGE_SIZE - 1) // admin_service.USER_PAGE_SIZE, 1)

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
        search=params["search"],
        role_filter=params["role"] or "",
        status_filter=params["status"] or "",
        sort=params["sort"],
        direction=params["direction"],
        page=params["page"],
        total_pages=total_pages,
        total_users=total_users,
        role_names=admin_service.VALID_ROLE_NAMES,
    )


@admin_dashboard_bp.route("/admin/users/export.csv")
@dashboard_admin_required
def export_users_csv():
    import csv
    import io

    params = _user_list_params()
    users = admin_service.list_users_for_export(
        search=params["search"] or None, role=params["role"], status=params["status"],
        sort=params["sort"], direction=params["direction"],
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Name", "Email", "Role", "Joined", "Last Login", "Status", "Transactions", "Income", "Expenses"])
    for u in users:
        writer.writerow([
            u["name"], u["email"], u["role_name"] or "USER", u["created_at"],
            u["last_login_at"] or "Never",
            "Suspended" if u["is_suspended"] else ("Online" if u["is_logged_in"] else "Offline"),
            u["transaction_count"], f"{u['income']:.2f}", f"{u['expenses']:.2f}",
        ])

    response = current_app.response_class(buffer.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=users.csv"
    return response


def _redirect_back(fallback_endpoint, **fallback_args):
    """Returns to wherever the action was triggered from (dashboard row,
    or the user's own activity page) instead of always bouncing to one
    fixed place — same-origin referrers only, to avoid an open redirect."""
    referrer = request.referrer
    if referrer and referrer.startswith(request.host_url):
        return redirect(referrer)
    return redirect(url_for(fallback_endpoint, **fallback_args))


@admin_dashboard_bp.route("/admin/users/<int:user_id>/role", methods=["POST"])
@dashboard_permission_required("users.update")
def change_user_role(user_id):
    current_admin = user_model.get_user_by_id(session[SESSION_KEY])
    try:
        admin_service.change_user_role(user_id, request.form.get("role", ""), current_admin)
    except ValueError:
        pass
    return _redirect_back("admin_dashboard.dashboard", **request.args)


@admin_dashboard_bp.route("/admin/users/<int:user_id>/activity")
@dashboard_admin_required
def user_activity(user_id):
    user = admin_service.get_user(user_id)
    if user is None:
        return redirect(url_for("admin_dashboard.dashboard"))

    activity = admin_service.get_user_activity(user_id, 200)
    for a in activity:
        a["time_label"] = _time_ago(a["created_at"])

    return _render(
        "admin_user_activity.html", "dashboard", target_user=user, activity=activity,
        role_names=admin_service.VALID_ROLE_NAMES,
    )


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
    return _redirect_back("admin_dashboard.dashboard")


@admin_dashboard_bp.route("/admin/users/<int:user_id>/activate", methods=["POST"])
@dashboard_permission_required("users.suspend")
def activate_user(user_id):
    current_admin = user_model.get_user_by_id(session[SESSION_KEY])
    try:
        admin_service.activate_user(user_id, current_admin)
    except ValueError:
        pass
    return _redirect_back("admin_dashboard.dashboard")


@admin_dashboard_bp.route("/admin/admins")
@dashboard_permission_required("admins.view")
def admins():
    admin_list = admin_service.list_admins()
    return _render("admin_admins.html", "admins", admins=admin_list, error=None, reset_link=None, role_names=admin_service.VALID_ROLE_NAMES)


@admin_dashboard_bp.route("/admin/admins/<int:user_id>/edit", methods=["GET", "POST"])
@dashboard_permission_required("admins.update")
def edit_admin(user_id):
    current_admin = user_model.get_user_by_id(session[SESSION_KEY])
    target = user_model.get_user_by_id(user_id)
    if target is None or not target.get("is_admin"):
        return redirect(url_for("admin_dashboard.admins"))

    error = None
    if request.method == "POST":
        try:
            admin_service.update_admin_profile(
                user_id, request.form.get("name"), request.form.get("email"), current_admin
            )
            return redirect(url_for("admin_dashboard.admins"))
        except ValueError as e:
            error = str(e)
            target = user_model.get_user_by_id(user_id)  # re-fetch in case name/email partially applied

    return _render("admin_edit_admin.html", "admins", target=target, error=error)


@admin_dashboard_bp.route("/admin/admins/<int:user_id>/reset-password", methods=["POST"])
@dashboard_permission_required("admins.update")
def reset_admin_password(user_id):
    target = user_model.get_user_by_id(user_id)
    if target is None or not target.get("is_admin"):
        return redirect(url_for("admin_dashboard.admins"))

    token = secrets.token_urlsafe(32)
    _reset_tokens[token] = {"user_id": user_id, "expires": datetime.now(timezone.utc) + RESET_TOKEN_TTL}
    reset_link = url_for("admin_dashboard.reset_password", token=token, _external=True)

    admin_list = admin_service.list_admins()
    return _render(
        "admin_admins.html", "admins", admins=admin_list, error=None,
        reset_link=reset_link, reset_link_for=target["name"], role_names=admin_service.VALID_ROLE_NAMES,
    )


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
        permission_groups=authz_service.grouped_permissions(),
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
    notice = None

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
            notice = "Settings saved."
        except ValueError as e:
            error = str(e)

    return _render(
        "admin_system_settings.html",
        "system-settings",
        settings=system_settings_service.get_all(),
        can_manage=can_manage,
        error=error,
        notice=notice,
        currencies=ALLOWED_CURRENCIES,
        messaging_status=admin_service.get_messaging_status(),
        email_status=admin_service.get_email_status(),
    )


@admin_dashboard_bp.route("/admin/diagnostics/test-notification", methods=["POST"])
@dashboard_permission_required("settings.view")
def send_test_notification():
    current_admin = user_model.get_user_by_id(session[SESSION_KEY])
    admin_service.send_test_notification(current_admin)
    return _render(
        "admin_system_settings.html",
        "system-settings",
        settings=system_settings_service.get_all(),
        can_manage=authz_service.has_permission(current_admin, "settings.manage"),
        error=None,
        notice="Test notification sent — check the bell icon in the main app.",
        currencies=ALLOWED_CURRENCIES,
        messaging_status=admin_service.get_messaging_status(),
        email_status=admin_service.get_email_status(),
    )


@admin_dashboard_bp.route("/admin/system-health")
@dashboard_permission_required("system_health.view")
def system_health():
    checked_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return _render(
        "admin_system_health.html", "system-health",
        health=admin_service.get_system_health(), checked_at=checked_at,
    )


def _log_filter_params():
    search = (request.args.get("q") or "").strip()
    start_date = (request.args.get("start_date") or "").strip() or None
    end_date = (request.args.get("end_date") or "").strip() or None
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except ValueError:
        page = 1
    return search, start_date, end_date, page


@admin_dashboard_bp.route("/admin/audit-logs")
@dashboard_permission_required("audit_logs.view")
def audit_logs():
    admin_only = request.args.get("scope", "admin") == "admin"
    search, start_date, end_date, page = _log_filter_params()
    page_size = admin_service.AUDIT_LOG_PAGE_SIZE

    entries = admin_service.get_audit_log(
        limit=page_size, offset=(page - 1) * page_size, admin_actions_only=admin_only,
        search=search or None, start_date=start_date, end_date=end_date,
    )
    for e in entries:
        e["time_label"] = _time_ago(e["created_at"])

    total = admin_service.count_audit_log(
        admin_actions_only=admin_only, search=search or None, start_date=start_date, end_date=end_date
    )
    total_pages = max((total + page_size - 1) // page_size, 1)

    return _render(
        "admin_audit_logs.html", "audit-logs", entries=entries, admin_only=admin_only,
        search=search, start_date=start_date or "", end_date=end_date or "",
        page=page, total_pages=total_pages, total=total,
    )


@admin_dashboard_bp.route("/admin/audit-logs/export.csv")
@dashboard_permission_required("audit_logs.view")
def export_audit_log_csv():
    import csv
    import io

    admin_only = request.args.get("scope", "admin") == "admin"
    search, start_date, end_date, _page = _log_filter_params()
    entries = admin_service.get_audit_log(
        limit=1_000_000, offset=0, admin_actions_only=admin_only,
        search=search or None, start_date=start_date, end_date=end_date,
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["When", "User", "Action", "Details"])
    for e in entries:
        writer.writerow([e["created_at"], e.get("user_name") or "", e["action"], e.get("details") or ""])

    response = current_app.response_class(buffer.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=audit-log.csv"
    return response


@admin_dashboard_bp.route("/admin/security-events")
@dashboard_permission_required("audit_logs.view")
def security_events():
    search, start_date, end_date, page = _log_filter_params()
    page_size = admin_service.AUDIT_LOG_PAGE_SIZE

    entries = admin_service.get_security_events(
        limit=page_size, offset=(page - 1) * page_size,
        search=search or None, start_date=start_date, end_date=end_date,
    )
    for e in entries:
        e["time_label"] = _time_ago(e["created_at"])

    total = admin_service.count_security_events(search=search or None, start_date=start_date, end_date=end_date)
    total_pages = max((total + page_size - 1) // page_size, 1)

    return _render(
        "admin_security_events.html", "security-events", entries=entries,
        search=search, start_date=start_date or "", end_date=end_date or "",
        page=page, total_pages=total_pages, total=total,
    )


@admin_dashboard_bp.route("/admin/security-events/export.csv")
@dashboard_permission_required("audit_logs.view")
def export_security_events_csv():
    import csv
    import io

    search, start_date, end_date, _page = _log_filter_params()
    entries = admin_service.get_security_events(
        limit=1_000_000, offset=0, search=search or None, start_date=start_date, end_date=end_date
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["When", "User", "Event", "Detail"])
    for e in entries:
        writer.writerow([e["created_at"], e.get("user_name") or "", e["action"], e.get("details") or ""])

    response = current_app.response_class(buffer.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=security-events.csv"
    return response
