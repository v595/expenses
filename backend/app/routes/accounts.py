from flask import Blueprint, g, jsonify, request

from app.routes.auth import login_required
from app.services import account_service

accounts_bp = Blueprint("accounts", __name__)


@accounts_bp.route("/api/accounts", methods=["GET"])
@login_required
def list_accounts():
    return jsonify(account_service.get_accounts(g.current_user["id"])), 200


@accounts_bp.route("/api/accounts", methods=["POST"])
@login_required
def create_account():
    try:
        account = account_service.create_account(g.current_user["id"], request.get_json(silent=True))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Account created", "account": account}), 201


@accounts_bp.route("/api/accounts/<int:account_id>", methods=["PUT"])
@login_required
def update_account(account_id):
    try:
        account = account_service.update_account(account_id, g.current_user["id"], request.get_json(silent=True))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Account updated", "account": account}), 200


@accounts_bp.route("/api/accounts/<int:account_id>", methods=["DELETE"])
@login_required
def delete_account(account_id):
    account_service.delete_account(account_id, g.current_user["id"])
    return jsonify({"message": "Account deleted"}), 200
