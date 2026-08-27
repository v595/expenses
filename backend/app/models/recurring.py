from app.extensions import db
from app.models.orm import RecurringTransaction


def get_recurring_by_user(user_id):
    rows = (
        db.session.query(RecurringTransaction)
        .filter_by(user_id=user_id)
        .order_by(RecurringTransaction.next_date)
        .all()
    )
    return [r.to_dict() for r in rows]


def get_due_recurring(user_id, today):
    rows = (
        db.session.query(RecurringTransaction)
        .filter(RecurringTransaction.user_id == user_id, RecurringTransaction.next_date <= today)
        .all()
    )
    return [r.to_dict() for r in rows]


def create_recurring(user_id, amount, type_, category, description, frequency, next_date):
    recurring = RecurringTransaction(
        user_id=user_id,
        amount=amount,
        type=type_,
        category=category,
        description=description,
        frequency=frequency,
        next_date=next_date,
    )
    db.session.add(recurring)
    db.session.commit()
    return recurring.to_dict()


def update_next_date(recurring_id, next_date):
    recurring = db.session.get(RecurringTransaction, recurring_id)
    if recurring is None:
        return
    recurring.next_date = next_date
    db.session.commit()


def delete_recurring(recurring_id, user_id):
    db.session.query(RecurringTransaction).filter_by(id=recurring_id, user_id=user_id).delete()
    db.session.commit()
