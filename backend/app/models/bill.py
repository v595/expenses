from app.database import get_db_connection


def get_bills_by_user(user_id):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM bills WHERE user_id = ? ORDER BY is_paid, due_date", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_bill_by_id(bill_id, user_id):
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM bills WHERE id = ? AND user_id = ?", (bill_id, user_id)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_upcoming_unpaid(user_id, cutoff_date):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM bills WHERE user_id = ? AND is_paid = 0 AND due_date <= ?",
        (user_id, cutoff_date),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def create_bill(user_id, name, amount, due_date, repeat_frequency):
    conn = get_db_connection()
    row = conn.execute(
        """
        INSERT INTO bills (user_id, name, amount, due_date, repeat_frequency)
        VALUES (?, ?, ?, ?, ?)
        RETURNING *
        """,
        (user_id, name, amount, due_date, repeat_frequency),
    ).fetchone()
    conn.commit()
    conn.close()
    return dict(row)


def mark_paid(bill_id, user_id):
    conn = get_db_connection()
    conn.execute(
        "UPDATE bills SET is_paid = 1 WHERE id = ? AND user_id = ?", (bill_id, user_id)
    )
    conn.commit()
    conn.close()


def reschedule(bill_id, next_due_date):
    conn = get_db_connection()
    conn.execute(
        "UPDATE bills SET due_date = ?, is_paid = 0 WHERE id = ?", (next_due_date, bill_id)
    )
    conn.commit()
    conn.close()


def delete_bill(bill_id, user_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM bills WHERE id = ? AND user_id = ?", (bill_id, user_id))
    conn.commit()
    conn.close()
