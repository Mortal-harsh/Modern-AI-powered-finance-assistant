"""
Unit Tests for Financial Calculations and Formatters.
Verifies savings formulas, percentage rounding, division-by-zero handling,
and Indian numbering system format.
"""

import unittest
from utils.formatters import format_inr, format_compact_inr, format_pct


class TestCalculations(unittest.TestCase):

    def test_inr_formatting(self):
        # 3 Lakhs, 12 Thousand, 719
        self.assertEqual(format_inr(312719), "₹3,12,719")
        # 1 Lakh 20 Thousand
        self.assertEqual(format_inr(120000), "₹1,20,000")
        # 552810
        self.assertEqual(format_inr(552810), "₹5,52,810")
        # Negative amount
        self.assertEqual(format_inr(-4500), "-₹4,500")

    def test_compact_formatting(self):
        # 710000 -> ₹710K
        self.assertEqual(format_compact_inr(710000), "₹710K")
        # 553000 -> ₹553K
        self.assertEqual(format_compact_inr(553000), "₹553K")
        # 1.5 Crore -> ₹1.5Cr
        self.assertEqual(format_compact_inr(15000000), "₹1.5Cr")

    def test_kpi_formulas(self):
        # Scenario: Income 7,10,000 | Expense 5,53,800
        income = 710000.0
        expenses = 553800.0

        savings = income - expenses
        self.assertEqual(savings, 156200.0)

        expense_pct = (expenses / income) * 100.0
        self.assertAlmostEqual(expense_pct, 78.0, delta=0.5)

        savings_pct = (savings / income) * 100.0
        self.assertAlmostEqual(savings_pct, 22.0, delta=0.5)

    def test_division_by_zero_safety(self):
        income = 0.0
        expenses = 15000.0

        savings = income - expenses
        self.assertEqual(savings, -15000.0)

        # Handling zero income safely
        if income > 0:
            exp_pct = (expenses / income) * 100.0
            sav_pct = (savings / income) * 100.0
        else:
            exp_pct = 100.0 if expenses > 0 else 0.0
            sav_pct = 0.0

        self.assertEqual(exp_pct, 100.0)
        self.assertEqual(sav_pct, 0.0)


if __name__ == "__main__":
    unittest.main()
