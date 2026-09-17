"""Small shared types returned by the agent workflow."""

from dataclasses import dataclass


@dataclass(frozen=True)
class InsightResult:
    current_total: float
    prior_total: float
    change: float
    change_percent: float
    current_quarter: str
    prior_quarter: str
    explanation: str
