"""Read-only debug view: prints each user with their own transactions.

Run from backend/: python view_by_user.py
"""
from app.database import get_db_connection

conn = get_db_connection()
users = conn.execute("SELECT id, name, email, created_at FROM users ORDER BY name").fetchall()

for user in users:
    print(f"\n=== {user['name']} <{user['email']}> (id={user['id']}, joined {user['created_at']}) ===")
    transactions = conn.execute(
        "SELECT date, type, category, amount, description FROM transactions "
        "WHERE user_id = ? ORDER BY date DESC",
        (user["id"],),
    ).fetchall()
    if not transactions:
        print("  (no transactions)")
        continue
    for t in transactions:
        print(f"  {t['date']}  {t['type']:<7}  {t['category']:<15}  {t['amount']:>10.2f}  {t['description'] or ''}")

conn.close()
