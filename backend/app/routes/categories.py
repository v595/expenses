from flask import Blueprint, g, jsonify, request

from app.routes.auth import login_required
from app.services import category_service

categories_bp = Blueprint("categories", __name__)


@categories_bp.route("/api/categories", methods=["GET"])
@login_required
def list_categories():
    return jsonify(category_service.get_categories(g.current_user["id"])), 200


@categories_bp.route("/api/categories", methods=["POST"])
@login_required
def create_category():
    try:
        category = category_service.create_category(g.current_user["id"], request.get_json(silent=True))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Category created", "category": category}), 201


@categories_bp.route("/api/categories/<int:category_id>", methods=["DELETE"])
@login_required
def delete_category(category_id):
    category_service.delete_category(category_id, g.current_user["id"])
    return jsonify({"message": "Category deleted"}), 200
