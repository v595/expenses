from app.models import transaction as transaction_model


def get_summary(user_id):
    totals = transaction_model.get_totals(user_id)
    category_spending = transaction_model.get_category_spending(user_id)

    return {
        "income": totals["income"],
        "expenses": totals["expenses"],
        "balance": totals["income"] - totals["expenses"],
        "transaction_count": totals["transaction_count"],
        "top_category": category_spending[0] if category_spending else None,
        "category_spending": category_spending,
    }


def get_monthly(user_id):
    return {"monthly": transaction_model.get_monthly_totals(user_id)}
