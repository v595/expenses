"""Read-only debug view: prints each user with their own transactions.

Run from backend/: python scripts/view_by_user.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models.orm import Transaction, User

app = create_app()

with app.app_context():
    users = User.query.order_by(User.name).all()

    for user in users:
        print(f"\n=== {user.name} <{user.email}> (id={user.id}, joined {user.created_at}) ===")
        transactions = (
            Transaction.query.filter_by(user_id=user.id).order_by(Transaction.date.desc()).all()
        )
        if not transactions:
            print("  (no transactions)")
            continue
        for t in transactions:
            print(f"  {t.date}  {t.type:<7}  {t.category:<15}  {t.amount:>10.2f}  {t.description or ''}")
