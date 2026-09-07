"""add budget_shares for read-only shared/family budgets

Revision ID: 0008_budget_shares
Revises: 0007_debts
Create Date: 2026-09-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '0008_budget_shares'
down_revision = '0007_debts'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'budget_shares',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('budget_id', sa.Integer(), sa.ForeignKey('budgets.id'), nullable=False),
        sa.Column('owner_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('shared_with_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.Text(), nullable=False),
        sa.UniqueConstraint('budget_id', 'shared_with_user_id'),
    )


def downgrade():
    op.drop_table('budget_shares')
