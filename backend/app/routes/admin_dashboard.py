from datetime import datetime, timezone
from functools import wraps

from flask import Blueprint, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from app.models import user as user_model
from app.services import admin_service

admin_dashboard_bp = Blueprint("admin_dashboard", __name__)

SESSION_KEY = "dashboard_admin_id"


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
            if user.get("is_admin"):
                session[SESSION_KEY] = user["id"]
                user_model.record_login(user["id"], datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
                return redirect(url_for("admin_dashboard.dashboard"))
            error = "That account doesn't have admin access."
        else:
            error = "Invalid email or password."

    return render_template("admin_login.html", error=error)


@admin_dashboard_bp.route("/admin/logout")
def logout():
    session.pop(SESSION_KEY, None)
    return redirect(url_for("admin_dashboard.login"))


@admin_dashboard_bp.route("/admin")
@dashboard_admin_required
def dashboard():
    search = (request.args.get("q") or "").strip()
    stats = admin_service.get_stats()
    users = admin_service.list_users(search=search or None)
    admin_user = user_model.get_user_by_id(session[SESSION_KEY])

    for u in users:
        u["last_login_label"] = _time_ago(u["last_login_at"])

    max_signups = max((m["count"] for m in stats["signups_by_month"]), default=1) or 1

    activity = admin_service.get_recent_activity(50)
    for a in activity:
        a["time_label"] = _time_ago(a["created_at"])

    return render_template(
        "admin_dashboard.html",
        stats=stats,
        users=users,
        activity=activity,
        admin_name=admin_user["name"],
        admin_avatar=admin_user["name"][:1].upper(),
        current_admin_id=session[SESSION_KEY],
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

    return render_template("admin_user_activity.html", target_user=user, activity=activity)


@admin_dashboard_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@dashboard_admin_required
def delete_user(user_id):
    try:
        admin_service.delete_user(user_id, session[SESSION_KEY])
    except ValueError:
        pass  # tried to delete their own account — silently ignored on this view
    return redirect(url_for("admin_dashboard.dashboard"))
