from flask import Blueprint, g, jsonify, request

from app.routes.auth import login_required
from app.services import cashbook_service
from app.services.errors import ServiceError

cashbook_bp = Blueprint("cashbook", __name__)


@cashbook_bp.route("/api/cashbook", methods=["GET"])
@login_required
def get_cashbook():
    book_id = request.args.get("book_id")
    try:
        cashbook = cashbook_service.get_cashbook(
            g.current_user["id"],
            book_id=int(book_id) if book_id else None,
            start_date=request.args.get("start_date"),
            end_date=request.args.get("end_date"),
        )
    except ServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(cashbook), 200
