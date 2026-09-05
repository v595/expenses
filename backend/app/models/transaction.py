from app.extensions import db
from app.models.orm import Transaction, now_iso, transaction_tags


def create_transaction(user_id, amount, type_, category, description, date, account_id=None, receipt=None, category_id=None):
    transaction = Transaction(
        user_id=user_id,
        amount=amount,
        type=type_,
        category=category,
        category_id=category_id,
        description=description,
        date=date,
        account_id=account_id,
        receipt=receipt,
        created_at=now_iso(),
    )
    db.session.add(transaction)
    db.session.commit()
    return transaction.to_dict()


def get_transactions_by_user(
    user_id, category=None, type_=None, start_date=None, end_date=None, search=None, tag_id=None
):
    query = db.session.query(Transaction).filter(Transaction.user_id == user_id)

    if category:
        query = query.filter(Transaction.category == category)
    if type_:
        query = query.filter(Transaction.type == type_)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(Transaction.category.like(like), Transaction.description.like(like))
        )
    if tag_id:
        query = query.join(transaction_tags).filter(transaction_tags.c.tag_id == tag_id)

    rows = query.order_by(Transaction.date.desc(), Transaction.id.desc()).all()
    return [t.to_dict() for t in rows]


def get_transaction_by_id(transaction_id):
    transaction = db.session.get(Transaction, transaction_id)
    return transaction.to_dict() if transaction else None


def update_transaction(transaction_id, amount, type_, category, description, date, account_id=None, receipt=None, category_id=None):
    transaction = db.session.get(Transaction, transaction_id)
    if transaction is None:
        return None
    transaction.amount = amount
    transaction.type = type_
    transaction.category = category
    transaction.category_id = category_id
    transaction.description = description
    transaction.date = date
    transaction.account_id = account_id
    transaction.receipt = receipt
    db.session.commit()
    return transaction.to_dict()


def unassign_book(book_id, user_id):
    """Drops a deleted book's id off any transaction still pointing at it.
    book_id is nullable precisely so a transaction outlives its book instead
    of being deleted with it."""
    db.session.query(Transaction).filter_by(book_id=book_id, user_id=user_id).update(
        {Transaction.book_id: None}
    )
    db.session.commit()


def delete_transaction(transaction_id):
    db.session.execute(transaction_tags.delete().where(transaction_tags.c.transaction_id == transaction_id))
    db.session.query(Transaction).filter_by(id=transaction_id).delete()
    db.session.commit()


def get_totals(user_id):
    row = db.session.execute(
        db.text(
            """
            SELECT
                COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) AS income,
                COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) AS expenses,
                COUNT(*) AS transaction_count
            FROM transactions
            WHERE user_id = :user_id
            """
        ),
        {"user_id": user_id},
    ).mappings().first()
    return dict(row)


def get_category_spending(user_id):
    rows = db.session.execute(
        db.text(
            """
            SELECT category, SUM(amount) AS total
            FROM transactions
            WHERE user_id = :user_id AND type = 'expense'
            GROUP BY category
            ORDER BY total DESC
            """
        ),
        {"user_id": user_id},
    ).mappings().all()
    return [dict(row) for row in rows]


def get_category_spending_for_month(user_id, year_month):
    rows = db.session.execute(
        db.text(
            """
            SELECT category, SUM(amount) AS total
            FROM transactions
            WHERE user_id = :user_id AND type = 'expense' AND SUBSTR(date, 1, 7) = :year_month
            GROUP BY category
            """
        ),
        {"user_id": user_id, "year_month": year_month},
    ).mappings().all()
    return {row["category"]: row["total"] for row in rows}


def get_monthly_totals(user_id):
    rows = db.session.execute(
        db.text(
            """
            SELECT
                SUBSTR(date, 1, 7) AS month,
                COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) AS income,
                COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) AS expenses
            FROM transactions
            WHERE user_id = :user_id
            GROUP BY month
            ORDER BY month
            """
        ),
        {"user_id": user_id},
    ).mappings().all()
    return [dict(row) for row in rows]
