from flask import Blueprint, g, jsonify, request

from app.routes.auth import login_required
from app.services import book_service
from app.services.errors import ServiceError

books_bp = Blueprint("books", __name__)


@books_bp.route("/api/books", methods=["GET"])
@login_required
def list_books():
    return jsonify(book_service.get_books(g.current_user["id"])), 200


@books_bp.route("/api/books", methods=["POST"])
@login_required
def create_book():
    try:
        book = book_service.create_book(g.current_user["id"], request.get_json(silent=True))
    except ServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Book created", "book": book}), 201


@books_bp.route("/api/books/<int:book_id>", methods=["PUT"])
@login_required
def update_book(book_id):
    try:
        book = book_service.update_book(book_id, g.current_user["id"], request.get_json(silent=True))
    except ServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Book updated", "book": book}), 200


@books_bp.route("/api/books/<int:book_id>/default", methods=["POST"])
@login_required
def set_default_book(book_id):
    try:
        book = book_service.set_default_book(book_id, g.current_user["id"])
    except ServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    return jsonify({"message": "Default book updated", "book": book}), 200


@books_bp.route("/api/books/<int:book_id>", methods=["DELETE"])
@login_required
def delete_book(book_id):
    try:
        book_service.delete_book(book_id, g.current_user["id"])
    except ServiceError as e:
        return jsonify({"error": e.message}), e.status_code
    return jsonify({"message": "Book deleted"}), 200
