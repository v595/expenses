"""khatabook: books (workspaces), parties, ledger entries and reminders, and
scope transactions to a book

Revision ID: 0004_books_parties_ledger
Revises: 0003_rbac_roles_rename
Create Date: 2026-09-05 17:45:00.000000

"""
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa


revision = '0004_books_parties_ledger'
down_revision = '0003_rbac_roles_rename'
branch_labels = None
depends_on = None


DEFAULT_BOOK_NAME = "My Book"
DEFAULT_BOOK_TYPE = "personal"


def upgrade():
    op.create_table(
        'books',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('type', sa.Text(), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('color', sa.Text(), nullable=True),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.CheckConstraint("type IN ('business', 'personal', 'home', 'daily')"),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name'),
    )
    op.create_table(
        'parties',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('phone', sa.Text(), nullable=True),
        sa.Column('type', sa.Text(), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.CheckConstraint("type IN ('customer', 'supplier')"),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('book_id', 'name', 'type'),
    )
    op.create_table(
        'ledger_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.Column('party_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('direction', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('date', sa.Text(), nullable=False),
        sa.Column('due_date', sa.Text(), nullable=True),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.CheckConstraint("amount > 0"),
        sa.CheckConstraint("direction IN ('given', 'got')"),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ),
        sa.ForeignKeyConstraint(['party_id'], ['parties.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'reminders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.Column('party_id', sa.Integer(), nullable=False),
        sa.Column('channel', sa.Text(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False, server_default='pending'),
        sa.Column('sent_at', sa.Text(), nullable=True),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.CheckConstraint("channel IN ('whatsapp', 'sms', 'inapp')"),
        sa.CheckConstraint("status IN ('pending', 'sent', 'failed')"),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ),
        sa.ForeignKeyConstraint(['party_id'], ['parties.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('book_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_transactions_book_id_books', 'books', ['book_id'], ['id'])

    _seed_default_books_and_backfill_transactions()


def _seed_default_books_and_backfill_transactions():
    """Every existing user gets the default book they'd otherwise only get on
    their next login, and each of their transactions is pointed at it. The
    column stays nullable — this is a convenience backfill, not a constraint."""
    conn = op.get_bind()
    now_value = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    user_ids = [row[0] for row in conn.execute(sa.text("SELECT id FROM users ORDER BY id")).all()]

    for user_id in user_ids:
        book_id = conn.execute(
            sa.text(
                "INSERT INTO books (user_id, name, type, is_default, color, created_at) "
                "VALUES (:user_id, :name, :type, TRUE, NULL, :now) RETURNING id"
            ),
            {
                "user_id": user_id,
                "name": DEFAULT_BOOK_NAME,
                "type": DEFAULT_BOOK_TYPE,
                "now": now_value,
            },
        ).scalar()

        conn.execute(
            sa.text("UPDATE transactions SET book_id = :book_id WHERE user_id = :user_id"),
            {"book_id": book_id, "user_id": user_id},
        )


def downgrade():
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.drop_constraint('fk_transactions_book_id_books', type_='foreignkey')
        batch_op.drop_column('book_id')

    op.drop_table('reminders')
    op.drop_table('ledger_entries')
    op.drop_table('parties')
    op.drop_table('books')
