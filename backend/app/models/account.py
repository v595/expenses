from app.extensions import db
from app.models.orm import Account


def get_accounts_by_user(user_id):
    rows = db.session.query(Account).filter_by(user_id=user_id).order_by(Account.name).all()
    return [a.to_dict() for a in rows]


def get_account_by_id(account_id, user_id):
    account = db.session.query(Account).filter_by(id=account_id, user_id=user_id).first()
    return account.to_dict() if account else None


def create_account(user_id, name, type_, balance, color):
    account = Account(user_id=user_id, name=name, type=type_, balance=balance, color=color)
    db.session.add(account)
    db.session.commit()
    return account.to_dict()


def update_account(account_id, user_id, name, type_, color):
    account = db.session.query(Account).filter_by(id=account_id, user_id=user_id).first()
    if account is None:
        return None
    account.name = name
    account.type = type_
    account.color = color
    db.session.commit()
    return account.to_dict()


def adjust_balance(account_id, delta):
    account = db.session.get(Account, account_id)
    if account is None:
        return
    account.balance = account.balance + delta
    db.session.commit()


def delete_account(account_id, user_id):
    db.session.query(Account).filter_by(id=account_id, user_id=user_id).delete()
    db.session.commit()
