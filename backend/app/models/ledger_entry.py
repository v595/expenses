"""Ledger entries, and THE single definition of the balance sign convention.

    balance = SUM(amount WHERE direction = 'given') - SUM(amount WHERE direction = 'got')

  * `given`  — you gave money/goods/credit out. For a **customer** that's the
    goods or credit you handed over, so they now owe you. For a **supplier**
    it's you paying them, which reduces what you owe them.
  * `got`    — money/goods came back in. From a **customer** that's them
    paying you; from a **supplier** it's stock they gave you on credit.

  * A **positive** balance means "You'll get" — the party owes you (a
    receivable).
  * A **negative** balance means "You'll give" — you owe the party (a
    payable).
  * Zero means settled.

The sign flip between customer and supplier therefore falls out of which
direction each side's entries are recorded in — it is NOT a second rule
applied on top, and nothing outside this module may re-derive it. Everything
that needs a balance (parties list, statements, cashbook, receivables
summary, reminders) calls in here.
"""

from app.extensions import db
from app.models.orm import LedgerEntry, Party, now_iso

GIVEN = "given"
GOT = "got"
VALID_DIRECTIONS = (GIVEN, GOT)


def signed_amount(amount, direction):
    """Python-side counterpart of `_signed_column()` — the one conversion from
    (amount, direction) to a signed contribution to the balance."""
    return float(amount) if direction == GIVEN else -float(amount)


def _signed_column():
    """SQL-side counterpart of `signed_amount()`."""
    return db.case((LedgerEntry.direction == GIVEN, LedgerEntry.amount), else_=-LedgerEntry.amount)


def describe_balance(balance):
    """Turns a raw balance into the labelled shape every read API returns, so
    the "positive means you'll get" reading is written down exactly once."""
    rounded = round(float(balance or 0), 2)
    if rounded > 0:
        direction = "you_will_get"
        label = "You'll get"
    elif rounded < 0:
        direction = "you_will_give"
        label = "You'll give"
    else:
        direction = "settled"
        label = "Settled"
    return {
        "balance": rounded,
        "balance_direction": direction,
        "balance_label": label,
        # Always non-negative, for UIs that render the label and the number
        # separately ("You'll get ₹500") rather than showing a minus sign.
        "balance_abs": abs(rounded),
    }


def _scoped(user_id):
    return db.session.query(LedgerEntry).filter(LedgerEntry.user_id == user_id)


def get_entry_by_id(entry_id, user_id):
    entry = db.session.query(LedgerEntry).filter_by(id=entry_id, user_id=user_id).first()
    return entry.to_dict() if entry else None


def get_entries_for_party(party_id, user_id, start_date=None, end_date=None):
    query = _scoped(user_id).filter(LedgerEntry.party_id == party_id)
    if start_date:
        query = query.filter(LedgerEntry.date >= start_date)
    if end_date:
        query = query.filter(LedgerEntry.date <= end_date)
    rows = query.order_by(LedgerEntry.date, LedgerEntry.id).all()
    return [e.to_dict() for e in rows]


def get_entries_for_book(book_id, user_id, start_date=None, end_date=None):
    """Book-wide entries with their party's name/type attached — what the
    cashbook renders."""
    query = (
        db.session.query(LedgerEntry, Party.name, Party.type)
        .join(Party, Party.id == LedgerEntry.party_id)
        .filter(LedgerEntry.user_id == user_id, LedgerEntry.book_id == book_id)
    )
    if start_date:
        query = query.filter(LedgerEntry.date >= start_date)
    if end_date:
        query = query.filter(LedgerEntry.date <= end_date)

    rows = query.order_by(LedgerEntry.date, LedgerEntry.id).all()
    result = []
    for entry, party_name, party_type in rows:
        data = entry.to_dict()
        data["party_name"] = party_name
        data["party_type"] = party_type
        result.append(data)
    return result


