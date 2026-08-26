from app.database import get_db_connection


def get_notifications_by_user(user_id, limit=50):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC, id DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_unread_count(user_id):
    conn = get_db_connection()
    row = conn.execute(
        "SELECT COUNT(*) AS count FROM notifications WHERE user_id = ? AND is_read = 0",
        (user_id,),
    ).fetchone()
    conn.close()
    return row["count"]


def exists_by_ref(user_id, ref_key):
    conn = get_db_connection()
    row = conn.execute(
        "SELECT id FROM notifications WHERE user_id = ? AND ref_key = ?", (user_id, ref_key)
    ).fetchone()
    conn.close()
    return row is not None


def create_notification(user_id, type_, title, message, ref_key):
    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO notifications (user_id, type, title, message, ref_key)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, type_, title, message, ref_key),
    )
    conn.commit()
    conn.close()


def mark_read(notification_id, user_id):
    conn = get_db_connection()
    conn.execute(
        "UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?",
        (notification_id, user_id),
    )
    conn.commit()
    conn.close()


def mark_all_read(user_id):
    conn = get_db_connection()
    conn.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def delete_notification(notification_id, user_id):
    conn = get_db_connection()
    conn.execute(
        "DELETE FROM notifications WHERE id = ? AND user_id = ?", (notification_id, user_id)
    )
    conn.commit()
    conn.close()
