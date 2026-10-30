"""
Unit Tests for Input Validators.
"""

import unittest
from datetime import date
from utils.validators import validate_amount, validate_date, validate_required_text, validate_threshold


class TestValidators(unittest.TestCase):

    def test_valid_amounts(self):
        ok, val, err = validate_amount("1500")
        self.assertTrue(ok)
        self.assertEqual(val, 1500.0)

        ok, val, err = validate_amount("₹ 3,12,719.50")
        self.assertTrue(ok)
        self.assertEqual(val, 312719.50)

    def test_invalid_amounts(self):
        # Zero
        ok, val, err = validate_amount("0")
        self.assertFalse(ok)
        self.assertIn("greater than zero", err)

        # Negative
        ok, val, err = validate_amount("-500")
        self.assertFalse(ok)
        self.assertIn("greater than zero", err)

        # Non-numeric
        ok, val, err = validate_amount("abc")
        self.assertFalse(ok)

        # Empty
        ok, val, err = validate_amount("")
        self.assertFalse(ok)

    def test_valid_dates(self):
        ok, d, err = validate_date("2024-05-15")
        self.assertTrue(ok)
        self.assertEqual(d, date(2024, 5, 15))

        ok, d, err = validate_date("15-05-2024")
        self.assertTrue(ok)
        self.assertEqual(d, date(2024, 5, 15))

    def test_invalid_dates(self):
        ok, d, err = validate_date("not-a-date")
        self.assertFalse(ok)

        ok, d, err = validate_date("")
        self.assertFalse(ok)

        # Out of bounds year
        ok, d, err = validate_date("1995-01-01")
        self.assertFalse(ok)

    def test_required_text(self):
        ok, txt, err = validate_required_text("Grocery Shopping", "Description")
        self.assertTrue(ok)
        self.assertEqual(txt, "Grocery Shopping")

        ok, txt, err = validate_required_text("   ", "Description")
        self.assertFalse(ok)

    def test_threshold(self):
        ok, val, err = validate_threshold("85")
        self.assertTrue(ok)
        self.assertEqual(val, 85)

        ok, val, err = validate_threshold("120")
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
