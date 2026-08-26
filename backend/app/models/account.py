from app.database import get_db_connection


def get_accounts_by_user(user_id):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM accounts WHERE user_id = ? ORDER BY name", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_account_by_id(account_id, user_id):
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM accounts WHERE id = ? AND user_id = ?", (account_id, user_id)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def create_account(user_id, name, type_, balance, color):
    conn = get_db_connection()
    row = conn.execute(
        """
        INSERT INTO accounts (user_id, name, type, balance, color)
        VALUES (?, ?, ?, ?, ?)
        RETURNING *
        """,
        (user_id, name, type_, balance, color),
    ).fetchone()
    conn.commit()
    conn.close()
    return dict(row)


def update_account(account_id, user_id, name, type_, color):
    conn = get_db_connection()
    conn.execute(
        "UPDATE accounts SET name = ?, type = ?, color = ? WHERE id = ? AND user_id = ?",
        (name, type_, color, account_id, user_id),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM accounts WHERE id = ? AND user_id = ?", (account_id, user_id)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def adjust_balance(account_id, delta):
    conn = get_db_connection()
    conn.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (delta, account_id))
    conn.commit()
    conn.close()


def delete_account(account_id, user_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM accounts WHERE id = ? AND user_id = ?", (account_id, user_id))
    conn.commit()
    conn.close()
