from app.database import get_db_connection


def get_categories_by_user(user_id):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM categories WHERE user_id = ? ORDER BY type, name", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def create_category(user_id, name, type_, color):
    conn = get_db_connection()
    row = conn.execute(
        """
        INSERT INTO categories (user_id, name, type, color)
        VALUES (?, ?, ?, ?)
        RETURNING *
        """,
        (user_id, name, type_, color),
    ).fetchone()
    conn.commit()
    conn.close()
    return dict(row)


def get_category_by_id(category_id, user_id):
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM categories WHERE id = ? AND user_id = ?", (category_id, user_id)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_category(category_id, user_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM categories WHERE id = ? AND user_id = ?", (category_id, user_id))
    conn.commit()
    conn.close()
