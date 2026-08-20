from app.database import get_db_connection


def create_transaction(user_id, amount, type_, category, description, date):
    conn = get_db_connection()
    cursor = conn.execute(
        """
        INSERT INTO transactions (user_id, amount, type, category, description, date)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, amount, type_, category, description, date),
    )
    conn.commit()
    new_id = cursor.lastrowid
    row = conn.execute("SELECT * FROM transactions WHERE id = ?", (new_id,)).fetchone()
    conn.close()
    return dict(row)


def get_transactions_by_user(user_id, category=None, type_=None, start_date=None, end_date=None, search=None):
    # Built dynamically because filters are optional, but every value still goes
    # through a `?` placeholder — never string-interpolated into the SQL itself.
    conditions = ["user_id = ?"]
    params = [user_id]

    if category:
        conditions.append("category = ?")
        params.append(category)
    if type_:
        conditions.append("type = ?")
        params.append(type_)
    if start_date:
        conditions.append("date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("date <= ?")
        params.append(end_date)
    if search:
        conditions.append("(category LIKE ? OR description LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like])

    query = f"SELECT * FROM transactions WHERE {' AND '.join(conditions)} ORDER BY date DESC, id DESC"

    conn = get_db_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_transaction_by_id(transaction_id):
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM transactions WHERE id = ?", (transaction_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_transaction(transaction_id, amount, type_, category, description, date):
    conn = get_db_connection()
    conn.execute(
        """
        UPDATE transactions
        SET amount = ?, type = ?, category = ?, description = ?, date = ?
        WHERE id = ?
        """,
        (amount, type_, category, description, date, transaction_id),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM transactions WHERE id = ?", (transaction_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_transaction(transaction_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()
    conn.close()


def get_totals(user_id):
    conn = get_db_connection()
    row = conn.execute(
        """
        SELECT
            COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) AS income,
            COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) AS expenses,
            COUNT(*) AS transaction_count
        FROM transactions
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()
    conn.close()
    return dict(row)


def get_category_spending(user_id):
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT category, SUM(amount) AS total
        FROM transactions
        WHERE user_id = ? AND type = 'expense'
        GROUP BY category
        ORDER BY total DESC
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_category_spending_for_month(user_id, year_month):
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT category, SUM(amount) AS total
        FROM transactions
        WHERE user_id = ? AND type = 'expense' AND strftime('%Y-%m', date) = ?
        GROUP BY category
        """,
        (user_id, year_month),
    ).fetchall()
    conn.close()
    return {row["category"]: row["total"] for row in rows}


def get_monthly_totals(user_id):
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT
            strftime('%Y-%m', date) AS month,
            COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) AS income,
            COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) AS expenses
        FROM transactions
        WHERE user_id = ?
        GROUP BY month
        ORDER BY month
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
