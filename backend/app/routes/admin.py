from flask import Blueprint, g, jsonify, request

from app.routes.auth import admin_required, require_permission
from app.services import admin_service

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/api/admin/stats", methods=["GET"])
@admin_required
def stats():
    return jsonify(admin_service.get_stats()), 200


@admin_bp.route("/api/admin/users", methods=["GET"])
@admin_required
def list_users():
    return jsonify(admin_service.list_users()), 200


@admin_bp.route("/api/admin/users/<int:user_id>/transactions", methods=["GET"])
@admin_required
def user_transactions(user_id):
    if admin_service.get_user(user_id) is None:
        return jsonify({"error": "User not found"}), 404
    return jsonify(admin_service.get_user_transactions(user_id)), 200


@admin_bp.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    try:
        admin_service.delete_user(user_id, g.current_user["id"])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "User deleted"}), 200


@admin_bp.route("/api/admin/users/<int:user_id>/suspend", methods=["POST"])
@require_permission("users.suspend")
def suspend_user(user_id):
    try:
        user = admin_service.suspend_user(user_id, g.current_user)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "User suspended", "user": user}), 200


@admin_bp.route("/api/admin/users/<int:user_id>/activate", methods=["POST"])
@require_permission("users.suspend")
def activate_user(user_id):
    try:
        user = admin_service.activate_user(user_id, g.current_user)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "User activated", "user": user}), 200


@admin_bp.route("/api/admin/audit-logs", methods=["GET"])
@require_permission("audit_logs.view")
def audit_logs():
    limit = min(int(request.args.get("limit", 100)), 500)
    offset = max(int(request.args.get("offset", 0)), 0)
    admin_only = request.args.get("admin_only") == "true"
    return jsonify(admin_service.get_audit_log(limit=limit, offset=offset, admin_actions_only=admin_only)), 200


@admin_bp.route("/api/admin/security-events", methods=["GET"])
@require_permission("audit_logs.view")
def security_events():
    limit = min(int(request.args.get("limit", 100)), 500)
    offset = max(int(request.args.get("offset", 0)), 0)
    return jsonify(admin_service.get_security_events(limit=limit, offset=offset)), 200
