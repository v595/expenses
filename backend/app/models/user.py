from app.database import get_db_connection


def count_users():
    conn = get_db_connection()
    row = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()
    conn.close()
    return row["count"]


def create_user(name, email, password_hash):
    conn = get_db_connection()
    row = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?) RETURNING *",
        (name, email, password_hash),
    ).fetchone()
    conn.commit()
    conn.close()
    return dict(row)


def get_user_by_email(email):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_token(token):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM users WHERE token = ?", (token,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_name(user_id, name):
    conn = get_db_connection()
    conn.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
    conn.commit()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row)


def update_avatar(user_id, avatar):
    conn = get_db_connection()
    conn.execute("UPDATE users SET avatar = ? WHERE id = ?", (avatar, user_id))
    conn.commit()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row)


def update_password(user_id, password_hash):
    conn = get_db_connection()
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
    conn.commit()
    conn.close()


def set_user_token(user_id, token):
    conn = get_db_connection()
    conn.execute("UPDATE users SET token = ? WHERE id = ?", (token, user_id))
    conn.commit()
    conn.close()


def record_login(user_id, timestamp):
    conn = get_db_connection()
    conn.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (timestamp, user_id))
    conn.commit()
    conn.close()


def update_settings(user_id, currency, notify_budget_alerts, notify_bill_reminders):
    conn = get_db_connection()
    conn.execute(
        """
        UPDATE users
        SET currency = ?, notify_budget_alerts = ?, notify_bill_reminders = ?
        WHERE id = ?
        """,
        (currency, notify_budget_alerts, notify_bill_reminders, user_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row)


def delete_user(user_id):
    # No ON DELETE CASCADE in this schema, so every table that references a
    # user gets cleaned up by hand, in dependency order (children first).
    conn = get_db_connection()
    conn.execute(
        "DELETE FROM transaction_tags WHERE transaction_id IN "
        "(SELECT id FROM transactions WHERE user_id = ?)",
        (user_id,),
    )
    conn.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM tags WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM budgets WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM recurring_transactions WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM accounts WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM categories WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM goals WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM bills WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM notifications WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
