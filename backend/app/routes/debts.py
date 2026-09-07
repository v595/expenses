from flask import Blueprint, g, jsonify, request

from app.routes.auth import login_required
from app.services import debt_service

debts_bp = Blueprint("debts", __name__)


@debts_bp.route("/api/debts", methods=["GET"])
@login_required
def list_debts():
    return jsonify(debt_service.get_debts(g.current_user["id"])), 200


@debts_bp.route("/api/debts", methods=["POST"])
@login_required
def create_debt():
    try:
        debt = debt_service.create_debt(g.current_user["id"], request.get_json(silent=True))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Debt added", "debt": debt}), 201


@debts_bp.route("/api/debts/<int:debt_id>", methods=["PUT"])
@login_required
def update_debt(debt_id):
    try:
        debt = debt_service.update_debt(debt_id, g.current_user["id"], request.get_json(silent=True))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Debt updated", "debt": debt}), 200


@debts_bp.route("/api/debts/<int:debt_id>", methods=["DELETE"])
@login_required
def delete_debt(debt_id):
    debt_service.delete_debt(debt_id, g.current_user["id"])
    return jsonify({"message": "Debt deleted"}), 200


@debts_bp.route("/api/debts/payoff-plan", methods=["POST"])
@login_required
def payoff_plan():
    data = request.get_json(silent=True) or {}
    extra_payment = data.get("extra_payment", 0)
    strategy = data.get("strategy", "avalanche")

    if not isinstance(extra_payment, (int, float)) or isinstance(extra_payment, bool) or extra_payment < 0:
        return jsonify({"error": "Extra payment must be a non-negative number"}), 400
    if strategy not in ("avalanche", "snowball"):
        return jsonify({"error": "Strategy must be 'avalanche' or 'snowball'"}), 400

    debts = debt_service.get_debts(g.current_user["id"])
    plan = debt_service.build_payoff_plan(debts, float(extra_payment), strategy)
    return jsonify({**plan, "strategy": strategy, "extra_payment": float(extra_payment)}), 200
