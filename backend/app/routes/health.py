from flask import Blueprint, jsonify

from app.services.health_service import get_health_status

health_bp = Blueprint("health", __name__)


@health_bp.route("/")
def index():
    return jsonify(
        {
            "message": "Expense Tracker API",
            "health": "/api/health",
            "docs": "See README.md for the full API reference",
        }
    )


@health_bp.route("/api/health")
def health():
    return jsonify(get_health_status())
