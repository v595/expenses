from flask import Blueprint, g, jsonify, request

from app.routes.auth import login_required
from app.services import reminder_service
from app.services.errors import ServiceError
from app.services.messaging import MessagingError

reminders_bp = Blueprint("reminders", __name__)


def _int_arg(name):
    value = request.args.get(name)
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"{name} must be a number")


@reminders_bp.route("/api/reminders/pending", methods=["GET"])
@login_required
def pending_dues():
    try:
        dues = reminder_service.get_pending_dues(
            g.current_user["id"],
            book_id=_int_arg("book_id"),
            overdue_only=request.args.get("overdue_only") == "true",
        )
    except ServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(dues), 200


@reminders_bp.route("/api/reminders", methods=["GET"])
@login_required
def list_reminders():
    try:
        history = reminder_service.get_history(
            g.current_user["id"], book_id=_int_arg("book_id"), party_id=_int_arg("party_id")
        )
    except ServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(history), 200


@reminders_bp.route("/api/reminders", methods=["POST"])
@login_required
def create_reminder():
    try:
        reminder = reminder_service.create_reminder(g.current_user["id"], request.get_json(silent=True))
    except MessagingError as e:
        # The driver couldn't prepare the message (e.g. Twilio isn't
        # configured) — surface its actionable text as-is.
        return jsonify({"error": e.message}), e.status_code
    except ServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Reminder created", "reminder": reminder}), 201


@reminders_bp.route("/api/reminders/<int:reminder_id>/sent", methods=["POST"])
@login_required
def mark_sent(reminder_id):
    try:
        reminder = reminder_service.mark_sent(reminder_id, g.current_user["id"])
    except ServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    return jsonify({"message": "Reminder marked sent", "reminder": reminder}), 200
