from app.extensions import db
from app.models.orm import Bill


def get_bills_by_user(user_id):
    rows = db.session.query(Bill).filter_by(user_id=user_id).order_by(Bill.is_paid, Bill.due_date).all()
    return [b.to_dict() for b in rows]


def get_bill_by_id(bill_id, user_id):
    bill = db.session.query(Bill).filter_by(id=bill_id, user_id=user_id).first()
    return bill.to_dict() if bill else None


def get_upcoming_unpaid(user_id, cutoff_date):
    rows = (
        db.session.query(Bill)
        .filter(Bill.user_id == user_id, Bill.is_paid.is_(False), Bill.due_date <= cutoff_date)
        .all()
    )
    return [b.to_dict() for b in rows]


def create_bill(user_id, name, amount, due_date, repeat_frequency, bill_type=None):
    bill = Bill(
        user_id=user_id,
        name=name,
        amount=amount,
        due_date=due_date,
        repeat_frequency=repeat_frequency,
        bill_type=bill_type,
    )
    db.session.add(bill)
    db.session.commit()
    return bill.to_dict()


def mark_paid(bill_id, user_id):
    bill = db.session.query(Bill).filter_by(id=bill_id, user_id=user_id).first()
    if bill is None:
        return
    bill.is_paid = True
    db.session.commit()


def reschedule(bill_id, next_due_date):
    bill = db.session.get(Bill, bill_id)
    if bill is None:
        return
    bill.due_date = next_due_date
    bill.is_paid = False
    db.session.commit()


def delete_bill(bill_id, user_id):
    db.session.query(Bill).filter_by(id=bill_id, user_id=user_id).delete()
    db.session.commit()
