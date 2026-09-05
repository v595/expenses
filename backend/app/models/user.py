from app.extensions import db
from app.models.orm import Role, User, now_iso


def count_users():
    return db.session.query(User).count()


def create_user(name, email, password_hash):
    user = User(name=name, email=email, password_hash=password_hash, created_at=now_iso())
    user_role = db.session.query(Role).filter_by(name="USER").first()
    if user_role is not None:
        user.role_id = user_role.id
    db.session.add(user)
    db.session.commit()
    return user.to_dict()


def promote_first_user_if_no_admin():
    """The very first account ever registered becomes the admin, so there's
    always someone who can see the admin dashboard without a manual DB edit.
    Called both at app startup and right after each registration, so the
    invariant holds immediately rather than waiting for the next boot."""
    if db.session.query(User).filter_by(is_admin=True).count() > 0:
        return
    first_user = db.session.query(User).order_by(User.id).first()
    if first_user is None:
        return
    first_user.is_admin = True
    super_admin_role = db.session.query(Role).filter_by(name="SUPER_ADMIN").first()
    if super_admin_role is not None:
        first_user.role_id = super_admin_role.id
    db.session.commit()


def suspend_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return None
    user.is_suspended = True
    user.token = None  # force out any existing session immediately
    db.session.commit()
    return user.to_dict()


def activate_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return None
    user.is_suspended = False
    db.session.commit()
    return user.to_dict()


def set_role(user_id, role_id):
    user = db.session.get(User, user_id)
    if user is None:
        return None
    role = db.session.get(Role, role_id) if role_id is not None else None
    user.role_id = role_id
    user.is_admin = role is not None and role.name in ("ADMIN", "SUPER_ADMIN")
    db.session.commit()
    return user.to_dict()


def get_users_by_role_names(role_names):
    return [
        u.to_dict()
        for u in db.session.query(User).join(Role, Role.id == User.role_id).filter(Role.name.in_(role_names)).all()
    ]


def get_user_by_email(email):
    user = db.session.query(User).filter_by(email=email).first()
    return user.to_dict() if user else None


def get_user_by_id(user_id):
    user = db.session.get(User, user_id)
    return user.to_dict() if user else None


def get_user_by_token(token):
    user = db.session.query(User).filter_by(token=token).first()
    return user.to_dict() if user else None


def update_name(user_id, name):
    user = db.session.get(User, user_id)
    user.name = name
    db.session.commit()
    return user.to_dict()


def update_avatar(user_id, avatar):
    user = db.session.get(User, user_id)
    user.avatar = avatar
    db.session.commit()
    return user.to_dict()


def update_password(user_id, password_hash):
    user = db.session.get(User, user_id)
    user.password_hash = password_hash
    db.session.commit()


def set_user_token(user_id, token):
    user = db.session.get(User, user_id)
    user.token = token
    db.session.commit()


def record_login(user_id, timestamp):
    user = db.session.get(User, user_id)
    user.last_login_at = timestamp
    db.session.commit()


def update_settings(user_id, currency, notify_budget_alerts, notify_bill_reminders):
    user = db.session.get(User, user_id)
    user.currency = currency
    user.notify_budget_alerts = notify_budget_alerts
    user.notify_bill_reminders = notify_bill_reminders
    db.session.commit()
    return user.to_dict()


def delete_user(user_id):
    # No ON DELETE CASCADE in this schema, so every table that references a
    # user gets cleaned up by hand, in dependency order (children first).
    from app.models.orm import (
        Account,
        ActivityLog,
        Bill,
        Book,
        Budget,
        Category,
        Goal,
        LedgerEntry,
        Notification,
        Party,
        RecurringTransaction,
        Reminder,
        Tag,
        Transaction,
        transaction_tags,
    )

    transaction_ids = [
        row[0] for row in db.session.query(Transaction.id).filter_by(user_id=user_id).all()
    ]
    if transaction_ids:
        db.session.execute(
            transaction_tags.delete().where(transaction_tags.c.transaction_id.in_(transaction_ids))
        )
    db.session.query(Transaction).filter_by(user_id=user_id).delete()
    # Books sit at the top of the khatabook chain, so reminders/ledger
    # entries/parties go first, then the books themselves.
    db.session.query(Reminder).filter_by(user_id=user_id).delete()
    db.session.query(LedgerEntry).filter_by(user_id=user_id).delete()
    db.session.query(Party).filter_by(user_id=user_id).delete()
    db.session.query(Book).filter_by(user_id=user_id).delete()
    db.session.query(Tag).filter_by(user_id=user_id).delete()
    db.session.query(Budget).filter_by(user_id=user_id).delete()
    db.session.query(RecurringTransaction).filter_by(user_id=user_id).delete()
    db.session.query(Account).filter_by(user_id=user_id).delete()
    db.session.query(Category).filter_by(user_id=user_id).delete()
    db.session.query(Goal).filter_by(user_id=user_id).delete()
    db.session.query(Bill).filter_by(user_id=user_id).delete()
    db.session.query(Notification).filter_by(user_id=user_id).delete()
    db.session.query(ActivityLog).filter_by(user_id=user_id).delete()
    db.session.query(User).filter_by(id=user_id).delete()
    db.session.commit()
