"""
Input Validation Utilities.
Provides strict validations for transaction amounts, dates, required fields,
and budget thresholds.
"""

from datetime import datetime, date
from typing import Tuple, Optional


def validate_amount(raw_val: str) -> Tuple[bool, float, str]:
    """
    Validates monetary input. Must be a numeric string strictly > 0.
    Returns: (is_valid, parsed_float, error_message)
    """
    if not raw_val or not raw_val.strip():
        return False, 0.0, "Amount cannot be empty."

    # Strip currency symbol and commas if present
    cleaned = raw_val.strip().replace("₹", "").replace(",", "").strip()

    try:
        val = float(cleaned)
    except ValueError:
        return False, 0.0, "Amount must be a valid numeric figure (e.g. 1500.50)."

    if val <= 0:
        return False, 0.0, "Amount must be strictly greater than zero."

    if val > 999_999_999.99:
        return False, 0.0, "Amount exceeds maximum allowable limit."

    return True, round(val, 2), ""


def validate_date(raw_val: str) -> Tuple[bool, Optional[date], str]:
    """
    Validates date string in YYYY-MM-DD or DD-MM-YYYY format.
    Returns: (is_valid, parsed_date, error_message)
    """
    if not raw_val or not raw_val.strip():
        return False, None, "Date cannot be empty."

    cleaned = raw_val.strip()
    formats = ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%d-%b-%Y"]

    for fmt in formats:
        try:
            d = datetime.strptime(cleaned, fmt).date()
            if d.year < 2000 or d.year > 2100:
                return False, None, "Year must be between 2000 and 2100."
            return True, d, ""
        except ValueError:
            continue

    return False, None, "Invalid date format. Please use YYYY-MM-DD or DD-MM-YYYY."


def validate_required_text(raw_val: str, field_name: str, min_len: int = 1, max_len: int = 255) -> Tuple[bool, str, str]:
    """Validates that a string is non-empty and within bounds."""
    if not raw_val or not raw_val.strip():
        return False, "", f"{field_name} is required."
    cleaned = raw_val.strip()
    if len(cleaned) < min_len:
        return False, "", f"{field_name} must have at least {min_len} characters."
    if len(cleaned) > max_len:
        return False, "", f"{field_name} cannot exceed {max_len} characters."
    return True, cleaned, ""


def validate_threshold(raw_val: str) -> Tuple[bool, int, str]:
    """Validates budget alert threshold (1 to 100)."""
    if not raw_val or not raw_val.strip():
        return True, 80, ""  # Default 80%
    try:
        val = int(raw_val.strip().replace("%", ""))
        if 1 <= val <= 100:
            return True, val, ""
        return False, 80, "Alert threshold must be an integer between 1 and 100%."
    except ValueError:
        return False, 80, "Alert threshold must be an integer (e.g. 80)."
