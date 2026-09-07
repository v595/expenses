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


def _apply_audit_filters(query, admin_actions_only=False, search=None, start_date=None, end_date=None, with_user=True):
    """Shared by every log listing/count — `query` must already be joined to
    User when with_user is True (get_audit_log needs it anyway for
    user_name/email; count_audit_log joins it purely so `search` can match
    "who did this" the same way an admin actually thinks to search)."""
    if admin_actions_only:
        query = query.filter(
            db.or_(
                db.and_(ActivityLog.actor_id.isnot(None), ActivityLog.actor_id != ActivityLog.user_id),
                ActivityLog.entity_type.isnot(None),
            )
        )
    if search:
        like = f"%{search}%"
        clauses = [ActivityLog.action.like(like), ActivityLog.details.like(like)]
        if with_user:
            clauses += [User.name.like(like), User.email.like(like)]
        query = query.filter(db.or_(*clauses))
    if start_date:
        query = query.filter(ActivityLog.created_at >= start_date)
    if end_date:
        # created_at carries a time component, so an inclusive end date needs
        # the very end of that day, not midnight at its start.
        query = query.filter(ActivityLog.created_at <= f"{end_date} 23:59:59")
    return query


def get_audit_log(limit=100, offset=0, admin_actions_only=False, search=None, start_date=None, end_date=None):
    """The shared audit trail: every logged action, optionally narrowed to
    ones an admin performed on someone/something else (actor_id set and
    different from user_id, or a non-null entity_type)."""
    query = db.session.query(ActivityLog, User.name, User.email).outerjoin(User, User.id == ActivityLog.user_id)
    query = _apply_audit_filters(query, admin_actions_only, search, start_date, end_date)
    rows = query.order_by(ActivityLog.id.desc()).offset(offset).limit(limit).all()

    result = []
    for entry, user_name, user_email in rows:
        data = entry.to_dict()
        data["user_name"] = user_name
        data["user_email"] = user_email
        result.append(data)
    return result


def count_audit_log(admin_actions_only=False, search=None, start_date=None, end_date=None):
    query = db.session.query(ActivityLog).outerjoin(User, User.id == ActivityLog.user_id)
    query = _apply_audit_filters(query, admin_actions_only, search, start_date, end_date)
    return query.count()


def get_security_events(limit=100, offset=0, search=None, start_date=None, end_date=None):
    query = (
        db.session.query(ActivityLog, User.name, User.email)
        .outerjoin(User, User.id == ActivityLog.user_id)
        .filter(ActivityLog.entity_type == "security")
    )
    query = _apply_audit_filters(query, search=search, start_date=start_date, end_date=end_date)
    rows = query.order_by(ActivityLog.id.desc()).offset(offset).limit(limit).all()
    result = []
    for entry, user_name, user_email in rows:
        data = entry.to_dict()
        data["user_name"] = user_name
        data["user_email"] = user_email
        result.append(data)
    return result


def count_security_events(search=None, start_date=None, end_date=None):
    query = (
        db.session.query(ActivityLog)
        .outerjoin(User, User.id == ActivityLog.user_id)
        .filter(ActivityLog.entity_type == "security")
    )
    query = _apply_audit_filters(query, search=search, start_date=start_date, end_date=end_date)
    return query.count()
