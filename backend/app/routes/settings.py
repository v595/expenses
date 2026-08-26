from flask import Blueprint, g, jsonify, request

from app.routes.auth import login_required
from app.services import settings_service

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/api/settings", methods=["PUT"])
@login_required
def update_settings():
    try:
        user = settings_service.update_settings(g.current_user, request.get_json(silent=True))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Settings updated", "user": user}), 200


@settings_bp.route("/api/settings/account", methods=["DELETE"])
@login_required
def delete_account():
    settings_service.delete_account(g.current_user["id"])
    return jsonify({"message": "Account deleted"}), 200
