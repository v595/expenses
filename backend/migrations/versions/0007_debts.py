"""add debts table for payoff planning (snowball/avalanche)

Revision ID: 0007_debts
Revises: 0006_security_hardening
Create Date: 2026-09-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '0007_debts'
down_revision = '0006_security_hardening'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'debts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('balance', sa.Float(), nullable=False),
        sa.Column('interest_rate', sa.Float(), nullable=False, server_default='0'),
        sa.Column('min_payment', sa.Float(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.Text(), nullable=False),
    )


def downgrade():
    op.drop_table('debts')
