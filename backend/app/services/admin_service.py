from datetime import datetime, timedelta, timezone

from app.database import get_db_connection
from app.models import user as user_model
from app.services.auth_service import to_public_user

ACTIVE_WINDOW_DAYS = 30


def get_stats():
    conn = get_db_connection()
    user_count = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
    transaction_count = conn.execute("SELECT COUNT(*) AS count FROM transactions").fetchone()["count"]
    totals = conn.execute(
        """
        SELECT
            COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) AS income,
            COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) AS expenses
        FROM transactions
        """
    ).fetchone()
    # CAST to TEXT first: created_at is a real TIMESTAMP column on Postgres,
    # and SUBSTR there only accepts text (SQLite has no such type distinction).
    signups = conn.execute(
        """
        SELECT SUBSTR(CAST(created_at AS TEXT), 1, 7) AS month, COUNT(*) AS count
        FROM users
        GROUP BY month
        ORDER BY month
        """
    ).fetchall()

    logged_in_now = conn.execute(
        "SELECT COUNT(*) AS count FROM users WHERE token IS NOT NULL"
    ).fetchone()["count"]

    active_cutoff = (datetime.now(timezone.utc) - timedelta(days=ACTIVE_WINDOW_DAYS)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    active_recently = conn.execute(
        "SELECT COUNT(*) AS count FROM users WHERE last_login_at >= ?", (active_cutoff,)
    ).fetchone()["count"]

    conn.close()

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
    conditions = []
    params = []
    if search:
        conditions.append("(users.name LIKE ? OR users.email LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like])
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    conn = get_db_connection()
    rows = conn.execute(
        f"""
        SELECT
            users.id, users.name, users.email, users.created_at, users.is_admin,
            users.last_login_at, users.token,
            COUNT(transactions.id) AS transaction_count,
            COALESCE(SUM(CASE WHEN transactions.type = 'income' THEN transactions.amount ELSE 0 END), 0) AS income,
            COALESCE(SUM(CASE WHEN transactions.type = 'expense' THEN transactions.amount ELSE 0 END), 0) AS expenses
        FROM users
        LEFT JOIN transactions ON transactions.user_id = users.id
        {where}
        GROUP BY users.id, users.name, users.email, users.created_at, users.is_admin,
                 users.last_login_at, users.token
        ORDER BY users.name
        """,
        params,
    ).fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "created_at": row["created_at"],
            "is_admin": bool(row["is_admin"]),
            "last_login_at": row["last_login_at"],
            "is_logged_in": row["token"] is not None,
            "transaction_count": row["transaction_count"],
            "income": row["income"],
            "expenses": row["expenses"],
        }
        for row in rows
    ]


def get_user_transactions(user_id):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, date, type, category, amount, description FROM transactions "
        "WHERE user_id = ? ORDER BY date DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_user(user_id, requesting_user_id):
    if user_id == requesting_user_id:
        raise ValueError("You can't delete your own account from here")
    user_model.delete_user(user_id)


def get_user(user_id):
    user = user_model.get_user_by_id(user_id)
    return to_public_user(user) if user else None
