from datetime import datetime, timezone

from app.extensions import db


def now_iso():
    """UTC timestamp string in the exact 'YYYY-MM-DD HH:MM:SS' format the rest
    of the app (activity feed, admin dashboard's _time_ago, frontend date
    parsing) has always stored/expected — kept as plain TEXT columns rather
    than a native DateTime type so that format never drifts."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


# Plain association table (no extra columns) for the transactions<->tags
# many-to-many relationship — mirrors the original transaction_tags table.
transaction_tags = db.Table(
    "transaction_tags",
    db.Column("transaction_id", db.Integer, db.ForeignKey("transactions.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id"), primary_key=True),
)

# Role <-> Permission many-to-many.
role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey("permissions.id"), primary_key=True),
)


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False, unique=True)
    description = db.Column(db.Text)

    permissions = db.relationship("Permission", secondary=role_permissions, backref="roles")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "permissions": [p.key for p in self.permissions],
        }


class Permission(db.Model):
    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.Text, nullable=False, unique=True)
    description = db.Column(db.Text)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False, unique=True)
    password_hash = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.Text, nullable=False, default=now_iso)
    token = db.Column(db.Text)
    avatar = db.Column(db.Text)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    currency = db.Column(db.Text, nullable=False, default="INR")
    notify_budget_alerts = db.Column(db.Boolean, nullable=False, default=True)
    notify_bill_reminders = db.Column(db.Boolean, nullable=False, default=True)
    last_login_at = db.Column(db.Text)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))
    is_suspended = db.Column(db.Boolean, nullable=False, default=False)

    role = db.relationship("Role")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "password_hash": self.password_hash,
            "created_at": self.created_at,
            "token": self.token,
            "avatar": self.avatar,
            "is_admin": self.is_admin,
            "currency": self.currency,
            "notify_budget_alerts": self.notify_budget_alerts,
            "notify_bill_reminders": self.notify_bill_reminders,
            "last_login_at": self.last_login_at,
            "role_id": self.role_id,
            "role_name": self.role.name if self.role is not None else None,
            "is_suspended": self.is_suspended,
        }


class Account(db.Model):
    __tablename__ = "accounts"
    __table_args__ = (db.UniqueConstraint("user_id", "name"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.Text, nullable=False)
    type = db.Column(db.Text, nullable=False, default="cash")
    balance = db.Column(db.Float, nullable=False, default=0)
    color = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "type": self.type,
            "balance": self.balance,
            "color": self.color,
        }


class Category(db.Model):
    __tablename__ = "categories"
    __table_args__ = (
        db.UniqueConstraint("user_id", "name", "type"),
        db.CheckConstraint("type IN ('income', 'expense')"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.Text, nullable=False)
    type = db.Column(db.Text, nullable=False)
    color = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "type": self.type,
            "color": self.color,
        }


class Transaction(db.Model):
    __tablename__ = "transactions"
    __table_args__ = (db.CheckConstraint("type IN ('income', 'expense')"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.Text, nullable=False)
    category = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    description = db.Column(db.Text)
    date = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.Text, nullable=False, default=now_iso)
    # No FK constraint here, matching the original schema exactly: an
    # account can be deleted while transactions still carry its old id.
    account_id = db.Column(db.Integer)
    receipt = db.Column(db.Text)
    # Which Book (workspace) this transaction belongs to. Nullable on purpose:
    # every pre-Books transaction, and any client that doesn't send one yet,
    # keeps working exactly as before. The 0004 migration backfills existing
    # rows onto each user's default book.
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"))

    tags = db.relationship("Tag", secondary=transaction_tags, backref="transactions")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "type": self.type,
            "category": self.category,
            "category_id": self.category_id,
            "description": self.description,
            "date": self.date,
            "created_at": self.created_at,
            "account_id": self.account_id,
            "receipt": self.receipt,
            "book_id": self.book_id,
        }


class Budget(db.Model):
    __tablename__ = "budgets"
    __table_args__ = (db.UniqueConstraint("user_id", "category"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category = db.Column(db.Text, nullable=False)
    monthly_limit = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {"category": self.category, "monthly_limit": self.monthly_limit}


class RecurringTransaction(db.Model):
    __tablename__ = "recurring_transactions"
    __table_args__ = (
        db.CheckConstraint("type IN ('income', 'expense')"),
        db.CheckConstraint("frequency IN ('weekly', 'monthly', 'yearly')"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.Text, nullable=False)
    category = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    frequency = db.Column(db.Text, nullable=False)
    next_date = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "type": self.type,
            "category": self.category,
            "description": self.description,
            "frequency": self.frequency,
            "next_date": self.next_date,
        }


class Goal(db.Model):
    __tablename__ = "goals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.Text, nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, nullable=False, default=0)
    target_date = db.Column(db.Text)
    created_at = db.Column(db.Text, nullable=False, default=now_iso)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "target_amount": self.target_amount,
            "current_amount": self.current_amount,
            "target_date": self.target_date,
            "created_at": self.created_at,
        }


class Bill(db.Model):
    __tablename__ = "bills"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Text, nullable=False)
    is_paid = db.Column(db.Boolean, nullable=False, default=False)
    repeat_frequency = db.Column(db.Text)
    # Which kind of bill this is (electricity, rent, ...) — drives the icon in
    # the UI. Nullable so bills created before this existed still load.
    bill_type = db.Column(db.Text)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "amount": self.amount,
            "due_date": self.due_date,
            "is_paid": self.is_paid,
            "repeat_frequency": self.repeat_frequency,
            "bill_type": self.bill_type,
        }


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    type = db.Column(db.Text, nullable=False)
    title = db.Column(db.Text, nullable=False)
    message = db.Column(db.Text)
    ref_key = db.Column(db.Text)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.Text, nullable=False, default=now_iso)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "ref_key": self.ref_key,
            "is_read": self.is_read,
            "created_at": self.created_at,
        }


class Tag(db.Model):
    __tablename__ = "tags"
    __table_args__ = (db.UniqueConstraint("user_id", "name"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {"id": self.id, "user_id": self.user_id, "name": self.name}


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    # Nullable: a failed-login security event may not resolve to a real
    # user (e.g. the attempted email doesn't exist), and still needs to be
    # recorded.
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.Text, nullable=False)
    details = db.Column(db.Text)
    created_at = db.Column(db.Text, nullable=False, default=now_iso)

    # Audit-trail fields: who actually performed the action (defaults to the
    # same user for self-actions) and, for admin-on-user actions, who was
    # affected. entity_type/entity_id are a generic pointer (e.g. "user"/5)
    # so a future Audit Log page can filter on `actor_id != target_user_id`
    # without a separate table duplicating this one. Deliberately NOT FK
    # constraints: an admin action's target user can later be deleted, and
    # the log entry should keep the numeric id rather than being blocked or
    # nulled out by that deletion.
    actor_id = db.Column(db.Integer)
    target_user_id = db.Column(db.Integer)
    entity_type = db.Column(db.Text)
    entity_id = db.Column(db.Integer)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "details": self.details,
            "created_at": self.created_at,
            "actor_id": self.actor_id,
            "target_user_id": self.target_user_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
        }


class FeatureFlag(db.Model):
    __tablename__ = "feature_flags"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.Text, nullable=False, unique=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    is_enabled = db.Column(db.Boolean, nullable=False, default=False)
    updated_at = db.Column(db.Text, nullable=False, default=now_iso)

    def to_dict(self):
        return {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "is_enabled": self.is_enabled,
            "updated_at": self.updated_at,
        }


class SystemSetting(db.Model):
    __tablename__ = "system_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.Text, nullable=False, unique=True)
    value = db.Column(db.Text)
    updated_at = db.Column(db.Text, nullable=False, default=now_iso)

    def to_dict(self):
        return {"key": self.key, "value": self.value, "updated_at": self.updated_at}


class Book(db.Model):
    """A workspace the user switches between (Business / Personal / Home /
    Daily). Every user always has at least one — see
    `app.models.book.ensure_default_book`."""

    __tablename__ = "books"
    __table_args__ = (
        db.UniqueConstraint("user_id", "name"),
        db.CheckConstraint("type IN ('business', 'personal', 'home', 'daily')"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.Text, nullable=False)
    type = db.Column(db.Text, nullable=False, default="personal")
    is_default = db.Column(db.Boolean, nullable=False, default=False)
    color = db.Column(db.Text)
    created_at = db.Column(db.Text, nullable=False, default=now_iso)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "type": self.type,
            "is_default": self.is_default,
            "color": self.color,
            "created_at": self.created_at,
        }


class Party(db.Model):
    """A customer or supplier a book keeps a running ledger with."""

    __tablename__ = "parties"
    __table_args__ = (
        db.UniqueConstraint("book_id", "name", "type"),
        db.CheckConstraint("type IN ('customer', 'supplier')"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    name = db.Column(db.Text, nullable=False)
    # Stored normalised to digits plus an optional leading '+', so the same
    # number always renders (and builds a wa.me link) the same way.
    phone = db.Column(db.Text)
    type = db.Column(db.Text, nullable=False)
    note = db.Column(db.Text)
    created_at = db.Column(db.Text, nullable=False, default=now_iso)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "book_id": self.book_id,
            "name": self.name,
            "phone": self.phone,
            "type": self.type,
            "note": self.note,
            "created_at": self.created_at,
        }


class LedgerEntry(db.Model):
    """One credit/debit line against a party. The meaning of `direction` and
    how it rolls up into a balance lives in exactly one place —
    `app.models.ledger_entry` — never re-derive the sign anywhere else."""

    __tablename__ = "ledger_entries"
    __table_args__ = (
        db.CheckConstraint("direction IN ('given', 'got')"),
        db.CheckConstraint("amount > 0"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    party_id = db.Column(db.Integer, db.ForeignKey("parties.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    direction = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.Text)
    created_at = db.Column(db.Text, nullable=False, default=now_iso)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "book_id": self.book_id,
            "party_id": self.party_id,
            "amount": self.amount,
            "direction": self.direction,
            "description": self.description,
            "date": self.date,
            "due_date": self.due_date,
            "created_at": self.created_at,
        }


class Reminder(db.Model):
    """A payment reminder raised against a party. Nothing is actually sent by
    the default driver — see `app.services.messaging` — so `status` stays
    'pending' until the caller confirms the message was opened/sent."""

    __tablename__ = "reminders"
    __table_args__ = (
        db.CheckConstraint("channel IN ('whatsapp', 'sms', 'inapp')"),
        db.CheckConstraint("status IN ('pending', 'sent', 'failed')"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    party_id = db.Column(db.Integer, db.ForeignKey("parties.id"), nullable=False)
    channel = db.Column(db.Text, nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.Text, nullable=False, default="pending")
    sent_at = db.Column(db.Text)
    created_at = db.Column(db.Text, nullable=False, default=now_iso)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "book_id": self.book_id,
            "party_id": self.party_id,
            "channel": self.channel,
            "message": self.message,
            "status": self.status,
            "sent_at": self.sent_at,
            "created_at": self.created_at,
        }
