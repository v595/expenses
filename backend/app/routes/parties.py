from flask import Blueprint, g, jsonify, request

from app.routes.auth import login_required
from app.services import party_service
from app.services.errors import ServiceError

parties_bp = Blueprint("parties", __name__)


def _int_arg(name):
    value = request.args.get(name)
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"{name} must be a number")


@parties_bp.route("/api/parties", methods=["GET"])
@login_required
def list_parties():
    try:
        parties = party_service.get_parties(
            g.current_user["id"], book_id=_int_arg("book_id"), type_=request.args.get("type")
        )
    except ServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(parties), 200


@parties_bp.route("/api/parties/<int:party_id>", methods=["GET"])
@login_required
def get_party(party_id):
    try:
        party = party_service.get_party(party_id, g.current_user["id"])
    except ServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    return jsonify(party), 200


@parties_bp.route("/api/parties", methods=["POST"])
@login_required
def create_party():
    try:
        party = party_service.create_party(g.current_user["id"], request.get_json(silent=True))
    except ServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Party created", "party": party}), 201


@parties_bp.route("/api/parties/<int:party_id>", methods=["PUT"])
@login_required
def update_party(party_id):
    try:
        party = party_service.update_party(party_id, g.current_user["id"], request.get_json(silent=True))
    except ServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Party updated", "party": party}), 200


@parties_bp.route("/api/parties/<int:party_id>", methods=["DELETE"])
@login_required
def delete_party(party_id):
    try:
        party_service.delete_party(party_id, g.current_user["id"])
    except ServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    return jsonify({"message": "Party deleted"}), 200
