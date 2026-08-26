from flask import Blueprint, g, jsonify

from app.routes.auth import login_required
from app.services import dashboard_service, recurring_service

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/api/dashboard/summary", methods=["GET"])
@login_required
def summary():
    recurring_service.materialize_due(g.current_user["id"])
    return jsonify(dashboard_service.get_summary(g.current_user["id"])), 200


@dashboard_bp.route("/api/dashboard/monthly", methods=["GET"])
@login_required
def monthly():
    return jsonify(dashboard_service.get_monthly(g.current_user["id"])), 200


@dashboard_bp.route("/api/dashboard/insights", methods=["GET"])
@login_required
def insights():
    return jsonify(dashboard_service.get_insights(g.current_user["id"])), 200
