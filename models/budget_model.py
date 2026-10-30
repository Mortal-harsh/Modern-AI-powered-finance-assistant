"""
Budget Data Model.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Budget:
    budget_id: Optional[int]
    user_id: int
    category_id: Optional[int]
    category_name: str
    budget_month: int
    budget_year: int
    budget_amount: float
    actual_spending: float = 0.0
    remaining_budget: float = 0.0
    utilization_pct: float = 0.0
    alert_threshold: int = 80
    alert_status: str = "OK"  # 'OK', 'WARNING', 'EXCEEDED'

    @classmethod
    def from_dict(cls, data: dict) -> "Budget":
        return cls(
            budget_id=int(data["BUDGET_ID"]) if data.get("BUDGET_ID") else None,
            user_id=int(data.get("USER_ID", 1)),
            category_id=int(data["CATEGORY_ID"]) if data.get("CATEGORY_ID") is not None else None,
            category_name=str(data.get("CATEGORY_NAME", "OVERALL MONTHLY BUDGET")),
            budget_month=int(data.get("BUDGET_MONTH", 1)),
            budget_year=int(data.get("BUDGET_YEAR", 2024)),
            budget_amount=float(data.get("BUDGET_AMOUNT", 0.0)),
            actual_spending=float(data.get("ACTUAL_SPENDING", 0.0)),
            remaining_budget=float(data.get("REMAINING_BUDGET", 0.0)),
            utilization_pct=float(data.get("UTILIZATION_PCT", 0.0)),
            alert_threshold=int(data.get("ALERT_THRESHOLD", 80)),
            alert_status=str(data.get("ALERT_STATUS", "OK"))
        )
