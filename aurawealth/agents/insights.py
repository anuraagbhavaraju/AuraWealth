"""On-Demand Insights specialist for subscription-spending questions."""

from collections import defaultdict
from typing import Any

from aurawealth.models import InsightResult


CURRENT_QUARTER = "2026 Q3"
PRIOR_QUARTER = "2026 Q2"


def _quarter(month: str) -> str:
    year, month_number = month.split("-")
    return f"{year} Q{(int(month_number) - 1) // 3 + 1}"


def subscription_comparison(data: dict[str, Any]) -> InsightResult:
    totals: dict[str, float] = defaultdict(float)
    for transaction in data["subscriptions"]:
        totals[_quarter(transaction["month"])] += transaction["amount"]

    current_total = totals[CURRENT_QUARTER]
    prior_total = totals[PRIOR_QUARTER]
    change = current_total - prior_total
    change_percent = (change / prior_total * 100) if prior_total else 0

    direction = "increased" if change >= 0 else "decreased"
    explanation = (
        f"Your subscription spending {direction} by ${abs(change):,.0f} "
        f"({abs(change_percent):.0f}%) from {PRIOR_QUARTER} to {CURRENT_QUARTER}."
    )
    return InsightResult(
        current_total=current_total,
        prior_total=prior_total,
        change=change,
        change_percent=change_percent,
        current_quarter=CURRENT_QUARTER,
        prior_quarter=PRIOR_QUARTER,
        explanation=explanation,
    )


def answers_subscription_query(query: str) -> bool:
    normalised = query.lower()
    return "subscription" in normalised and any(
        term in normalised for term in ("spend", "spent", "quarter", "compare")
    )
