from flask import Blueprint, g, jsonify

from app.routes.auth import login_required
from app.services import tag_service

tags_bp = Blueprint("tags", __name__)


@tags_bp.route("/api/tags", methods=["GET"])
@login_required
def list_tags():
    return jsonify(tag_service.get_tags(g.current_user["id"])), 200


@tags_bp.route("/api/tags/<int:tag_id>", methods=["DELETE"])
@login_required
def delete_tag(tag_id):
    tag_service.delete_tag(tag_id, g.current_user["id"])
    return jsonify({"message": "Tag deleted"}), 200
