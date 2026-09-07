from flask import Blueprint, jsonify

from app.routes.auth import login_required
from app.services import feature_flag_service

feature_flags_bp = Blueprint("feature_flags", __name__)


@feature_flags_bp.route("/api/feature-flags", methods=["GET"])
@login_required
def list_feature_flags():
    """Every flag's on/off state, for the frontend to gate UI on — the
    server-side enforcement (e.g. net worth returning 404 when its flag is
    off) is what actually matters; this just lets the UI match reality
    instead of showing a button that 404s when clicked."""
    flags = feature_flag_service.list_flags()
    return jsonify({flag["key"]: flag["is_enabled"] for flag in flags}), 200