def _apply_date_window(query, start_date=None, end_date=None, before_date=None):
    if start_date:
        query = query.filter(LedgerEntry.date >= start_date)
    if end_date:
        query = query.filter(LedgerEntry.date <= end_date)
    if before_date:
        # Strictly earlier — this is what an "opening balance" is made of.
        query = query.filter(LedgerEntry.date < before_date)
    return query


def get_balance_for_party(party_id, user_id, start_date=None, end_date=None, before_date=None):
    query = db.session.query(db.func.coalesce(db.func.sum(_signed_column()), 0.0)).filter(
        LedgerEntry.user_id == user_id, LedgerEntry.party_id == party_id
    )
    query = _apply_date_window(query, start_date, end_date, before_date)
    return round(float(query.scalar() or 0), 2)


def get_balance_for_book(book_id, user_id, start_date=None, end_date=None, before_date=None):
    query = db.session.query(db.func.coalesce(db.func.sum(_signed_column()), 0.0)).filter(
        LedgerEntry.user_id == user_id, LedgerEntry.book_id == book_id
    )
    query = _apply_date_window(query, start_date, end_date, before_date)
    return round(float(query.scalar() or 0), 2)


def get_balances_for_parties(party_ids, user_id, start_date=None, end_date=None):
    """{party_id: balance} for a batch of parties, so a list endpoint doesn't
    run one aggregate query per row."""
    if not party_ids:
        return {}
    query = (
        db.session.query(LedgerEntry.party_id, db.func.coalesce(db.func.sum(_signed_column()), 0.0))
        .filter(LedgerEntry.user_id == user_id, LedgerEntry.party_id.in_(list(party_ids)))
        .group_by(LedgerEntry.party_id)
    )
    query = _apply_date_window(query, start_date, end_date)
    balances = {party_id: round(float(total or 0), 2) for party_id, total in query.all()}
    return {party_id: balances.get(party_id, 0.0) for party_id in party_ids}


def get_earliest_due_dates(party_ids, user_id):
    """{party_id: earliest due_date} across the party's outstanding `given`
    entries — what decides whether a due is "overdue"."""
    if not party_ids:
        return {}
    rows = (
        db.session.query(LedgerEntry.party_id, db.func.min(LedgerEntry.due_date))
        .filter(
            LedgerEntry.user_id == user_id,
            LedgerEntry.party_id.in_(list(party_ids)),
            LedgerEntry.direction == GIVEN,
            LedgerEntry.due_date.isnot(None),
        )
        .group_by(LedgerEntry.party_id)
        .all()
    )
    return {party_id: due_date for party_id, due_date in rows}


def create_entry(user_id, book_id, party_id, amount, direction, description, date, due_date=None):
    entry = LedgerEntry(
        user_id=user_id,
        book_id=book_id,
        party_id=party_id,
        amount=amount,
        direction=direction,
        description=description,
        date=date,
        due_date=due_date,
        created_at=now_iso(),
    )
    db.session.add(entry)
    db.session.commit()
    return entry.to_dict()


def update_entry(entry_id, user_id, amount, direction, description, date, due_date=None):
    entry = db.session.query(LedgerEntry).filter_by(id=entry_id, user_id=user_id).first()
    if entry is None:
        return None
    entry.amount = amount
    entry.direction = direction
    entry.description = description
    entry.date = date
    entry.due_date = due_date
    db.session.commit()
    return entry.to_dict()


def delete_entry(entry_id, user_id):
    db.session.query(LedgerEntry).filter_by(id=entry_id, user_id=user_id).delete()
    db.session.commit()


def delete_entries_for_party(party_id, user_id):
    db.session.query(LedgerEntry).filter_by(party_id=party_id, user_id=user_id).delete()
    db.session.commit()


def count_entries_for_book(book_id, user_id):
    return _scoped(user_id).filter(LedgerEntry.book_id == book_id).count()
