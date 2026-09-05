from flask import Blueprint, g, jsonify, request

from app.routes.auth import login_required
from app.services import party_report_service
from app.services.errors import ServiceError

party_reports_bp = Blueprint("party_reports", __name__)


@party_reports_bp.route("/api/reports/parties/summary", methods=["GET"])
@login_required
def parties_summary():
    book_id = request.args.get("book_id")
    try:
        summary = party_report_service.get_summary(
            g.current_user["id"],
            book_id=int(book_id) if book_id else None,
            start_date=request.args.get("start_date"),
            end_date=request.args.get("end_date"),
        )
    except ServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(summary), 200


@party_reports_bp.route("/api/reports/parties/<int:party_id>/statement", methods=["GET"])
@login_required
def party_statement(party_id):
    try:
        statement = party_report_service.get_statement(
            party_id,
            g.current_user["id"],
            start_date=request.args.get("start_date"),
            end_date=request.args.get("end_date"),
        )
    except ServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(statement), 200
