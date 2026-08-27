from app.extensions import db
from app.models.orm import Permission, Role, User


def get_role_by_name(name):
    role = db.session.query(Role).filter_by(name=name).first()
    return role.to_dict() if role else None


def get_role_by_id(role_id):
    role = db.session.get(Role, role_id)
    return role.to_dict() if role else None


def role_has_permission(role_id, permission_key):
    if role_id is None:
        return False
    role = db.session.get(Role, role_id)
    if role is None:
        return False
    return any(p.key == permission_key for p in role.permissions)


def list_permission_keys(role_id):
    if role_id is None:
        return []
    role = db.session.get(Role, role_id)
    return [p.key for p in role.permissions] if role else []


def list_roles_with_counts():
    roles = db.session.query(Role).order_by(Role.id).all()
    result = []
    for role in roles:
        user_count = db.session.query(User).filter_by(role_id=role.id).count()
        data = role.to_dict()
        data["user_count"] = user_count
        result.append(data)
    return result


def list_all_permissions():
    return [p.key for p in db.session.query(Permission).order_by(Permission.key).all()]


def set_role_permissions(role_id, permission_keys):
    role = db.session.get(Role, role_id)
    if role is None:
        return None
    if role.name == "SUPER_ADMIN":
        # Always has every permission — never editable, so it can't be
        # accidentally (or maliciously) downgraded via this endpoint.
        return None
    permissions = db.session.query(Permission).filter(Permission.key.in_(permission_keys)).all()
    role.permissions = permissions
    db.session.commit()
    return role.to_dict()
