from app.extensions import db
from app.models.orm import Goal, now_iso


def get_goals_by_user(user_id):
    rows = (
        db.session.query(Goal)
        .filter_by(user_id=user_id)
        .order_by(Goal.target_date.is_(None), Goal.target_date)
        .all()
    )
    return [g.to_dict() for g in rows]


def get_goal_by_id(goal_id, user_id):
    goal = db.session.query(Goal).filter_by(id=goal_id, user_id=user_id).first()
    return goal.to_dict() if goal else None


def create_goal(user_id, name, target_amount, target_date):
    goal = Goal(
        user_id=user_id,
        name=name,
        target_amount=target_amount,
        target_date=target_date,
        created_at=now_iso(),
    )
    db.session.add(goal)
    db.session.commit()
    return goal.to_dict()


def add_funds(goal_id, user_id, amount):
    goal = db.session.query(Goal).filter_by(id=goal_id, user_id=user_id).first()
    if goal is None:
        return None
    goal.current_amount = goal.current_amount + amount
    db.session.commit()
    return goal.to_dict()


def delete_goal(goal_id, user_id):
    db.session.query(Goal).filter_by(id=goal_id, user_id=user_id).delete()
    db.session.commit()
