from app.extensions import db
from app.models.orm import Budget, BudgetShare, User, now_iso


def get_share(budget_id, shared_with_user_id):
    share = db.session.query(BudgetShare).filter_by(
        budget_id=budget_id, shared_with_user_id=shared_with_user_id
    ).first()
    return share.to_dict() if share else None


def get_shares_for_budget(budget_id):
    rows = db.session.query(BudgetShare).filter_by(budget_id=budget_id).all()
    return [s.to_dict() for s in rows]


def create_share(budget_id, owner_user_id, shared_with_user_id):
    share = BudgetShare(
        budget_id=budget_id,
        owner_user_id=owner_user_id,
        shared_with_user_id=shared_with_user_id,
        created_at=now_iso(),
    )
    db.session.add(share)
    db.session.commit()
    return share.to_dict()


def delete_share(budget_id, shared_with_user_id):
    db.session.query(BudgetShare).filter_by(
        budget_id=budget_id, shared_with_user_id=shared_with_user_id
    ).delete()
    db.session.commit()


def get_budgets_shared_with_user(user_id):
    """Every budget shared with this user, with the owning user's name/email
    attached — read-only visibility, not ownership."""
    rows = (
        db.session.query(BudgetShare, Budget, User)
        .join(Budget, Budget.id == BudgetShare.budget_id)
        .join(User, User.id == BudgetShare.owner_user_id)
        .filter(BudgetShare.shared_with_user_id == user_id)
        .all()
    )
    return [
        {
            "share_id": share.id,
            "budget_id": budget.id,
            "category": budget.category,
            "monthly_limit": budget.monthly_limit,
            "owner_user_id": owner.id,
            "owner_name": owner.name,
        }
        for share, budget, owner in rows
    ]
