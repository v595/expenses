from app.database import get_db_connection


def log(user_id, action, details=None):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)",
        (user_id, action, details),
    )
    conn.commit()
    conn.close()


def get_recent(limit=50):
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT activity_logs.id, activity_logs.action, activity_logs.details, activity_logs.created_at,
               users.id AS user_id, users.name AS user_name, users.email AS user_email
        FROM activity_logs
        JOIN users ON users.id = activity_logs.user_id
        ORDER BY activity_logs.id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_for_user(user_id, limit=100):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM activity_logs WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
