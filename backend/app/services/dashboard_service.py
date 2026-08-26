from datetime import datetime, timezone

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


def _prev_year_month(year_month):
    year, month = (int(part) for part in year_month.split("-"))
    if month == 1:
        return f"{year - 1}-12"
    return f"{year}-{month - 1:02d}"


def get_insights(user_id, top_n=3):
    """Compares this month's category spending to last month's and surfaces
    the biggest movers — cheap to compute (two grouped queries) and doesn't
    need its own table since it's derived entirely from transactions."""
    this_month = datetime.now(timezone.utc).strftime("%Y-%m")
    last_month = _prev_year_month(this_month)

    current = transaction_model.get_category_spending_for_month(user_id, this_month)
    previous = transaction_model.get_category_spending_for_month(user_id, last_month)

    movers = []
    for category in set(current) | set(previous):
        now_amount = current.get(category, 0)
        prev_amount = previous.get(category, 0)
        change = now_amount - prev_amount
        if prev_amount > 0:
            percent = (change / prev_amount) * 100
        elif now_amount > 0:
            percent = 100.0
        else:
            percent = 0.0
        if change == 0:
            continue
        movers.append(
            {
                "category": category,
                "current": now_amount,
                "previous": prev_amount,
                "change": change,
                "percent_change": percent,
            }
        )

    movers.sort(key=lambda m: abs(m["change"]), reverse=True)
    return {"this_month": this_month, "last_month": last_month, "movers": movers[:top_n]}
