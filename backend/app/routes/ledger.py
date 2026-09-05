from flask import Blueprint, g, jsonify, request

from app.routes.auth import login_required
from app.services import ledger_service
from app.services.errors import ServiceError

ledger_bp = Blueprint("ledger", __name__)


@ledger_bp.route("/api/ledger", methods=["GET"])
@login_required
def list_entries():
    party_id = request.args.get("party_id")
    if not party_id:
        return jsonify({"error": "party_id is required"}), 400
    try:
        entries = ledger_service.get_entries(
            int(party_id),
            g.current_user["id"],
            start_date=request.args.get("start_date"),
            end_date=request.args.get("end_date"),
        )
    except ServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(entries), 200


@ledger_bp.route("/api/ledger", methods=["POST"])
@login_required
def create_entry():
    try:
        entry = ledger_service.create_entry(g.current_user["id"], request.get_json(silent=True))
    except ServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Ledger entry created", "entry": entry}), 201


@ledger_bp.route("/api/ledger/<int:entry_id>", methods=["PUT"])
@login_required
def update_entry(entry_id):
    try:
        entry = ledger_service.update_entry(entry_id, g.current_user["id"], request.get_json(silent=True))
    except ServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Ledger entry updated", "entry": entry}), 200


@ledger_bp.route("/api/ledger/<int:entry_id>", methods=["DELETE"])
@login_required
def delete_entry(entry_id):
    try:
        ledger_service.delete_entry(entry_id, g.current_user["id"])
    except ServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    return jsonify({"message": "Ledger entry deleted"}), 200
