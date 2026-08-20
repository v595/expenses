from app.database import get_db_connection


def get_budgets_by_user(user_id):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT category, monthly_limit FROM budgets WHERE user_id = ? ORDER BY category",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def upsert_budget(user_id, category, monthly_limit):
    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO budgets (user_id, category, monthly_limit)
        VALUES (?, ?, ?)
        ON CONFLICT (user_id, category) DO UPDATE SET monthly_limit = excluded.monthly_limit
        """,
        (user_id, category, monthly_limit),
    )
    conn.commit()
    conn.close()


def delete_budget(user_id, category):
    conn = get_db_connection()
    conn.execute("DELETE FROM budgets WHERE user_id = ? AND category = ?", (user_id, category))
    conn.commit()
    conn.close()
