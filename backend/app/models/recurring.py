from app.database import get_db_connection


def get_recurring_by_user(user_id):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM recurring_transactions WHERE user_id = ? ORDER BY next_date",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_due_recurring(user_id, today):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM recurring_transactions WHERE user_id = ? AND next_date <= ?",
        (user_id, today),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def create_recurring(user_id, amount, type_, category, description, frequency, next_date):
    conn = get_db_connection()
    row = conn.execute(
        """
        INSERT INTO recurring_transactions (user_id, amount, type, category, description, frequency, next_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        RETURNING *
        """,
        (user_id, amount, type_, category, description, frequency, next_date),
    ).fetchone()
    conn.commit()
    conn.close()
    return dict(row)


def update_next_date(recurring_id, next_date):
    conn = get_db_connection()
    conn.execute(
        "UPDATE recurring_transactions SET next_date = ? WHERE id = ?", (next_date, recurring_id)
    )
    conn.commit()
    conn.close()


def delete_recurring(recurring_id, user_id):
    conn = get_db_connection()
    conn.execute(
        "DELETE FROM recurring_transactions WHERE id = ? AND user_id = ?", (recurring_id, user_id)
    )
    conn.commit()
    conn.close()
