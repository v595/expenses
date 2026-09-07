"""fix stale "Expense Tracker" app_name setting — the app was rebranded to
Hisaab, but the seeded system_settings row was never updated, so System
Settings silently showed the pre-rebrand name to every admin.

Revision ID: 0010_fix_app_name_default
Revises: 0009_enable_shipped_flags
Create Date: 2026-09-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '0010_fix_app_name_default'
down_revision = '0009_enable_shipped_flags'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    # Only touch it if it's still the untouched default — an admin who
    # already deliberately renamed it (to anything, including back to
    # "Expense Tracker") should not have that choice silently reverted.
    conn.execute(
        sa.text("UPDATE system_settings SET value = 'Hisaab' WHERE key = 'app_name' AND value = 'Expense Tracker'")
    )


def downgrade():
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE system_settings SET value = 'Expense Tracker' WHERE key = 'app_name' AND value = 'Hisaab'")
    )
