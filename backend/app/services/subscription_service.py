"""Subscription radar: spot recurring-looking charges in transaction history
that the user never set up a Recurring rule for — the classic "forgotten
subscription" ($499/mo Netflix nobody remembers signing up for).

This is a heuristic over existing Transaction rows, not a new data model:
group same-description expenses, and flag a group as a likely subscription
when the same amount (within a small tolerance) shows up in at least
MIN_OCCURRENCES distinct months."""

from collections import defaultdict

from app.models import recurring as recurring_model
from app.models import transaction as transaction_model

MIN_OCCURRENCES = 2
AMOUNT_TOLERANCE = 0.05  # 5% — allows for small price changes/rounding


def _month_key(date_str):
    return date_str[:7]  # "YYYY-MM-DD" -> "YYYY-MM"


def _amounts_match(a, b):
    if a == 0 or b == 0:
        return a == b
    return abs(a - b) / max(a, b) <= AMOUNT_TOLERANCE


def _group_key(transaction):
    # Description is the closest thing to "which merchant/service" — category
    # alone is too coarse (e.g. every "Shopping" purchase isn't one subscription).
    description = (transaction["description"] or "").strip().lower()
    return (description, transaction["category"]) if description else None


def _already_tracked(user_id, category, amount):
    """True if a Recurring rule already exists for roughly this category and
    amount — the user already knows about and is tracking this charge."""
    for rule in recurring_model.get_recurring_by_user(user_id):
        if rule["category"] == category and _amounts_match(rule["amount"], amount):
            return True
    return False


def detect_subscriptions(user_id):
    transactions = transaction_model.get_transactions_by_user(user_id, type_="expense")

    groups = defaultdict(list)
    for t in transactions:
        key = _group_key(t)
        if key is not None:
            groups[key].append(t)

    detected = []
    for (description, category), rows in groups.items():
        rows.sort(key=lambda t: t["date"])

        # Cluster by matching amount within this description group — a
        # merchant occasionally charges two different things under the same
        # description (e.g. "Amazon"), so amount clustering keeps those separate.
        clusters = []
        for t in rows:
            placed = False
            for cluster in clusters:
                if _amounts_match(cluster[-1]["amount"], t["amount"]):
                    cluster.append(t)
                    placed = True
                    break
            if not placed:
                clusters.append([t])

        for cluster in clusters:
            months = {_month_key(t["date"]) for t in cluster}
            if len(months) < MIN_OCCURRENCES:
                continue

            avg_amount = sum(t["amount"] for t in cluster) / len(cluster)
            last = cluster[-1]

            if _already_tracked(user_id, category, avg_amount):
                continue

            detected.append(
                {
                    "description": last["description"],
                    "category": category,
                    "amount": round(avg_amount, 2),
                    "times_seen": len(cluster),
                    "months_seen": len(months),
                    "first_date": cluster[0]["date"],
                    "last_date": last["date"],
                    "estimated_yearly_cost": round(avg_amount * 12, 2),
                }
            )

    detected.sort(key=lambda d: -d["estimated_yearly_cost"])
    return detected
