from app.services import authz_service


def test_permission_groups_cover_every_permission_exactly_once():
    """Guards against PERMISSIONS growing a key that PERMISSION_GROUPS forgets
    to place — that key would silently vanish from the Roles & Permissions
    editor instead of erroring."""
    grouped_keys = [key for _label, keys in authz_service.PERMISSION_GROUPS for key in keys]
    assert sorted(grouped_keys) == sorted(authz_service.PERMISSIONS)
    assert len(grouped_keys) == len(set(grouped_keys)), "a permission key appears in more than one group"


def test_grouped_permissions_flags_super_admin_only():
    groups = authz_service.grouped_permissions()
    flagged = {p["key"] for group in groups for p in group["permissions"] if p["super_admin_only"]}
    assert flagged == authz_service.SUPER_ADMIN_ONLY
