from app.extensions import db
from app.models.orm import Budget


def get_budgets_by_user(user_id):
    rows = db.session.query(Budget).filter_by(user_id=user_id).order_by(Budget.category).all()
    return [b.to_dict() for b in rows]


def upsert_budget(user_id, category, monthly_limit):
    budget = db.session.query(Budget).filter_by(user_id=user_id, category=category).first()
    if budget is None:
        budget = Budget(user_id=user_id, category=category, monthly_limit=monthly_limit)
        db.session.add(budget)
    else:
        budget.monthly_limit = monthly_limit
    db.session.commit()


def delete_budget(user_id, category):
    db.session.query(Budget).filter_by(user_id=user_id, category=category).delete()
    db.session.commit()
