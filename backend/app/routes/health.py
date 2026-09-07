from flask import Blueprint, jsonify

from app.services import system_settings_service
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


@health_bp.route("/api/app-info")
def app_info():
    """Public (no login) so the login/register screens — which render before
    any auth — can also show the configured app name, not just pages behind
    a session."""
    settings = system_settings_service.get_all()
    return jsonify({"app_name": settings.get("app_name") or "Hisaab"})
