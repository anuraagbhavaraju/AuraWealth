"""Cash-flow projection for the Goal Planning specialist."""

from datetime import date
from typing import Any, Dict, Union


def months_until(target_month: str, as_of: date = date(2026, 9, 17)) -> int:
    year, month = (int(part) for part in target_month.split("-"))
    return max(0, (year - as_of.year) * 12 + month - as_of.month)


def model_goal_affordability(data: Dict[str, Any], planned_cost: float = 6_000) -> Dict[str, Union[float, int, bool]]:
    client, goal, mortgage = data["client"], data["goal"], data["mortgage"]
    months = months_until(goal["target_month"])
    monthly_outgoings = sum(data["monthly_expenses"].values()) + mortgage["monthly_payment"]
    projected_cash = client["cash_balance"] + (client["monthly_income"] - monthly_outgoings) * months
    cash_after_cost = projected_cash - planned_cost
    return {"planned_cost": planned_cost, "cash_after_cost": cash_after_cost, "emergency_fund_target": client["emergency_fund_target"], "buffer": cash_after_cost - client["emergency_fund_target"], "affordable": cash_after_cost >= client["emergency_fund_target"]}
