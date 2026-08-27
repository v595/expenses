from flask import Blueprint, g, jsonify, request

from app.models import role as role_model
from app.routes.auth import require_permission
from app.services import admin_service, authz_service, feature_flag_service, system_settings_service

super_admin_bp = Blueprint("super_admin", __name__)


@super_admin_bp.route("/api/super-admin/admins", methods=["GET"])
@require_permission("admins.view")
def list_admins():
    return jsonify(admin_service.list_admins()), 200


@super_admin_bp.route("/api/super-admin/admins", methods=["POST"])
@require_permission("admins.create")
def create_admin():
    data = request.get_json(silent=True) or {}
    try:
        user = admin_service.create_admin_user(
            data.get("name"), data.get("email"), data.get("password"), data.get("role"), g.current_user
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Admin account created", "user": user}), 201


@super_admin_bp.route("/api/super-admin/admins/<int:user_id>/disable", methods=["POST"])
@require_permission("admins.disable")
def disable_admin(user_id):
    try:
        user = admin_service.disable_admin(user_id, g.current_user)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Admin disabled", "user": user}), 200


@super_admin_bp.route("/api/super-admin/admins/<int:user_id>/activate", methods=["POST"])
@require_permission("admins.disable")
def activate_admin(user_id):
    try:
        user = admin_service.activate_admin(user_id, g.current_user)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Admin activated", "user": user}), 200


@super_admin_bp.route("/api/super-admin/roles", methods=["GET"])
@require_permission("roles.view")
def list_roles():
    return jsonify(role_model.list_roles_with_counts()), 200


@super_admin_bp.route("/api/super-admin/roles/<int:role_id>", methods=["PUT"])
@require_permission("roles.manage")
def update_role(role_id):
    data = request.get_json(silent=True) or {}
    permission_keys = data.get("permissions")
    if not isinstance(permission_keys, list) or not all(isinstance(k, str) for k in permission_keys):
        return jsonify({"error": "permissions must be a list of permission keys"}), 400

    role = role_model.set_role_permissions(role_id, permission_keys)
    if role is None:
        return jsonify({"error": "Role not found"}), 404
    return jsonify({"message": "Role updated", "role": role}), 200


@super_admin_bp.route("/api/super-admin/permissions", methods=["GET"])
@require_permission("permissions.view")
def list_permissions():
    return jsonify(authz_service.PERMISSIONS), 200


@super_admin_bp.route("/api/super-admin/feature-flags", methods=["GET"])
@require_permission("feature_flags.view")
def list_feature_flags():
    return jsonify(feature_flag_service.list_flags()), 200


@super_admin_bp.route("/api/super-admin/feature-flags/<key>", methods=["PUT"])
@require_permission("feature_flags.manage")
def update_feature_flag(key):
    data = request.get_json(silent=True) or {}
    try:
        flag = feature_flag_service.set_enabled(key, data.get("enabled"), g.current_user["id"])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Feature flag updated", "flag": flag}), 200


@super_admin_bp.route("/api/super-admin/system-settings", methods=["GET"])
@require_permission("settings.view")
def get_system_settings():
    return jsonify(system_settings_service.get_all()), 200


@super_admin_bp.route("/api/super-admin/system-settings", methods=["PUT"])
@require_permission("settings.manage")
def update_system_settings():
    data = request.get_json(silent=True) or {}
    try:
        settings = system_settings_service.update_settings(data, g.current_user["id"])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Settings updated", "settings": settings}), 200


@super_admin_bp.route("/api/super-admin/system-health", methods=["GET"])
@require_permission("system_health.view")
def system_health():
    return jsonify(admin_service.get_system_health()), 200
