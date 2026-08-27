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


def list_users(search=None):
    where = ""
    params = {}
    if search:
        where = "WHERE (users.name LIKE :like OR users.email LIKE :like)"
        params["like"] = f"%{search}%"

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
                ORDER BY users.name
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


def get_audit_log(limit=100, offset=0, admin_actions_only=False):
    return activity_log_model.get_audit_log(limit=limit, offset=offset, admin_actions_only=admin_actions_only)


def get_security_events(limit=100, offset=0):
    return activity_log_model.get_security_events(limit=limit, offset=offset)


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


def disable_admin(user_id, requesting_user):
    return suspend_user(user_id, requesting_user)


def activate_admin(user_id, requesting_user):
    return activate_user(user_id, requesting_user)


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
