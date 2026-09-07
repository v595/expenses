from datetime import datetime, timedelta, timezone

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import activity_log as activity_log_model
from app.models import role as role_model
from app.models import user as user_model
from app.services import authz_service
from app.services.auth_service import EMAIL_PATTERN, MIN_PASSWORD_LENGTH, to_public_user

ACTIVE_WINDOW_DAYS = 30


def get_stats():
    user_count = db.session.execute(db.text("SELECT COUNT(*) AS count FROM users")).mappings().first()["count"]
    transaction_count = (
        db.session.execute(db.text("SELECT COUNT(*) AS count FROM transactions")).mappings().first()["count"]
    )
    totals = (
        db.session.execute(
            db.text(
                """
                SELECT
                    COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) AS income,
                    COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) AS expenses
                FROM transactions
                """
            )
        )
        .mappings()
        .first()
    )
    # CAST to TEXT first: created_at is a real TIMESTAMP column on some
    # Postgres-era rows, and SUBSTR there only accepts text (SQLite has no
    # such type distinction).
    signups = (
        db.session.execute(
            db.text(
                """
                SELECT SUBSTR(CAST(created_at AS TEXT), 1, 7) AS month, COUNT(*) AS count
                FROM users
                GROUP BY month
                ORDER BY month
                """
            )
        )
        .mappings()
        .all()
    )

    logged_in_now = (
        db.session.execute(db.text("SELECT COUNT(*) AS count FROM users WHERE token IS NOT NULL"))
        .mappings()
        .first()["count"]
    )

    active_cutoff = (datetime.now(timezone.utc) - timedelta(days=ACTIVE_WINDOW_DAYS)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    active_recently = (
        db.session.execute(
            db.text("SELECT COUNT(*) AS count FROM users WHERE last_login_at >= :cutoff"),
            {"cutoff": active_cutoff},
        )
        .mappings()
        .first()["count"]
    )

    return {
        "user_count": user_count,
        "transaction_count": transaction_count,
        "total_income": totals["income"],
        "total_expenses": totals["expenses"],
        "signups_by_month": [dict(row) for row in signups],
        "logged_in_now": logged_in_now,
        "active_recently": active_recently,
        "active_window_days": ACTIVE_WINDOW_DAYS,
    }


USER_SORT_COLUMNS = {
    "name": "users.name",
    "joined": "users.created_at",
    "last_login": "users.last_login_at",
    "transactions": "transaction_count",
    "income": "income",
    "expenses": "expenses",
}
USER_PAGE_SIZE = 25


def _build_user_filters(search, role, status):
    clauses = []
    params = {}

    if search:
        clauses.append("(users.name LIKE :like OR users.email LIKE :like)")
        params["like"] = f"%{search}%"

    if role:
        clauses.append("roles.name = :role")
        params["role"] = role

    if status == "suspended":
        clauses.append("users.is_suspended = 1")
    elif status == "online":
        clauses.append("users.is_suspended = 0 AND users.token IS NOT NULL")
    elif status == "offline":
        clauses.append("users.is_suspended = 0 AND users.token IS NULL")

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return where, params


def count_users(search=None, role=None, status=None):
    where, params = _build_user_filters(search, role, status)
    return (
        db.session.execute(
            db.text(
                f"""
                SELECT COUNT(*) AS count FROM users
                LEFT JOIN roles ON roles.id = users.role_id
                {where}
                """
            ),
            params,
        )
        .mappings()
        .first()["count"]
    )


def list_users(search=None, role=None, status=None, sort="name", direction="asc", page=1, per_page=USER_PAGE_SIZE):
    where, params = _build_user_filters(search, role, status)
    sort_column = USER_SORT_COLUMNS.get(sort, USER_SORT_COLUMNS["name"])
    sort_direction = "DESC" if direction == "desc" else "ASC"
    params["limit"] = per_page
    params["offset"] = max(page - 1, 0) * per_page

    rows = (
        db.session.execute(
            db.text(
                f"""
                SELECT
                    users.id, users.name, users.email, users.created_at, users.is_admin,
                    users.is_suspended, users.last_login_at, users.token, roles.name AS role_name,
                    COUNT(transactions.id) AS transaction_count,
                    COALESCE(SUM(CASE WHEN transactions.type = 'income' THEN transactions.amount ELSE 0 END), 0) AS income,
                    COALESCE(SUM(CASE WHEN transactions.type = 'expense' THEN transactions.amount ELSE 0 END), 0) AS expenses
                FROM users
                LEFT JOIN transactions ON transactions.user_id = users.id
                LEFT JOIN roles ON roles.id = users.role_id
                {where}
                GROUP BY users.id, users.name, users.email, users.created_at, users.is_admin,
                         users.is_suspended, users.last_login_at, users.token, roles.name
                ORDER BY {sort_column} {sort_direction}
                LIMIT :limit OFFSET :offset
                """
            ),
            params,
        )
        .mappings()
        .all()
    )
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "created_at": row["created_at"],
            "is_admin": bool(row["is_admin"]),
            "is_suspended": bool(row["is_suspended"]),
            "role_name": row["role_name"],
            "last_login_at": row["last_login_at"],
            "is_logged_in": row["token"] is not None,
            "transaction_count": row["transaction_count"],
            "income": row["income"],
            "expenses": row["expenses"],
        }
        for row in rows
    ]


