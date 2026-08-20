import os

from flask import Blueprint, jsonify, request

from app.database import get_db_connection

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/api/admin/users", methods=["GET"])
def list_users_with_transactions():
    # ponytail: shared-secret header, not a real admin auth system.
    # Swap for a proper is_admin flag + login_required if this grows past one debug route.
    secret = os.environ.get("ADMIN_SECRET")
    if not secret or request.headers.get("X-Admin-Secret") != secret:
        return jsonify({"error": "Not found"}), 404

    conn = get_db_connection()
    users = conn.execute(
        "SELECT id, name, email, created_at FROM users ORDER BY name"
    ).fetchall()

    result = []
    for user in users:
        transactions = conn.execute(
            "SELECT id, date, type, category, amount, description FROM transactions "
            "WHERE user_id = ? ORDER BY date DESC",
            (user["id"],),
        ).fetchall()
        result.append(
            {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "created_at": user["created_at"],
                "transactions": [dict(t) for t in transactions],
            }
        )

    conn.close()
    return jsonify(result)
