"""
Analytics Service.
Leverages Pandas and NumPy to perform advanced statistical and financial aggregations
from Oracle database transactions, including Month-over-Month (MoM) variance,
spending trends, expense distributions, and budget performance metrics.
"""

import logging
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from database.connection import get_db
from config.settings import AppConfig

logger = logging.getLogger("AnalyticsService")


class AnalyticsService:
    """Performs financial analysis using Pandas and NumPy over Oracle data."""

    def __init__(self):
        self.db = get_db()
        self.default_user_id = AppConfig.get_default_user_id()

    def get_transaction_dataframe(self, year: Optional[int] = None, user_id: Optional[int] = None) -> pd.DataFrame:
        """
        Fetches transactions from Oracle and returns a structured Pandas DataFrame.
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
                t.DESCRIPTION
            FROM TRANSACTIONS t
            JOIN CATEGORIES c ON t.CATEGORY_ID = c.CATEGORY_ID
            WHERE t.USER_ID = :u_id
        """
        params = {"u_id": u_id}
        if year is not None:
            sql += " AND EXTRACT(YEAR FROM t.TRANSACTION_DATE) = :p_year"
            params["p_year"] = year

        try:
            rows = self.db.execute_query(sql, params)
            if not rows:
                return pd.DataFrame(columns=[
                    "TRANSACTION_ID", "USER_ID", "CATEGORY_ID", "CATEGORY_NAME",
                    "TRANSACTION_TYPE", "EXPENSE_TYPE", "AMOUNT", "TRANSACTION_DATE",
                    "PAYMENT_METHOD", "DESCRIPTION", "YEAR", "MONTH"
                ])
            df = pd.DataFrame(rows)
            df["AMOUNT"] = pd.to_numeric(df["AMOUNT"], errors="coerce").fillna(0.0)
            df["TRANSACTION_DATE"] = pd.to_datetime(df["TRANSACTION_DATE"])
            df["YEAR"] = df["TRANSACTION_DATE"].dt.year
            df["MONTH"] = df["TRANSACTION_DATE"].dt.month
            df["MONTH_NAME"] = df["TRANSACTION_DATE"].dt.strftime("%b")
            return df
        except Exception as e:
            logger.error("Failed to build transaction DataFrame: %s", e)
            return pd.DataFrame()

    def get_kpi_metrics(self, year: Optional[int] = None, month: Optional[int] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Computes high-level KPI cards: Total Income, Total Expenses, Savings, Expense %, Savings %.
        Safe from division by zero.
        """
        df = self.get_transaction_dataframe(year=year, user_id=user_id)
        if df.empty:
            return {
                "total_income": 0.0,
                "total_expenses": 0.0,
                "savings": 0.0,
                "expense_pct": 0.0,
                "savings_pct": 0.0,
                "transaction_count": 0
            }

        if month is not None:
            df = df[df["MONTH"] == month]

        income_df = df[df["TRANSACTION_TYPE"] == "INCOME"]
        expense_df = df[df["TRANSACTION_TYPE"] == "EXPENSE"]

        total_income = float(income_df["AMOUNT"].sum())
        total_expenses = float(expense_df["AMOUNT"].sum())
        savings = total_income - total_expenses

        # Safe percentage formulas
        if total_income > 0:
            expense_pct = (total_expenses / total_income) * 100.0
            savings_pct = (savings / total_income) * 100.0
        else:
            expense_pct = 100.0 if total_expenses > 0 else 0.0
            savings_pct = 0.0

        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "savings": savings,
            "expense_pct": round(expense_pct, 1),
            "savings_pct": round(savings_pct, 1),
            "transaction_count": len(df)
        }

    def get_monthly_trend_analysis(self, year: Optional[int] = None, user_id: Optional[int] = None) -> pd.DataFrame:
        """
        Constructs a 12-month summary DataFrame with NumPy rolling average and MoM growth.
        """
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        base_df = pd.DataFrame({
            "MONTH": list(range(1, 13)),
            "MONTH_NAME": months,
            "INCOME": 0.0,
            "EXPENSES": 0.0,
            "SAVINGS": 0.0
        })

        df = self.get_transaction_dataframe(year=year, user_id=user_id)
        if df.empty:
            return base_df

        # Aggregate monthly
        inc = df[df["TRANSACTION_TYPE"] == "INCOME"].groupby("MONTH")["AMOUNT"].sum().reset_index()
        exp = df[df["TRANSACTION_TYPE"] == "EXPENSE"].groupby("MONTH")["AMOUNT"].sum().reset_index()

        merged = base_df.merge(inc.rename(columns={"AMOUNT": "INC_ACTUAL"}), on="MONTH", how="left")
        merged = merged.merge(exp.rename(columns={"AMOUNT": "EXP_ACTUAL"}), on="MONTH", how="left")

        merged["INCOME"] = merged["INC_ACTUAL"].fillna(0.0)
        merged["EXPENSES"] = merged["EXP_ACTUAL"].fillna(0.0)
        merged["SAVINGS"] = merged["INCOME"] - merged["EXPENSES"]
        merged.drop(columns=["INC_ACTUAL", "EXP_ACTUAL"], inplace=True)

        # NumPy rolling average for expense trend
        merged["EXPENSE_3M_AVG"] = np.round(merged["EXPENSES"].rolling(window=3, min_periods=1).mean(), 2)

        # MoM Expense Growth Percentage
        merged["PREV_EXPENSE"] = merged["EXPENSES"].shift(1)
        merged["MOM_GROWTH_PCT"] = np.where(
            merged["PREV_EXPENSE"] > 0,
            np.round(((merged["EXPENSES"] - merged["PREV_EXPENSE"]) / merged["PREV_EXPENSE"]) * 100, 1),
            0.0
        )
        merged.drop(columns=["PREV_EXPENSE"], inplace=True)

        return merged

    def get_category_distribution(self, year: Optional[int] = None, month: Optional[int] = None, user_id: Optional[int] = None) -> pd.DataFrame:
        """
        Computes category-wise expense breakdown, total amounts, and share percentage.
        """
        df = self.get_transaction_dataframe(year=year, user_id=user_id)
        if df.empty:
            return pd.DataFrame(columns=["CATEGORY_NAME", "AMOUNT", "SHARE_PCT", "COUNT"])

        exp_df = df[df["TRANSACTION_TYPE"] == "EXPENSE"]
        if month is not None:
            exp_df = exp_df[exp_df["MONTH"] == month]

        if exp_df.empty:
            return pd.DataFrame(columns=["CATEGORY_NAME", "AMOUNT", "SHARE_PCT", "COUNT"])

        cat_summary = exp_df.groupby("CATEGORY_NAME").agg(
            AMOUNT=("AMOUNT", "sum"),
            COUNT=("TRANSACTION_ID", "count")
        ).reset_index()

        total = cat_summary["AMOUNT"].sum()
        if total > 0:
            cat_summary["SHARE_PCT"] = np.round((cat_summary["AMOUNT"] / total) * 100, 1)
        else:
            cat_summary["SHARE_PCT"] = 0.0

        return cat_summary.sort_values(by="AMOUNT", ascending=False).reset_index(drop=True)

    def get_expense_type_distribution(self, year: Optional[int] = None, month: Optional[int] = None, user_id: Optional[int] = None) -> pd.DataFrame:
        """
        Computes distribution by expense type (NEED, WANTS, SELF, ANONYMOUS, etc.)
        Matches the 'Total Expenses by TYPE' donut chart in reference dashboard.
        """
        df = self.get_transaction_dataframe(year=year, user_id=user_id)
        if df.empty:
            return pd.DataFrame(columns=["EXPENSE_TYPE", "AMOUNT", "SHARE_PCT"])

        exp_df = df[df["TRANSACTION_TYPE"] == "EXPENSE"]
        if month is not None:
            exp_df = exp_df[exp_df["MONTH"] == month]

        if exp_df.empty:
            return pd.DataFrame(columns=["EXPENSE_TYPE", "AMOUNT", "SHARE_PCT"])

        type_summary = exp_df.groupby("EXPENSE_TYPE")["AMOUNT"].sum().reset_index()
        total = type_summary["AMOUNT"].sum()
        if total > 0:
            type_summary["SHARE_PCT"] = np.round((type_summary["AMOUNT"] / total) * 100, 1)
        else:
            type_summary["SHARE_PCT"] = 0.0

        return type_summary.sort_values(by="AMOUNT", ascending=False).reset_index(drop=True)

    def get_statistical_insights(self, year: Optional[int] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Returns statistical summary: highest spending category, average monthly expenses,
        highest spending month, median transaction amount.
        """
        df = self.get_transaction_dataframe(year=year, user_id=user_id)
        if df.empty:
            return {
                "top_category": "N/A",
                "top_category_amount": 0.0,
                "avg_monthly_expense": 0.0,
                "peak_month": "N/A",
                "median_transaction": 0.0,
                "total_expense": 0.0
            }

        exp_df = df[df["TRANSACTION_TYPE"] == "EXPENSE"]
        if exp_df.empty:
            return {
                "top_category": "N/A",
                "top_category_amount": 0.0,
                "avg_monthly_expense": 0.0,
                "peak_month": "N/A",
                "median_transaction": 0.0,
                "total_expense": 0.0
            }

        # Top category
        cat_group = exp_df.groupby("CATEGORY_NAME")["AMOUNT"].sum()
        top_cat = cat_group.idxmax() if not cat_group.empty else "N/A"
        top_cat_amt = float(cat_group.max()) if not cat_group.empty else 0.0

        # Monthly averages
        monthly_exp = exp_df.groupby("MONTH_NAME")["AMOUNT"].sum()
        avg_monthly = float(np.mean(monthly_exp.values)) if len(monthly_exp) > 0 else 0.0
        peak_month = monthly_exp.idxmax() if not monthly_exp.empty else "N/A"
        median_tx = float(np.median(exp_df["AMOUNT"].values)) if len(exp_df) > 0 else 0.0

        return {
            "top_category": top_cat,
            "top_category_amount": top_cat_amt,
            "avg_monthly_expense": round(avg_monthly, 2),
            "peak_month": peak_month,
            "median_transaction": round(median_tx, 2),
            "total_expense": float(exp_df["AMOUNT"].sum())
        }
