from app.extensions import db
from app.models.orm import ActivityLog, User, now_iso


def log(user_id, action, details=None, actor_id=None, target_user_id=None, entity_type=None, entity_id=None):
    entry = ActivityLog(
        user_id=user_id,
        action=action,
        details=details,
        created_at=now_iso(),
        actor_id=actor_id if actor_id is not None else user_id,
        target_user_id=target_user_id,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    db.session.add(entry)
    db.session.commit()


def get_recent(limit=50):
    rows = (
        db.session.query(ActivityLog, User.name, User.email)
        .join(User, User.id == ActivityLog.user_id)
        .order_by(ActivityLog.id.desc())
        .limit(limit)
        .all()
    )
    result = []
    for entry, user_name, user_email in rows:
        data = entry.to_dict()
        data["user_name"] = user_name
        data["user_email"] = user_email
        result.append(data)
    return result


def get_for_user(user_id, limit=100):
    rows = (
        db.session.query(ActivityLog)
        .filter_by(user_id=user_id)
        .order_by(ActivityLog.id.desc())
        .limit(limit)
        .all()
    )
    return [entry.to_dict() for entry in rows]


def get_audit_log(limit=100, offset=0, admin_actions_only=False):
    """The shared audit trail: every logged action, optionally narrowed to
    ones an admin performed on someone/something else (actor_id set and
    different from user_id, or a non-null entity_type)."""
    query = db.session.query(ActivityLog, User.name, User.email).outerjoin(User, User.id == ActivityLog.user_id)
    if admin_actions_only:
        query = query.filter(
            db.or_(
                db.and_(ActivityLog.actor_id.isnot(None), ActivityLog.actor_id != ActivityLog.user_id),
                ActivityLog.entity_type.isnot(None),
            )
        )
    rows = query.order_by(ActivityLog.id.desc()).offset(offset).limit(limit).all()

    result = []
    for entry, user_name, user_email in rows:
        data = entry.to_dict()
        data["user_name"] = user_name
        data["user_email"] = user_email
        result.append(data)
    return result


def get_security_events(limit=100, offset=0):
    rows = (
        db.session.query(ActivityLog)
        .filter(ActivityLog.entity_type == "security")
        .order_by(ActivityLog.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [entry.to_dict() for entry in rows]
