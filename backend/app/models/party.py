from app.extensions import db
from app.models.orm import Party, now_iso


def get_parties_by_user(user_id, book_id=None, type_=None):
    query = db.session.query(Party).filter(Party.user_id == user_id)
    if book_id is not None:
        query = query.filter(Party.book_id == book_id)
    if type_:
        query = query.filter(Party.type == type_)
    rows = query.order_by(Party.name).all()
    return [p.to_dict() for p in rows]


def get_party_by_id(party_id, user_id):
    party = db.session.query(Party).filter_by(id=party_id, user_id=user_id).first()
    return party.to_dict() if party else None


def get_party_by_name(user_id, book_id, name, type_):
    party = (
        db.session.query(Party)
        .filter_by(user_id=user_id, book_id=book_id, name=name, type=type_)
        .first()
    )
    return party.to_dict() if party else None


def count_parties_for_book(book_id, user_id):
    return db.session.query(Party).filter_by(book_id=book_id, user_id=user_id).count()


def create_party(user_id, book_id, name, phone, type_, note):
    party = Party(
        user_id=user_id,
        book_id=book_id,
        name=name,
        phone=phone,
        type=type_,
        note=note,
        created_at=now_iso(),
    )
    db.session.add(party)
    db.session.commit()
    return party.to_dict()


def update_party(party_id, user_id, name, phone, type_, note):
    party = db.session.query(Party).filter_by(id=party_id, user_id=user_id).first()
    if party is None:
        return None
    party.name = name
    party.phone = phone
    party.type = type_
    party.note = note
    db.session.commit()
    return party.to_dict()


def delete_party(party_id, user_id):
    db.session.query(Party).filter_by(id=party_id, user_id=user_id).delete()
    db.session.commit()
