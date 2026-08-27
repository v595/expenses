from app.extensions import db
from app.models.orm import Tag, transaction_tags


def get_tags_by_user(user_id):
    rows = db.session.query(Tag).filter_by(user_id=user_id).order_by(Tag.name).all()
    return [t.to_dict() for t in rows]


def get_or_create_tag(user_id, name):
    tag = db.session.query(Tag).filter_by(user_id=user_id, name=name).first()
    if tag is None:
        tag = Tag(user_id=user_id, name=name)
        db.session.add(tag)
        db.session.commit()
    return tag.to_dict()


def set_tags_for_transaction(transaction_id, tag_ids):
    db.session.execute(transaction_tags.delete().where(transaction_tags.c.transaction_id == transaction_id))
    for tag_id in tag_ids:
        db.session.execute(transaction_tags.insert().values(transaction_id=transaction_id, tag_id=tag_id))
    db.session.commit()


def get_tags_for_transaction(transaction_id):
    rows = db.session.execute(
        db.select(Tag.id, Tag.name)
        .join(transaction_tags, transaction_tags.c.tag_id == Tag.id)
        .where(transaction_tags.c.transaction_id == transaction_id)
        .order_by(Tag.name)
    ).all()
    return [{"id": row.id, "name": row.name} for row in rows]


def get_tags_for_transactions(transaction_ids):
    if not transaction_ids:
        return {}

    rows = db.session.execute(
        db.select(transaction_tags.c.transaction_id, Tag.id, Tag.name)
        .join(transaction_tags, transaction_tags.c.tag_id == Tag.id)
        .where(transaction_tags.c.transaction_id.in_(transaction_ids))
        .order_by(Tag.name)
    ).all()

    result = {tid: [] for tid in transaction_ids}
    for row in rows:
        result[row.transaction_id].append({"id": row.id, "name": row.name})
    return result


def delete_tag(tag_id, user_id):
    owned = db.session.query(Tag).filter_by(id=tag_id, user_id=user_id).first()
    if owned is None:
        return
    db.session.execute(transaction_tags.delete().where(transaction_tags.c.tag_id == tag_id))
    db.session.query(Tag).filter_by(id=tag_id, user_id=user_id).delete()
    db.session.commit()
