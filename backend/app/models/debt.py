from app.extensions import db
from app.models.orm import Debt, now_iso


def get_debts_by_user(user_id):
    rows = db.session.query(Debt).filter_by(user_id=user_id).order_by(Debt.balance).all()
    return [d.to_dict() for d in rows]


def get_debt_by_id(debt_id, user_id):
    debt = db.session.query(Debt).filter_by(id=debt_id, user_id=user_id).first()
    return debt.to_dict() if debt else None


def create_debt(user_id, name, balance, interest_rate, min_payment):
    debt = Debt(
        user_id=user_id,
        name=name,
        balance=balance,
        interest_rate=interest_rate,
        min_payment=min_payment,
        created_at=now_iso(),
    )
    db.session.add(debt)
    db.session.commit()
    return debt.to_dict()


def update_debt(debt_id, user_id, name, balance, interest_rate, min_payment):
    debt = db.session.query(Debt).filter_by(id=debt_id, user_id=user_id).first()
    if debt is None:
        return None
    debt.name = name
    debt.balance = balance
    debt.interest_rate = interest_rate
    debt.min_payment = min_payment
    db.session.commit()
    return debt.to_dict()


def delete_debt(debt_id, user_id):
    db.session.query(Debt).filter_by(id=debt_id, user_id=user_id).delete()
    db.session.commit()
