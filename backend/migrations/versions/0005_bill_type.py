"""add bill_type to bills so each bill can carry a category icon

Revision ID: 0005_bill_type
Revises: 0004_books_parties_ledger
Create Date: 2026-09-05 18:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '0005_bill_type'
down_revision = '0004_books_parties_ledger'
branch_labels = None
depends_on = None


def upgrade():
    # Nullable on purpose: bills that predate this column keep working and
    # simply render the generic "Other" icon until they're edited.
    with op.batch_alter_table('bills') as batch_op:
        batch_op.add_column(sa.Column('bill_type', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('bills') as batch_op:
        batch_op.drop_column('bill_type')
