"""flip net_worth and receipt_scanner flags on now that those features
actually exist and are wired to them — every other flag stays off since
nothing behind them is built yet.

Revision ID: 0009_enable_shipped_flags
Revises: 0008_budget_shares
Create Date: 2026-09-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '0009_enable_shipped_flags'
down_revision = '0008_budget_shares'
branch_labels = None
depends_on = None

_SHIPPED_FLAGS = ("net_worth", "receipt_scanner")


def upgrade():
    conn = op.get_bind()
    for key in _SHIPPED_FLAGS:
        conn.execute(
            sa.text("UPDATE feature_flags SET is_enabled = TRUE WHERE key = :key"), {"key": key}
        )


def downgrade():
    conn = op.get_bind()
    for key in _SHIPPED_FLAGS:
        conn.execute(
            sa.text("UPDATE feature_flags SET is_enabled = FALSE WHERE key = :key"), {"key": key}
        )
