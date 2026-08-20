from flask import Blueprint, g, jsonify, request

from app.routes.auth import login_required
from app.services import recurring_service

recurring_bp = Blueprint("recurring", __name__)


@recurring_bp.route("/api/recurring", methods=["GET"])
@login_required
def list_recurring():
    return jsonify(recurring_service.get_recurring(g.current_user["id"])), 200


@recurring_bp.route("/api/recurring", methods=["POST"])
@login_required
def create_recurring():
    try:
        rule = recurring_service.create_recurring(request.get_json(silent=True), g.current_user["id"])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Recurring transaction created", "recurring": rule}), 201


@recurring_bp.route("/api/recurring/<int:recurring_id>", methods=["DELETE"])
@login_required
def delete_recurring(recurring_id):
    recurring_service.delete_recurring(recurring_id, g.current_user["id"])
    return jsonify({"message": "Recurring transaction deleted"}), 200
