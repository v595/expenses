from flask import Blueprint, g, jsonify, request

from app.routes.auth import login_required
from app.services import bill_service

bills_bp = Blueprint("bills", __name__)


@bills_bp.route("/api/bills", methods=["GET"])
@login_required
def list_bills():
    return jsonify(bill_service.get_bills(g.current_user["id"])), 200


@bills_bp.route("/api/bills", methods=["POST"])
@login_required
def create_bill():
    try:
        bill = bill_service.create_bill(g.current_user["id"], request.get_json(silent=True))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Bill created", "bill": bill}), 201


@bills_bp.route("/api/bills/<int:bill_id>/pay", methods=["POST"])
@login_required
def pay_bill(bill_id):
    try:
        bill = bill_service.pay_bill(bill_id, g.current_user["id"])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Bill marked as paid", "bill": bill}), 200


@bills_bp.route("/api/bills/<int:bill_id>", methods=["DELETE"])
@login_required
def delete_bill(bill_id):
    bill_service.delete_bill(bill_id, g.current_user["id"])
    return jsonify({"message": "Bill deleted"}), 200