def get_user_transactions(user_id):
    rows = (
        db.session.execute(
            db.text(
                "SELECT id, date, type, category, amount, description FROM transactions "
                "WHERE user_id = :user_id ORDER BY date DESC"
            ),
            {"user_id": user_id},
        )
        .mappings()
        .all()
    )
    return [dict(row) for row in rows]


def delete_user(user_id, requesting_user_id):
    if user_id == requesting_user_id:
        raise ValueError("You can't delete your own account from here")
    target = user_model.get_user_by_id(user_id)
    user_model.delete_user(user_id)
    if target:
        activity_log_model.log(
            requesting_user_id,
            "Deleted user (admin action)",
            f"{target['name']} ({target['email']})",
            actor_id=requesting_user_id,
            target_user_id=user_id,
            entity_type="user",
            entity_id=user_id,
        )


def get_user(user_id):
    user = user_model.get_user_by_id(user_id)
    return to_public_user(user) if user else None


def get_recent_activity(limit=50):
    return activity_log_model.get_recent(limit)


def get_user_activity(user_id, limit=100):
    return activity_log_model.get_for_user(user_id, limit)


AUDIT_LOG_PAGE_SIZE = 50


def get_audit_log(limit=100, offset=0, admin_actions_only=False, search=None, start_date=None, end_date=None):
    return activity_log_model.get_audit_log(
        limit=limit, offset=offset, admin_actions_only=admin_actions_only,
        search=search, start_date=start_date, end_date=end_date,
    )


def count_audit_log(admin_actions_only=False, search=None, start_date=None, end_date=None):
    return activity_log_model.count_audit_log(
        admin_actions_only=admin_actions_only, search=search, start_date=start_date, end_date=end_date
    )


def get_security_events(limit=100, offset=0, search=None, start_date=None, end_date=None):
    return activity_log_model.get_security_events(
        limit=limit, offset=offset, search=search, start_date=start_date, end_date=end_date
    )


def count_security_events(search=None, start_date=None, end_date=None):
    return activity_log_model.count_security_events(search=search, start_date=start_date, end_date=end_date)


def _target_role_name(user_id):
    user = user_model.get_user_by_id(user_id)
    if user is None or user.get("role_id") is None:
        return None
    role = role_model.get_role_by_id(user["role_id"])
    return role["name"] if role else None


