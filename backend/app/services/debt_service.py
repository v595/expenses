from app.models import activity_log as activity_log_model
from app.models import debt as debt_model

MAX_NAME_LENGTH = 80
MAX_INTEREST_RATE = 100


def _validate(data):
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Name is required")
    if len(name.strip()) > MAX_NAME_LENGTH:
        raise ValueError(f"Name must be {MAX_NAME_LENGTH} characters or fewer")

    balance = data.get("balance")
    if not isinstance(balance, (int, float)) or isinstance(balance, bool):
        raise ValueError("Balance must be a number")
    if balance <= 0:
        raise ValueError("Balance must be greater than zero")

    interest_rate = data.get("interest_rate", 0)
    if not isinstance(interest_rate, (int, float)) or isinstance(interest_rate, bool):
        raise ValueError("Interest rate must be a number")
    if interest_rate < 0 or interest_rate > MAX_INTEREST_RATE:
        raise ValueError(f"Interest rate must be between 0 and {MAX_INTEREST_RATE}")

    min_payment = data.get("min_payment")
    if not isinstance(min_payment, (int, float)) or isinstance(min_payment, bool):
        raise ValueError("Minimum payment must be a number")
    if min_payment <= 0:
        raise ValueError("Minimum payment must be greater than zero")
    if min_payment > balance:
        raise ValueError("Minimum payment can't be more than the balance")

    return {
        "name": name.strip(),
        "balance": float(balance),
        "interest_rate": float(interest_rate),
        "min_payment": float(min_payment),
    }


def get_debts(user_id):
    return debt_model.get_debts_by_user(user_id)


def create_debt(user_id, data):
    clean = _validate(data)
    debt = debt_model.create_debt(
        user_id, clean["name"], clean["balance"], clean["interest_rate"], clean["min_payment"]
    )
    activity_log_model.log(user_id, "Added debt", f"{clean['name']} ({clean['balance']:.2f})")
    return debt


def update_debt(debt_id, user_id, data):
    clean = _validate(data)
    debt = debt_model.update_debt(
        debt_id, user_id, clean["name"], clean["balance"], clean["interest_rate"], clean["min_payment"]
    )
    if debt is None:
        raise ValueError("Debt not found")
    activity_log_model.log(user_id, "Updated debt", f"{clean['name']} ({clean['balance']:.2f})")
    return debt


def delete_debt(debt_id, user_id):
    debt = debt_model.get_debt_by_id(debt_id, user_id)
    debt_model.delete_debt(debt_id, user_id)
    if debt:
        activity_log_model.log(user_id, "Deleted debt", debt["name"])


MAX_MONTHS = 1200  # 100 years — a hard stop so a too-small payment can't hang the loop forever


def _order_debts(debts, strategy):
    if strategy == "avalanche":
        return sorted(debts, key=lambda d: -d["interest_rate"])
    return sorted(debts, key=lambda d: d["balance"])  # snowball: smallest balance first


def build_payoff_plan(debts, extra_payment, strategy):
    """Simulates paying every debt's minimum each month, with `extra_payment`
    (plus whatever's freed up as earlier debts finish) piled onto the debt
    that's first in the strategy's order — the standard snowball/avalanche
    method. Returns each debt's payoff month and total interest paid, plus
    the plan's overall totals."""
    if not debts:
        return {"debts": [], "months_to_debt_free": 0, "total_interest": 0.0}

    ordered = _order_debts(debts, strategy)
    remaining = {d["id"]: d["balance"] for d in ordered}
    interest_paid = {d["id"]: 0.0 for d in ordered}
    payoff_month = {}

    month = 0
    while any(remaining[d["id"]] > 0.005 for d in ordered) and month < MAX_MONTHS:
        month += 1
        pool = extra_payment

        for d in ordered:
            did = d["id"]
            if remaining[did] <= 0:
                continue
            monthly_rate = d["interest_rate"] / 100 / 12
            interest = remaining[did] * monthly_rate
            interest_paid[did] += interest
            remaining[did] += interest

            payment = min(d["min_payment"], remaining[did])
            remaining[did] -= payment

            if remaining[did] <= 0.005:
                # This debt just finished — its minimum payment joins the
                # pool immediately, so the freed-up cash rolls onto the next
                # debt in the SAME month rather than waiting until next month.
                pool += d["min_payment"] - payment
                payoff_month[did] = month

        # Extra (plus anything freed up this month) goes to the first debt
        # in strategy order that isn't paid off yet.
        for d in ordered:
            did = d["id"]
            if remaining[did] > 0 and pool > 0:
                apply_amount = min(pool, remaining[did])
                remaining[did] -= apply_amount
                pool -= apply_amount
                if remaining[did] <= 0.005:
                    payoff_month[did] = month
            if pool <= 0:
                break

    results = []
    for d in ordered:
        results.append(
            {
                "id": d["id"],
                "name": d["name"],
                "balance": d["balance"],
                "interest_rate": d["interest_rate"],
                "min_payment": d["min_payment"],
                "payoff_month": payoff_month.get(d["id"], month),
                "total_interest": round(interest_paid[d["id"]], 2),
            }
        )

    return {
        "debts": results,
        "months_to_debt_free": month,
        "total_interest": round(sum(interest_paid.values()), 2),
    }
