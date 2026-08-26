from app.database import get_db_connection


def get_goals_by_user(user_id):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM goals WHERE user_id = ? ORDER BY target_date IS NULL, target_date", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_goal_by_id(goal_id, user_id):
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM goals WHERE id = ? AND user_id = ?", (goal_id, user_id)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def create_goal(user_id, name, target_amount, target_date):
    conn = get_db_connection()
    row = conn.execute(
        """
        INSERT INTO goals (user_id, name, target_amount, target_date)
        VALUES (?, ?, ?, ?)
        RETURNING *
        """,
        (user_id, name, target_amount, target_date),
    ).fetchone()
    conn.commit()
    conn.close()
    return dict(row)


def add_funds(goal_id, user_id, amount):
    conn = get_db_connection()
    conn.execute(
        "UPDATE goals SET current_amount = current_amount + ? WHERE id = ? AND user_id = ?",
        (amount, goal_id, user_id),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM goals WHERE id = ? AND user_id = ?", (goal_id, user_id)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_goal(goal_id, user_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM goals WHERE id = ? AND user_id = ?", (goal_id, user_id))
    conn.commit()
    conn.close()
