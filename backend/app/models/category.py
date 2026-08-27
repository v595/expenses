from app.extensions import db
from app.models.orm import Category


def get_categories_by_user(user_id):
    rows = db.session.query(Category).filter_by(user_id=user_id).order_by(Category.type, Category.name).all()
    return [c.to_dict() for c in rows]


def get_category_by_name(user_id, name, type_):
    category = db.session.query(Category).filter_by(user_id=user_id, name=name, type=type_).first()
    return category.to_dict() if category else None


def create_category(user_id, name, type_, color):
    category = Category(user_id=user_id, name=name, type=type_, color=color)
    db.session.add(category)
    db.session.commit()
    return category.to_dict()


def get_or_create_category(user_id, name, type_):
    category = db.session.query(Category).filter_by(user_id=user_id, name=name, type=type_).first()
    if category is None:
        category = Category(user_id=user_id, name=name, type=type_)
        db.session.add(category)
        db.session.commit()
    return category.to_dict()


def get_category_by_id(category_id, user_id):
    category = db.session.query(Category).filter_by(id=category_id, user_id=user_id).first()
    return category.to_dict() if category else None


def delete_category(category_id, user_id):
    db.session.query(Category).filter_by(id=category_id, user_id=user_id).delete()
    db.session.commit()
