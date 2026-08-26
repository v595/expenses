from flask import Blueprint, g, jsonify, request

from app.routes.auth import login_required
from app.services import recurring_service, transaction_service

transactions_bp = Blueprint("transactions", __name__)


@transactions_bp.route("/api/transactions", methods=["GET"])
@login_required
def list_transactions():
    recurring_service.materialize_due(g.current_user["id"])
    try:
        tag_id = request.args.get("tag_id")
        transactions = transaction_service.get_transactions(
            g.current_user["id"],
            category=request.args.get("category"),
            type_=request.args.get("type"),
            start_date=request.args.get("start_date"),
            end_date=request.args.get("end_date"),
            search=request.args.get("search"),
            tag_id=int(tag_id) if tag_id else None,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(transactions), 200


@transactions_bp.route("/api/transactions/<int:transaction_id>", methods=["GET"])
@login_required
def get_transaction(transaction_id):
    transaction = transaction_service.get_transaction(transaction_id, g.current_user["id"])
    if transaction is None:
        return jsonify({"error": "Transaction not found"}), 404
    return jsonify(transaction), 200


@transactions_bp.route("/api/transactions", methods=["POST"])
@login_required
def create_transaction():
    data = request.get_json(silent=True)
    try:
        transaction = transaction_service.create_transaction(data, g.current_user["id"])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Transaction created successfully", "transaction": transaction}), 201


@transactions_bp.route("/api/transactions/<int:transaction_id>", methods=["PUT"])
@login_required
def update_transaction(transaction_id):
    try:
        transaction = transaction_service.update_transaction(transaction_id, data=request.get_json(silent=True), user_id=g.current_user["id"])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    if transaction is None:
        return jsonify({"error": "Transaction not found"}), 404
    return jsonify({"message": "Transaction updated successfully", "transaction": transaction}), 200


@transactions_bp.route("/api/transactions/<int:transaction_id>", methods=["DELETE"])
@login_required
def delete_transaction(transaction_id):
    deleted = transaction_service.delete_transaction(transaction_id, g.current_user["id"])
    if not deleted:
        return jsonify({"error": "Transaction not found"}), 404
    return jsonify({"message": "Transaction deleted successfully"}), 200


@transactions_bp.route("/api/transactions/import", methods=["POST"])
@login_required
def import_transactions():
    data = request.get_json(silent=True) or {}
    try:
        result = transaction_service.bulk_import(g.current_user["id"], data.get("rows"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(result), 200
