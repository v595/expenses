from flask import Blueprint, g, jsonify, request

from app.routes.auth import login_required
from app.services import activity_service

activity_bp = Blueprint("activity", __name__)


@activity_bp.route("/api/activity/pageview", methods=["POST"])
@login_required
def log_pageview():
    data = request.get_json(silent=True) or {}
    try:
        activity_service.log_pageview(g.current_user["id"], data.get("path"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Logged"}), 200
