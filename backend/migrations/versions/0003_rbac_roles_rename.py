"""RBAC: rename roles to USER/ADMIN/SUPER_ADMIN, expand permissions, add
suspension, feature flags, and system settings

Revision ID: 0003_rbac_roles_rename
Revises: 0002_category_fk_roles_audit
Create Date: 2026-08-27 18:00:00.000000

"""
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa


revision = '0003_rbac_roles_rename'
down_revision = '0002_category_fk_roles_audit'
branch_labels = None
depends_on = None


# Permission grants per role — kept in sync with authz_service.PERMISSIONS.
_ALL_PERMISSIONS = [
    ("users.view", "View user accounts"),
    ("users.create", "Create user accounts"),
    ("users.update", "Edit user accounts"),
    ("users.suspend", "Suspend or reactivate user accounts"),
    ("users.delete", "Permanently delete user accounts"),
    ("transactions.view", "View any user's transactions"),
    ("transactions.update", "Edit any user's transactions"),
    ("transactions.delete", "Delete any user's transactions"),
    ("accounts.view", "View any user's accounts"),
    ("budgets.view", "View any user's budgets"),
    ("goals.view", "View any user's goals"),
    ("bills.view", "View any user's bills"),
    ("recurring.view", "View any user's recurring transactions"),
    ("categories.view", "View categories"),
    ("categories.create", "Create categories"),
    ("categories.update", "Edit categories"),
    ("categories.delete", "Delete categories"),
    ("analytics.view", "View platform analytics"),
    ("reports.view", "View platform reports"),
    ("notifications.manage", "Manage notifications"),
    ("audit_logs.view", "View audit logs"),
    ("admins.view", "View admin accounts"),
    ("admins.create", "Create admin accounts"),
    ("admins.update", "Edit admin accounts"),
    ("admins.disable", "Disable/activate admin accounts"),
    ("roles.view", "View roles"),
    ("roles.manage", "Manage role permissions"),
    ("permissions.view", "View permissions"),
    ("permissions.manage", "Manage permissions"),
    ("settings.view", "View system settings"),
    ("settings.manage", "Manage system settings"),
    ("feature_flags.view", "View feature flags"),
    ("feature_flags.manage", "Toggle feature flags"),
    ("system_health.view", "View system health"),
]

_ADMIN_PERMISSIONS = [
    "users.view", "users.update", "users.suspend",
    "transactions.view", "accounts.view", "budgets.view", "goals.view",
    "bills.view", "recurring.view",
    "categories.view", "categories.create", "categories.update", "categories.delete",
    "analytics.view", "reports.view", "notifications.manage", "audit_logs.view",
]

_FEATURE_FLAGS = [
    ("ai_assistant", "AI Assistant", "Finance copilot / suggested-question assistant"),
    ("net_worth", "Net Worth", "Assets - liabilities net worth tracking"),
    ("financial_health", "Financial Health", "Financial health score and recommendations"),
    ("smart_insights", "Smart Insights", "Automated spending/income insight generation"),
    ("receipt_scanner", "Receipt Scanner", "Scan/OCR receipts into transactions"),
    ("beta_reports", "Beta Reports", "Experimental report formats"),
]


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_suspended', sa.Boolean(), nullable=False, server_default=sa.false()))

    with op.batch_alter_table('activity_logs', schema=None) as batch_op:
        batch_op.alter_column('user_id', existing_type=sa.Integer(), nullable=True)

    op.create_table(
        'feature_flags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.Text(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.Column('updated_at', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key'),
    )
    op.create_table(
        'system_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.Text(), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key'),
    )

    conn = op.get_bind()
    now_value = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # --- Roles: rename, drop the old generic 'support' role, add USER ------
    conn.execute(sa.text("UPDATE roles SET name = 'SUPER_ADMIN' WHERE name = 'super_admin'"))
    conn.execute(sa.text("UPDATE roles SET name = 'ADMIN' WHERE name = 'admin'"))

    support_role = conn.execute(sa.text("SELECT id FROM roles WHERE name = 'support'")).first()
    if support_role:
        conn.execute(sa.text("DELETE FROM role_permissions WHERE role_id = :role_id"), {"role_id": support_role[0]})
        conn.execute(sa.text("DELETE FROM roles WHERE id = :role_id"), {"role_id": support_role[0]})

    conn.execute(
        sa.text("INSERT INTO roles (name, description) VALUES ('USER', 'Regular user managing their own data')")
    )

    role_ids = dict(conn.execute(sa.text("SELECT name, id FROM roles")).all())

    # --- Permissions: replace the old 7-key set with the full 33-key set --
    conn.execute(sa.text("DELETE FROM role_permissions"))
    conn.execute(sa.text("DELETE FROM permissions"))
    for key, description in _ALL_PERMISSIONS:
        conn.execute(
            sa.text("INSERT INTO permissions (key, description) VALUES (:key, :description)"),
            {"key": key, "description": description},
        )
    permission_ids = dict(conn.execute(sa.text("SELECT key, id FROM permissions")).all())

    def grant(role_name, keys):
        for key in keys:
            conn.execute(
                sa.text("INSERT INTO role_permissions (role_id, permission_id) VALUES (:role_id, :permission_id)"),
                {"role_id": role_ids[role_name], "permission_id": permission_ids[key]},
            )

    grant("SUPER_ADMIN", permission_ids.keys())
    grant("ADMIN", _ADMIN_PERMISSIONS)
    # USER gets none of these — the finance app's ownership checks govern
    # a regular user's access to their own data, not this table.

    # --- Backfill every existing user onto USER/SUPER_ADMIN -----------------
    conn.execute(sa.text("UPDATE users SET role_id = :role_id WHERE is_admin"), {"role_id": role_ids["SUPER_ADMIN"]})
    conn.execute(sa.text("UPDATE users SET role_id = :role_id WHERE role_id IS NULL"), {"role_id": role_ids["USER"]})

    # --- Seed feature flags (all off — the features themselves don't exist
    # in the codebase yet, so there is nothing real to enable) --------------
    for key, name, description in _FEATURE_FLAGS:
        conn.execute(
            sa.text(
                "INSERT INTO feature_flags (key, name, description, is_enabled, updated_at) "
                "VALUES (:key, :name, :description, FALSE, :now)"
            ),
            {"key": key, "name": name, "description": description, "now": now_value},
        )

    # --- Seed system settings -----------------------------------------------
    settings_seed = [
        ("app_name", "Expense Tracker"),
        ("default_currency", "USD"),
        ("maintenance_mode", "false"),
    ]
    for key, value in settings_seed:
        conn.execute(
            sa.text("INSERT INTO system_settings (key, value, updated_at) VALUES (:key, :value, :now)"),
            {"key": key, "value": value, "now": now_value},
        )


def downgrade():
    op.drop_table('system_settings')
    op.drop_table('feature_flags')

    with op.batch_alter_table('activity_logs', schema=None) as batch_op:
        batch_op.alter_column('user_id', existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_suspended')

    # Roles/permissions are left as USER/ADMIN/SUPER_ADMIN on downgrade —
    # reconstructing the old generic support/7-permission seed isn't
    # meaningful to reverse.
