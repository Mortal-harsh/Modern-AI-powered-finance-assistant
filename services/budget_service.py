"""
Budget Service.
Manages overall and category-level monthly budgets via Oracle PL/SQL.
Calculates utilization and triggers warning and exceedance alerts based on actual spending.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

try:
    import oracledb
except ImportError:
    oracledb = None

from database.connection import get_db
from models.budget_model import Budget
from config.settings import AppConfig

logger = logging.getLogger("BudgetService")


class BudgetService:
    """Service wrapping PL/SQL procedures for budget lifecycle."""

    def __init__(self):
        self.db = get_db()
        self.default_user_id = AppConfig.get_default_user_id()

    def save_budget(
        self,
        month: int,
        year: int,
        amount: float,
        category_id: Optional[int] = None,
        alert_threshold: int = 80,
        user_id: Optional[int] = None
    ) -> Tuple[bool, Optional[int], str]:
        """
        Executes Oracle PL/SQL procedure SAVE_BUDGET.
        Inserts or updates (upserts) the allocated budget.
        Returns: (success: bool, budget_id: int, message: str)
        """
        u_id = user_id or self.default_user_id
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    out_id = cursor.var(oracledb.NUMBER)
                    cursor.callproc("SAVE_BUDGET", [
                        u_id,
                        category_id,
                        month,
                        year,
                        amount,
                        alert_threshold,
                        out_id
                    ])
                    conn.commit()
                    b_id = int(out_id.getvalue())
                    return True, b_id, "Budget saved successfully in Oracle Database."
        except Exception as e:
            logger.error("PL/SQL SAVE_BUDGET error: %s", e)
            return False, None, f"Failed to save budget: {e}"

    def get_budget_status(self, year: int, month: int, user_id: Optional[int] = None) -> List[Budget]:
        """
        Executes Oracle PL/SQL procedure GET_BUDGET_STATUS returning SYS_REFCURSOR.
        Retrieves allocated budget, actual spending, remaining amount, utilization %, and alert status.
        """
        u_id = user_id or self.default_user_id
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    out_cursor = conn.cursor()
                    cur.callproc("GET_BUDGET_STATUS", [u_id, year, month, out_cursor])
                    rows = self.db.fetch_refcursor(out_cursor)
                    return [Budget.from_dict(r) for r in rows]
        except Exception as e:
            logger.error("PL/SQL GET_BUDGET_STATUS error: %s", e)
            return []

    def delete_budget(self, budget_id: int) -> Tuple[bool, str]:
        """Deletes a budget record by ID."""
        sql = "DELETE FROM BUDGETS WHERE BUDGET_ID = :b_id"
        try:
            affected = self.db.execute_non_query(sql, {"b_id": budget_id})
            if affected > 0:
                return True, "Budget deleted successfully."
            return False, "Budget record not found."
        except Exception as e:
            logger.error("Failed to delete budget: %s", e)
            return False, f"Failed to delete budget: {e}"

    def check_active_alerts(self, year: int, month: int, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Returns list of active budget alerts (warning or exceeded).
        """
        budgets = self.get_budget_status(year, month, user_id)
        alerts = []
        for b in budgets:
            if b.alert_status in ["WARNING", "EXCEEDED"]:
                alerts.append({
                    "budget_id": b.budget_id,
                    "category": b.category_name,
                    "status": b.alert_status,
                    "utilization": b.utilization_pct,
                    "budget": b.budget_amount,
                    "spent": b.actual_spending,
                    "remaining": b.remaining_budget
                })
        return alerts
