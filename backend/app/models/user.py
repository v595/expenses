from app.database import get_db_connection


def count_users():
    conn = get_db_connection()
    row = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()
    conn.close()
    return row["count"]


def create_user(name, email, password_hash):
    conn = get_db_connection()
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, password_hash),
    )
    conn.commit()
    new_id = cursor.lastrowid
    row = conn.execute("SELECT * FROM users WHERE id = ?", (new_id,)).fetchone()
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


def set_user_token(user_id, token):
    conn = get_db_connection()
    conn.execute("UPDATE users SET token = ? WHERE id = ?", (token, user_id))
    conn.commit()
    conn.close()
