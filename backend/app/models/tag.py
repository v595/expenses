from app.database import get_db_connection


def get_tags_by_user(user_id):
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM tags WHERE user_id = ? ORDER BY name", (user_id,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_or_create_tag(user_id, name):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM tags WHERE user_id = ? AND name = ?", (user_id, name)).fetchone()
    if row is None:
        row = conn.execute(
            "INSERT INTO tags (user_id, name) VALUES (?, ?) RETURNING *", (user_id, name)
        ).fetchone()
        conn.commit()
    conn.close()
    return dict(row)


def set_tags_for_transaction(transaction_id, tag_ids):
    conn = get_db_connection()
    conn.execute("DELETE FROM transaction_tags WHERE transaction_id = ?", (transaction_id,))
    for tag_id in tag_ids:
        conn.execute(
            "INSERT INTO transaction_tags (transaction_id, tag_id) VALUES (?, ?)",
            (transaction_id, tag_id),
        )
    conn.commit()
    conn.close()


def get_tags_for_transaction(transaction_id):
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT tags.id, tags.name FROM tags
        JOIN transaction_tags ON transaction_tags.tag_id = tags.id
        WHERE transaction_tags.transaction_id = ?
        ORDER BY tags.name
        """,
        (transaction_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_tags_for_transactions(transaction_ids):
    if not transaction_ids:
        return {}

    placeholders = ",".join("?" for _ in transaction_ids)
    conn = get_db_connection()
    rows = conn.execute(
        f"""
        SELECT transaction_tags.transaction_id, tags.id, tags.name FROM tags
        JOIN transaction_tags ON transaction_tags.tag_id = tags.id
        WHERE transaction_tags.transaction_id IN ({placeholders})
        ORDER BY tags.name
        """,
        transaction_ids,
    ).fetchall()
    conn.close()

    result = {tid: [] for tid in transaction_ids}
    for row in rows:
        result[row["transaction_id"]].append({"id": row["id"], "name": row["name"]})
    return result


def delete_tag(tag_id, user_id):
    conn = get_db_connection()
    conn.execute(
        "DELETE FROM transaction_tags WHERE tag_id = ? AND tag_id IN (SELECT id FROM tags WHERE user_id = ?)",
        (tag_id, user_id),
    )
    conn.execute("DELETE FROM tags WHERE id = ? AND user_id = ?", (tag_id, user_id))
    conn.commit()
    conn.close()
