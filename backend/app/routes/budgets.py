from flask import Blueprint, g, jsonify, request

from app.routes.auth import login_required
from app.services import budget_service

budgets_bp = Blueprint("budgets", __name__)


@budgets_bp.route("/api/budgets", methods=["GET"])
@login_required
def list_budgets():
    return jsonify(budget_service.get_budgets_with_spending(g.current_user["id"])), 200


@budgets_bp.route("/api/budgets", methods=["POST"])
@login_required
def set_budget():
    try:
        budget_service.set_budget(g.current_user["id"], request.get_json(silent=True))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Budget saved"}), 200


@budgets_bp.route("/api/budgets/<category>", methods=["DELETE"])
@login_required
def delete_budget(category):
    budget_service.delete_budget(g.current_user["id"], category)
    return jsonify({"message": "Budget deleted"}), 200
