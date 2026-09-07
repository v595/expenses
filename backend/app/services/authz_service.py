"""Role-based access control for the admin surface (both the JSON
/api/admin|super-admin routes and the server-rendered /admin dashboard).

This governs ADMIN/SUPER_ADMIN capabilities only. A regular USER's access to
their own financial data is unaffected and continues to be enforced by the
existing per-resource ownership checks (e.g. transaction_service.get_transaction
scoping every query to `user_id`) — this module has no bearing on that."""

from app.models import role as role_model

# Keep in sync with the permission keys seeded in
# backend/migrations/versions/0003_rbac_roles_rename_*.py.
PERMISSIONS = (
    "users.view",
    "users.create",
    "users.update",
    "users.suspend",
    "users.delete",
    "transactions.view",
    "transactions.update",
    "transactions.delete",
    "accounts.view",
    "budgets.view",
    "goals.view",
    "bills.view",
    "recurring.view",
    "categories.view",
    "categories.create",
    "categories.update",
    "categories.delete",
    "analytics.view",
    "reports.view",
    "notifications.manage",
    "audit_logs.view",
    "admins.view",
    "admins.create",
    "admins.update",
    "admins.disable",
    "roles.view",
    "roles.manage",
    "permissions.view",
    "permissions.manage",
    "settings.view",
    "settings.manage",
    "feature_flags.view",
    "feature_flags.manage",
    "system_health.view",
)

# Permissions gated behind this hard role check even if somehow granted to a
# role via the permissions editor — privilege escalation must not be
# possible purely by editing role_permissions. Only SUPER_ADMIN may ever
# reach these, full stop.
SUPER_ADMIN_ONLY = {
    "admins.view",
    "admins.create",
    "admins.update",
    "admins.disable",
    "roles.view",
    "roles.manage",
    "permissions.view",
    "permissions.manage",
    "settings.view",
    "settings.manage",
    "feature_flags.view",
    "feature_flags.manage",
    "system_health.view",
}

# How the Roles & Permissions editor groups the flat PERMISSIONS tuple into
# scannable sections, mirroring the admin sidebar's own section labels.
# Every key in PERMISSIONS must appear in exactly one group here — a mismatch
# would silently drop a permission from the editor.
PERMISSION_GROUPS = (
    (
        "User data",
        (
            "users.view", "users.create", "users.update", "users.suspend", "users.delete",
            "transactions.view", "transactions.update", "transactions.delete",
            "accounts.view", "budgets.view", "goals.view", "bills.view", "recurring.view",
            "categories.view", "categories.create", "categories.update", "categories.delete",
            "analytics.view", "reports.view", "notifications.manage",
        ),
    ),
    ("Security", ("audit_logs.view",)),
    ("Administration", ("admins.view", "admins.create", "admins.update", "admins.disable", "roles.view", "roles.manage")),
    (
        "System",
        (
            "permissions.view", "permissions.manage", "settings.view", "settings.manage",
            "feature_flags.view", "feature_flags.manage", "system_health.view",
        ),
    ),
)


def grouped_permissions():
    """PERMISSIONS bucketed into PERMISSION_GROUPS, each key annotated with
    whether it's SUPER_ADMIN_ONLY — what the Roles & Permissions template
    renders instead of one flat 30-checkbox grid."""
    return [
        {
            "label": label,
            "permissions": [{"key": key, "super_admin_only": key in SUPER_ADMIN_ONLY} for key in keys],
        }
        for label, keys in PERMISSION_GROUPS
    ]


def role_name(user):
    role_id = user.get("role_id") if user else None
    if role_id is None:
        return None
    role = role_model.get_role_by_id(role_id)
    return role["name"] if role else None


def is_super_admin(user):
    return role_name(user) == "SUPER_ADMIN"


def is_admin_or_super(user):
    return bool(user and user.get("is_admin"))


def has_permission(user, permission_key):
    if not user:
        return False
    if permission_key in SUPER_ADMIN_ONLY and not is_super_admin(user):
        return False
    return role_model.role_has_permission(user.get("role_id"), permission_key)


def get_permissions(user):
    if not user:
        return []
    return [key for key in role_model.list_permission_keys(user.get("role_id")) if has_permission(user, key)]
