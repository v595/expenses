from app.extensions import db
from app.models.orm import SystemSetting, now_iso


def get_all():
    rows = db.session.query(SystemSetting).order_by(SystemSetting.key).all()
    return {row.key: row.value for row in rows}


def get(key, default=None):
    row = db.session.query(SystemSetting).filter_by(key=key).first()
    return row.value if row else default


def set_value(key, value):
    row = db.session.query(SystemSetting).filter_by(key=key).first()
    if row is None:
        row = SystemSetting(key=key, value=value, updated_at=now_iso())
        db.session.add(row)
    else:
        row.value = value
        row.updated_at = now_iso()
    db.session.commit()
    return row.to_dict()
