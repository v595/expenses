from app.extensions import db
from app.models.orm import FeatureFlag, now_iso


def list_flags():
    rows = db.session.query(FeatureFlag).order_by(FeatureFlag.name).all()
    return [f.to_dict() for f in rows]


def get_flag(key):
    flag = db.session.query(FeatureFlag).filter_by(key=key).first()
    return flag.to_dict() if flag else None


def is_enabled(key):
    flag = db.session.query(FeatureFlag).filter_by(key=key).first()
    return bool(flag and flag.is_enabled)


def set_enabled(key, enabled):
    flag = db.session.query(FeatureFlag).filter_by(key=key).first()
    if flag is None:
        return None
    flag.is_enabled = enabled
    flag.updated_at = now_iso()
    db.session.commit()
    return flag.to_dict()
