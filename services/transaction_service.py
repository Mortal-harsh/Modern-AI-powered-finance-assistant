"""
Transaction Service.
Handles all transaction persistence and retrieval operations by invoking
the corresponding Oracle PL/SQL stored procedures and functions.
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import oracledb
except ImportError:
    oracledb = None

from database.connection import get_db
from models.transaction_model import Transaction
from models.category_model import Category
from config.settings import AppConfig

logger = logging.getLogger("TransactionService")


class TransactionService:
    """Service wrapping PL/SQL procedures for transaction lifecycle."""

    def __init__(self):
        self.db = get_db()
        self.default_user_id = AppConfig.get_default_user_id()

    def add_transaction(
        self,
        category_id: int,
        transaction_type: str,
        expense_type: str,
        amount: float,
        transaction_date: Union[date, datetime],
        payment_method: str,
        description: str,
        notes: str = "",
        user_id: Optional[int] = None
    ) -> Tuple[bool, Optional[int], str]:
        """
        Executes Oracle PL/SQL procedure ADD_TRANSACTION.
        Returns: (success: bool, new_transaction_id: int, message: str)
        """
        u_id = user_id or self.default_user_id
        if isinstance(transaction_date, datetime):
            tx_date = transaction_date.date()
        else:
            tx_date = transaction_date

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    out_id = cursor.var(oracledb.NUMBER)
                    cursor.callproc("ADD_TRANSACTION", [
                        u_id,
                        category_id,
                        transaction_type.upper(),
                        expense_type.upper(),
                        amount,
                        tx_date,
                        payment_method,
                        description,
                        notes,
                        out_id
                    ])
                    conn.commit()
                    new_id = int(out_id.getvalue())
                    return True, new_id, "Transaction recorded successfully in Oracle Database."
        except Exception as e:
            logger.error("PL/SQL ADD_TRANSACTION error: %s", e)
            return False, None, f"Failed to record transaction: {e}"

    def update_transaction(
        self,
        transaction_id: int,
        category_id: int,
        transaction_type: str,
        expense_type: str,
        amount: float,
        transaction_date: Union[date, datetime],
        payment_method: str,
        description: str,
        notes: str = ""
    ) -> Tuple[bool, str]:
        """
        Executes Oracle PL/SQL procedure UPDATE_TRANSACTION.
        Returns: (success: bool, message: str)
        """
        if isinstance(transaction_date, datetime):
            tx_date = transaction_date.date()
        else:
            tx_date = transaction_date

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    out_rows = cursor.var(oracledb.NUMBER)
                    cursor.callproc("UPDATE_TRANSACTION", [
                        transaction_id,
                        category_id,
                        transaction_type.upper(),
                        expense_type.upper(),
                        amount,
                        tx_date,
                        payment_method,
                        description,
                        notes,
                        out_rows
                    ])
                    conn.commit()
                    updated = out_rows.getvalue()
                    if updated and updated > 0:
                        return True, "Transaction updated successfully."
                    return False, "Transaction not found."
        except Exception as e:
            logger.error("PL/SQL UPDATE_TRANSACTION error: %s", e)
            return False, f"Failed to update transaction: {e}"

    def delete_transaction(self, transaction_id: int) -> Tuple[bool, str]:
        """
        Executes Oracle PL/SQL procedure DELETE_TRANSACTION.
        Returns: (success: bool, message: str)
        """
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    out_rows = cursor.var(oracledb.NUMBER)
                    cursor.callproc("DELETE_TRANSACTION", [
                        transaction_id,
                        out_rows
                    ])
                    conn.commit()
                    deleted = out_rows.getvalue()
                    if deleted and deleted > 0:
                        return True, "Transaction deleted successfully."
                    return False, "Transaction not found or already deleted."
        except Exception as e:
            logger.error("PL/SQL DELETE_TRANSACTION error: %s", e)
            return False, f"Failed to delete transaction: {e}"

    def get_total_income(self, year: Optional[int] = None, month: Optional[int] = None, user_id: Optional[int] = None) -> float:
        """Calls PL/SQL function GET_TOTAL_INCOME."""
        u_id = user_id or self.default_user_id
        try:
            val = self.db.call_function("GET_TOTAL_INCOME", oracledb.NUMBER, [u_id, year, month])
            return float(val or 0.0)
        except Exception as e:
            logger.error("PL/SQL GET_TOTAL_INCOME error: %s", e)
            return 0.0

    def get_total_expenses(self, year: Optional[int] = None, month: Optional[int] = None, user_id: Optional[int] = None) -> float:
        """Calls PL/SQL function GET_TOTAL_EXPENSES."""
        u_id = user_id or self.default_user_id
        try:
            val = self.db.call_function("GET_TOTAL_EXPENSES", oracledb.NUMBER, [u_id, year, month])
            return float(val or 0.0)
        except Exception as e:
            logger.error("PL/SQL GET_TOTAL_EXPENSES error: %s", e)
            return 0.0

    def get_monthly_summary(self, year: Optional[int] = None, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Calls PL/SQL procedure GET_MONTHLY_SUMMARY returning SYS_REFCURSOR.
        """
        u_id = user_id or self.default_user_id
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    out_cursor = conn.cursor()
                    cur.callproc("GET_MONTHLY_SUMMARY", [u_id, year, out_cursor])
                    return self.db.fetch_refcursor(out_cursor)
        except Exception as e:
            logger.error("PL/SQL GET_MONTHLY_SUMMARY error: %s", e)
            # Safe empty structure for 12 months
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            return [{"MONTH_NUM": i+1, "MONTH_NAME": m, "TOTAL_INCOME": 0, "TOTAL_EXPENSE": 0, "NET_SAVINGS": 0} for i, m in enumerate(months)]

    def get_category_summary(self, year: Optional[int] = None, month: Optional[int] = None, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Calls PL/SQL procedure GET_CATEGORY_SUMMARY returning SYS_REFCURSOR.
        """
        u_id = user_id or self.default_user_id
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    out_cursor = conn.cursor()
                    cur.callproc("GET_CATEGORY_SUMMARY", [u_id, year, month, out_cursor])
                    return self.db.fetch_refcursor(out_cursor)
        except Exception as e:
            logger.error("PL/SQL GET_CATEGORY_SUMMARY error: %s", e)
            return []

    def get_transactions(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        category_id: Optional[int] = None,
        transaction_type: Optional[str] = None,
        search_query: Optional[str] = None,
        user_id: Optional[int] = None,
        limit: int = 500
    ) -> List[Transaction]:
        """
        Retrieves transactions with dynamic filters using safe bind parameters.
        """
        u_id = user_id or self.default_user_id
        sql = """
            SELECT 
                t.TRANSACTION_ID,
                t.USER_ID,
                t.CATEGORY_ID,
                c.CATEGORY_NAME,
                t.TRANSACTION_TYPE,
                t.EXPENSE_TYPE,
                t.AMOUNT,
                t.TRANSACTION_DATE,
                t.PAYMENT_METHOD,
                t.DESCRIPTION,
                t.NOTES,
                t.CREATED_AT
            FROM TRANSACTIONS t
            JOIN CATEGORIES c ON t.CATEGORY_ID = c.CATEGORY_ID
            WHERE t.USER_ID = :user_id
        """
        params: Dict[str, Any] = {"user_id": u_id}

        if year is not None:
            sql += " AND EXTRACT(YEAR FROM t.TRANSACTION_DATE) = :p_year"
            params["p_year"] = year

        if month is not None:
            sql += " AND EXTRACT(MONTH FROM t.TRANSACTION_DATE) = :p_month"
            params["p_month"] = month

        if category_id is not None and category_id > 0:
            sql += " AND t.CATEGORY_ID = :p_cat"
            params["p_cat"] = category_id

        if transaction_type and transaction_type.upper() in ["INCOME", "EXPENSE"]:
            sql += " AND t.TRANSACTION_TYPE = :p_type"
            params["p_type"] = transaction_type.upper()

        if search_query and search_query.strip():
            sql += " AND (UPPER(t.DESCRIPTION) LIKE :p_search OR UPPER(c.CATEGORY_NAME) LIKE :p_search OR UPPER(t.PAYMENT_METHOD) LIKE :p_search)"
            params["p_search"] = f"%{search_query.strip().upper()}%"

        sql += " ORDER BY t.TRANSACTION_DATE DESC, t.TRANSACTION_ID DESC"

        try:
            rows = self.db.execute_query(sql, params)
            return [Transaction.from_dict(r) for r in rows[:limit]]
        except Exception as e:
            logger.error("Failed to query transactions: %s", e)
            return []

    def get_categories(self, category_type: Optional[str] = None) -> List[Category]:
        """Fetches active categories."""
        sql = "SELECT * FROM CATEGORIES WHERE IS_ACTIVE = 'Y'"
        params = {}
        if category_type:
            sql += " AND CATEGORY_TYPE IN (:c_type, 'BOTH')"
            params["c_type"] = category_type.upper()
        sql += " ORDER BY CATEGORY_NAME ASC"

        try:
            rows = self.db.execute_query(sql, params)
            return [Category.from_dict(r) for r in rows]
        except Exception as e:
            logger.error("Failed to fetch categories: %s", e)
            return []

    def get_available_years(self, user_id: Optional[int] = None) -> List[int]:
        """Fetches all distinct transaction years available in database."""
        u_id = user_id or self.default_user_id
        sql = """
            SELECT DISTINCT EXTRACT(YEAR FROM TRANSACTION_DATE) AS T_YEAR
            FROM TRANSACTIONS
            WHERE USER_ID = :u_id
            ORDER BY T_YEAR DESC
        """
        try:
            rows = self.db.execute_query(sql, {"u_id": u_id})
            years = [int(r["T_YEAR"]) for r in rows if r.get("T_YEAR")]
            # Ensure 2024 and current year are included
            current_year = datetime.now().year
            for y in [2024, current_year]:
                if y not in years:
                    years.append(y)
            return sorted(list(set(years)), reverse=True)
        except Exception as e:
            logger.error("Failed to fetch available years: %s", e)
            return [2024, 2023, 2022]
