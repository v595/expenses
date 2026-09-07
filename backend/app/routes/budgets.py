from flask import Blueprint, g, jsonify, request

from app.routes.auth import login_required
from app.services import budget_service
from app.services.errors import ServiceError

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


@budgets_bp.route("/api/budgets/shared-with-me", methods=["GET"])
@login_required
def shared_with_me():
    return jsonify(budget_service.get_budgets_shared_with_me(g.current_user["id"])), 200


@budgets_bp.route("/api/budgets/<category>", methods=["DELETE"])
@login_required
def delete_budget(category):
    budget_service.delete_budget(g.current_user["id"], category)
    return jsonify({"message": "Budget deleted"}), 200


@budgets_bp.route("/api/budgets/<category>/share", methods=["GET"])
@login_required
def list_shares(category):
    try:
        shares = budget_service.get_budget_shares(g.current_user["id"], category)
    except ServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    return jsonify(shares), 200


@budgets_bp.route("/api/budgets/<category>/share", methods=["POST"])
@login_required
def share_budget(category):
    try:
        result = budget_service.share_budget(g.current_user["id"], category, request.get_json(silent=True))
    except ServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Budget shared", **result}), 201


@budgets_bp.route("/api/budgets/<category>/share/<int:shared_with_user_id>", methods=["DELETE"])
@login_required
def unshare_budget(category, shared_with_user_id):
    try:
        budget_service.unshare_budget(g.current_user["id"], category, shared_with_user_id)
    except ServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    return jsonify({"message": "Budget unshared"}), 200
