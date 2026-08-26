from flask import Blueprint, g, jsonify, request

from app.routes.auth import login_required
from app.services import goal_service

goals_bp = Blueprint("goals", __name__)


@goals_bp.route("/api/goals", methods=["GET"])
@login_required
def list_goals():
    return jsonify(goal_service.get_goals(g.current_user["id"])), 200


@goals_bp.route("/api/goals", methods=["POST"])
@login_required
def create_goal():
    try:
        goal = goal_service.create_goal(g.current_user["id"], request.get_json(silent=True))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Goal created", "goal": goal}), 201


@goals_bp.route("/api/goals/<int:goal_id>/add-funds", methods=["POST"])
@login_required
def add_funds(goal_id):
    try:
        goal = goal_service.add_funds(goal_id, g.current_user["id"], request.get_json(silent=True))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"message": "Funds added", "goal": goal}), 200


@goals_bp.route("/api/goals/<int:goal_id>", methods=["DELETE"])
@login_required
def delete_goal(goal_id):
    goal_service.delete_goal(goal_id, g.current_user["id"])
    return jsonify({"message": "Goal deleted"}), 200