def suspend_user(user_id, requesting_user):
    if user_id == requesting_user["id"]:
        raise ValueError("You can't suspend your own account")
    if _target_role_name(user_id) == "SUPER_ADMIN" and not authz_service.is_super_admin(requesting_user):
        raise ValueError("Only a Super Admin can suspend another Super Admin")

    updated = user_model.suspend_user(user_id)
    if updated is None:
        raise ValueError("User not found")
    activity_log_model.log(
        requesting_user["id"],
        "Suspended user",
        f"{updated['name']} ({updated['email']})",
        actor_id=requesting_user["id"],
        target_user_id=user_id,
        entity_type="user",
        entity_id=user_id,
    )
    return to_public_user(updated)


def activate_user(user_id, requesting_user):
    updated = user_model.activate_user(user_id)
    if updated is None:
        raise ValueError("User not found")
    activity_log_model.log(
        requesting_user["id"],
        "Activated user",
        f"{updated['name']} ({updated['email']})",
        actor_id=requesting_user["id"],
        target_user_id=user_id,
        entity_type="user",
        entity_id=user_id,
    )
    return to_public_user(updated)


def list_users_for_export(search=None, role=None, status=None, sort="name", direction="asc"):
    """Every matching user, unpaginated — what the CSV export streams."""
    return list_users(search=search, role=role, status=status, sort=sort, direction=direction, page=1, per_page=1_000_000)


VALID_ROLE_NAMES = ("USER", "ADMIN", "SUPER_ADMIN")


def change_user_role(user_id, role_name, requesting_user):
    if user_id == requesting_user["id"]:
        raise ValueError("You can't change your own role from here")
    if role_name not in VALID_ROLE_NAMES:
        raise ValueError("Role must be one of " + ", ".join(VALID_ROLE_NAMES))

    role = role_model.get_role_by_name(role_name)
    if role is None:
        raise ValueError("Role not found — run migrations")

    target_role = _target_role_name(user_id)
    if not authz_service.is_super_admin(requesting_user):
        if role_name == "SUPER_ADMIN":
            raise ValueError("Only a Super Admin can grant Super Admin")
        if target_role == "SUPER_ADMIN":
            raise ValueError("Only a Super Admin can change another Super Admin's role")
        # Promoting to (or demoting from) ADMIN is admin-account management,
        # not plain user management — the route only requires users.update
        # since it's shared with the regular-user dashboard rows, so admin
        # involvement is gated here instead.
        touches_admin = role_name == "ADMIN" or target_role in ("ADMIN", "SUPER_ADMIN")
        if touches_admin and not authz_service.has_permission(requesting_user, "admins.update"):
            raise ValueError("You don't have permission to change admin roles")

    updated = user_model.set_role(user_id, role["id"])
    if updated is None:
        raise ValueError("User not found")
    activity_log_model.log(
        requesting_user["id"],
        f"Changed role to {role_name}",
        f"{updated['name']} ({updated['email']})",
        actor_id=requesting_user["id"],
        target_user_id=user_id,
        entity_type="user",
        entity_id=user_id,
    )
    return to_public_user(updated)


def list_admins():
    return [to_public_user(u) for u in user_model.get_users_by_role_names(["ADMIN", "SUPER_ADMIN"])]


def create_admin_user(name, email, password, role_name, requesting_user):
    if role_name not in ("ADMIN", "SUPER_ADMIN"):
        raise ValueError("Role must be ADMIN or SUPER_ADMIN")
    if role_name == "SUPER_ADMIN" and not authz_service.is_super_admin(requesting_user):
        raise ValueError("Only a Super Admin can create another Super Admin")

    if not isinstance(name, str) or not name.strip():
        raise ValueError("Name is required")
    if not isinstance(email, str) or not EMAIL_PATTERN.match(email):
        raise ValueError("A valid email is required")
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")

    email_clean = email.strip().lower()
    if user_model.get_user_by_email(email_clean):
        raise ValueError("Email is already registered")

    role = role_model.get_role_by_name(role_name)
    if role is None:
        raise ValueError("Role not found — run migrations")

    user = user_model.create_user(name.strip(), email_clean, generate_password_hash(password))
    updated = user_model.set_role(user["id"], role["id"])

    activity_log_model.log(
        requesting_user["id"],
        f"Created {role_name} account",
        f"{updated['name']} ({updated['email']})",
        actor_id=requesting_user["id"],
        target_user_id=user["id"],
        entity_type="admin",
        entity_id=user["id"],
    )
    return to_public_user(updated)


