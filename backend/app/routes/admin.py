from flask import Blueprint, g, jsonify

from app.routes.auth import admin_required
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
