from app.extensions import db
from app.models.orm import Notification, now_iso


def get_notifications_by_user(user_id, limit=50):
    rows = (
        db.session.query(Notification)
        .filter_by(user_id=user_id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .limit(limit)
        .all()
    )
    return [n.to_dict() for n in rows]


def get_unread_count(user_id):
    return db.session.query(Notification).filter_by(user_id=user_id, is_read=False).count()


def exists_by_ref(user_id, ref_key):
    return db.session.query(Notification).filter_by(user_id=user_id, ref_key=ref_key).first() is not None


def create_notification(user_id, type_, title, message, ref_key):
    notification = Notification(
        user_id=user_id, type=type_, title=title, message=message, ref_key=ref_key, created_at=now_iso()
    )
    db.session.add(notification)
    db.session.commit()


def mark_read(notification_id, user_id):
    notification = db.session.query(Notification).filter_by(id=notification_id, user_id=user_id).first()
    if notification is None:
        return
    notification.is_read = True
    db.session.commit()


def mark_all_read(user_id):
    db.session.query(Notification).filter_by(user_id=user_id).update({"is_read": True})
    db.session.commit()


def delete_notification(notification_id, user_id):
    db.session.query(Notification).filter_by(id=notification_id, user_id=user_id).delete()
    db.session.commit()
