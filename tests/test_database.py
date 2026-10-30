"""
Integration Tests for Oracle Database and PL/SQL Stored Procedures.
Validates real database connectivity and procedures execution.
"""

import unittest
from datetime import date
from database.connection import get_db
from services.transaction_service import TransactionService
from services.budget_service import BudgetService


class TestDatabaseIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = get_db()
        cls.tx_service = TransactionService()
        cls.budget_service = BudgetService()

    def test_01_oracle_connection(self):
        ok, msg, details = self.db.test_connection()
        self.assertTrue(ok, f"Oracle connection failed: {msg}")
        self.assertIn("Oracle", details.get("server_version", ""))

    def test_02_transaction_plsql_lifecycle(self):
        # 1. Add Transaction via PL/SQL ADD_TRANSACTION
        ok, tx_id, msg = self.tx_service.add_transaction(
            category_id=6,  # FOOD_SUPPLIES
            transaction_type="EXPENSE",
            expense_type="NEED",
            amount=999.50,
            transaction_date=date.today(),
            payment_method="UPI",
            description="Integration Test Transaction",
            notes="Temporary test row"
        )
        self.assertTrue(ok, msg)
        self.assertIsNotNone(tx_id)

        # 2. Update Transaction via PL/SQL UPDATE_TRANSACTION
        u_ok, u_msg = self.tx_service.update_transaction(
            transaction_id=tx_id,
            category_id=6,
            transaction_type="EXPENSE",
            expense_type="WANTS",
            amount=1250.00,
            transaction_date=date.today(),
            payment_method="Credit Card",
            description="Updated Integration Test Transaction",
            notes="Updated note"
        )
        self.assertTrue(u_ok, u_msg)

        # 3. Delete Transaction via PL/SQL DELETE_TRANSACTION
        d_ok, d_msg = self.tx_service.delete_transaction(tx_id)
        self.assertTrue(d_ok, d_msg)

    def test_03_plsql_functions_and_refcursors(self):
        # Test total income function
        income = self.tx_service.get_total_income(year=2024)
        self.assertGreaterEqual(income, 0.0)

        # Test total expenses function
        expenses = self.tx_service.get_total_expenses(year=2024)
        self.assertGreaterEqual(expenses, 0.0)

        # Test monthly summary refcursor
        m_data = self.tx_service.get_monthly_summary(year=2024)
        self.assertEqual(len(m_data), 12)

        # Test category summary refcursor
        cat_data = self.tx_service.get_category_summary(year=2024)
        self.assertIsInstance(cat_data, list)

    def test_04_budget_plsql_lifecycle(self):
        # Save budget via PL/SQL SAVE_BUDGET
        ok, b_id, msg = self.budget_service.save_budget(
            month=12,
            year=2024,
            amount=45000.00,
            category_id=None,
            alert_threshold=85
        )
        self.assertTrue(ok, msg)
        self.assertIsNotNone(b_id)

        # Query budget status via PL/SQL GET_BUDGET_STATUS
        statuses = self.budget_service.get_budget_status(year=2024, month=12)
        self.assertTrue(any(b.budget_id == b_id for b in statuses))

        # Cleanup
        del_ok, _ = self.budget_service.delete_budget(b_id)
        self.assertTrue(del_ok)


if __name__ == "__main__":
    unittest.main()
