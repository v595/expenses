from flask import Blueprint, g, jsonify

from app.routes.auth import login_required
from app.services import notification_service

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("/api/notifications", methods=["GET"])
@login_required
def list_notifications():
    return jsonify(notification_service.get_notifications(g.current_user)), 200


@notifications_bp.route("/api/notifications/unread-count", methods=["GET"])
@login_required
def unread_count():
    return jsonify({"count": notification_service.get_unread_count(g.current_user)}), 200


@notifications_bp.route("/api/notifications/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_read(notification_id):
    notification_service.mark_read(notification_id, g.current_user["id"])
    return jsonify({"message": "Marked as read"}), 200


@notifications_bp.route("/api/notifications/read-all", methods=["POST"])
@login_required
def mark_all_read():
    notification_service.mark_all_read(g.current_user["id"])
    return jsonify({"message": "All notifications marked as read"}), 200


@notifications_bp.route("/api/notifications/<int:notification_id>", methods=["DELETE"])
@login_required
def delete_notification(notification_id):
    notification_service.delete_notification(notification_id, g.current_user["id"])
    return jsonify({"message": "Notification deleted"}), 200
