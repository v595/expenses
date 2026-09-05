from app.extensions import db
from app.models.orm import Party, Reminder, now_iso


def get_reminders_by_user(user_id, book_id=None, party_id=None, limit=100):
    """Reminder history, newest first, with the party's name attached so the
    history list doesn't need a second round trip."""
    query = (
        db.session.query(Reminder, Party.name)
        .join(Party, Party.id == Reminder.party_id)
        .filter(Reminder.user_id == user_id)
    )
    if book_id is not None:
        query = query.filter(Reminder.book_id == book_id)
    if party_id is not None:
        query = query.filter(Reminder.party_id == party_id)

    rows = query.order_by(Reminder.id.desc()).limit(limit).all()
    result = []
    for reminder, party_name in rows:
        data = reminder.to_dict()
        data["party_name"] = party_name
        result.append(data)
    return result


def get_reminder_by_id(reminder_id, user_id):
    reminder = db.session.query(Reminder).filter_by(id=reminder_id, user_id=user_id).first()
    return reminder.to_dict() if reminder else None


def create_reminder(user_id, book_id, party_id, channel, message, status="pending"):
    reminder = Reminder(
        user_id=user_id,
        book_id=book_id,
        party_id=party_id,
        channel=channel,
        message=message,
        status=status,
        created_at=now_iso(),
    )
    db.session.add(reminder)
    db.session.commit()
    return reminder.to_dict()


def set_status(reminder_id, user_id, status, sent_at=None):
    reminder = db.session.query(Reminder).filter_by(id=reminder_id, user_id=user_id).first()
    if reminder is None:
        return None
    reminder.status = status
    reminder.sent_at = sent_at
    db.session.commit()
    return reminder.to_dict()


def delete_reminders_for_party(party_id, user_id):
    db.session.query(Reminder).filter_by(party_id=party_id, user_id=user_id).delete()
    db.session.commit()
