import re
from typing import Any, Dict, Union


def prepayment_amount(query: str, default: float = 10_000) -> float:
    match = re.search(r"\$\s*([\d,]+(?:\.\d{1,2})?)", query)
    return float(match.group(1).replace(",", "")) if match else default


def total_interest(balance: float, annual_rate_percent: float, monthly_payment: float) -> tuple[float, int]:
    monthly_rate = annual_rate_percent / 100 / 12
    interest_paid = 0.0
    months = 0
    while balance > 0.01:
        interest = balance * monthly_rate
        payment = min(monthly_payment, balance + interest)
        interest_paid += interest
        balance = balance + interest - payment
        months += 1
        if months > 600:
            raise ValueError("Monthly payment does not repay the loan.")
    return interest_paid, months


def model_prepayment(mortgage: Dict[str, Any], extra_payment: float) -> Dict[str, Union[float, int]]:
    balance = mortgage["outstanding_balance"]
    baseline_interest, baseline_months = total_interest(
        balance, mortgage["interest_rate_percent"], mortgage["monthly_payment"]
    )
    prepaid_interest, prepaid_months = total_interest(
        balance - extra_payment, mortgage["interest_rate_percent"], mortgage["monthly_payment"]
    )
    return {
        "extra_payment": extra_payment,
        "interest_saved": baseline_interest - prepaid_interest,
        "months_saved": baseline_months - prepaid_months,
        "baseline_months": baseline_months,
        "new_months": prepaid_months,
    }