def update_admin_profile(user_id, name, email, requesting_user):
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Name is required")
    if not isinstance(email, str) or not EMAIL_PATTERN.match(email):
        raise ValueError("A valid email is required")

    email_clean = email.strip().lower()
    existing = user_model.get_user_by_email(email_clean)
    if existing and existing["id"] != user_id:
        raise ValueError("Email is already registered to another account")

    target = user_model.get_user_by_id(user_id)
    if target is None:
        raise ValueError("Admin not found")

    updated = user_model.update_name(user_id, name.strip())
    updated = user_model.update_email(user_id, email_clean)
    activity_log_model.log(
        requesting_user["id"],
        "Updated admin profile",
        f"{updated['name']} ({updated['email']})",
        actor_id=requesting_user["id"],
        target_user_id=user_id,
        entity_type="admin",
        entity_id=user_id,
    )
    return to_public_user(updated)


def disable_admin(user_id, requesting_user):
    return suspend_user(user_id, requesting_user)


def activate_admin(user_id, requesting_user):
    return activate_user(user_id, requesting_user)


def send_test_notification(requesting_user):
    """Read-only-ish diagnostic: drops a real notification into the
    requesting admin's own account (never anyone else's) so they can confirm
    the notification pipeline actually works end-to-end — bell icon, list,
    mark-read — without waiting for a real budget/bill alert to fire."""
    from datetime import datetime, timezone

    from app.models import notification as notification_model

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    notification_model.create_notification(
        requesting_user["id"],
        "admin_test",
        "Test notification",
        f"Sent from System Settings by {requesting_user['name']} at {timestamp} UTC.",
        f"admin_test:{timestamp}",
    )
    # entity_type set (not left null) so this shows up in the Audit Logs
    # page's default "Admin actions" tab, same reasoning as the admin-login
    # log calls in routes/admin_dashboard.py.
    activity_log_model.log(requesting_user["id"], "Sent test notification", entity_type="admin_dashboard")


def get_messaging_status():
    from app.services import messaging

    return messaging.status()


def get_email_status():
    from app.services import email

    return email.status()


def get_system_health():
    """Only checks that can actually be verified against this app's real
    infrastructure — no fabricated CPU/memory/uptime metrics."""
    checks = []

    try:
        db.session.execute(db.text("SELECT 1")).scalar()
        checks.append({"name": "Database", "status": "healthy", "detail": "Query round-trip succeeded"})
    except Exception as e:
        checks.append({"name": "Database", "status": "critical", "detail": str(e)})

    try:
        count = db.session.execute(db.text("SELECT COUNT(*) FROM users")).scalar()
        checks.append({"name": "Authentication", "status": "healthy", "detail": f"{count} user record(s) reachable"})
    except Exception as e:
        checks.append({"name": "Authentication", "status": "critical", "detail": str(e)})

    try:
        db.session.execute(db.text("SELECT COUNT(*) FROM notifications")).scalar()
        checks.append({"name": "Notifications", "status": "healthy", "detail": "Table reachable"})
    except Exception as e:
        checks.append({"name": "Notifications", "status": "critical", "detail": str(e)})

    # If we got far enough to build this response, the API process itself
    # is up — this isn't a fabricated metric, it's the fact of responding.
    checks.append({"name": "API", "status": "healthy", "detail": "Responding"})

    overall = "critical" if any(c["status"] == "critical" for c in checks) else "healthy"
    return {"overall": overall, "checks": checks}
