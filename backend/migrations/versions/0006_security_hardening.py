"""security hardening: token expiry, login lockout, TOTP 2FA

Revision ID: 0006_security_hardening
Revises: 0005_bill_type
Create Date: 2026-09-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '0006_security_hardening'
down_revision = '0005_bill_type'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users') as batch_op:
        # Sliding-window expiry for the opaque bearer token: every
        # authenticated request pushes this forward, so active sessions never
        # drop but an idle/leaked token stops working after TOKEN_TTL.
        batch_op.add_column(sa.Column('token_expires_at', sa.Text(), nullable=True))
        # Brute-force protection: consecutive bad passwords, and the lockout
        # window that starts once the threshold is hit.
        batch_op.add_column(
            sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0')
        )
        batch_op.add_column(sa.Column('locked_until', sa.Text(), nullable=True))
        # TOTP-based 2FA. totp_secret stays set (but unused) if the user later
        # disables 2FA, so re-enabling doesn't require a fresh QR scan unless
        # they explicitly reset it.
        batch_op.add_column(sa.Column('totp_secret', sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column('totp_enabled', sa.Boolean(), nullable=False, server_default=sa.false())
        )


def downgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('totp_enabled')
        batch_op.drop_column('totp_secret')
        batch_op.drop_column('locked_until')
        batch_op.drop_column('failed_login_attempts')
        batch_op.drop_column('token_expires_at')
