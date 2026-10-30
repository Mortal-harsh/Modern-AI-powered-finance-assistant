"""
Formatting Utilities for Smart Expense Tracker.
Formats currency in Indian Rupees (₹) with Indian number formatting (lakhs/crores),
compact metrics for dashboard display, and clean date presentations.
"""

from datetime import date, datetime
from typing import Union


def format_inr(amount: Union[float, int, None], include_symbol: bool = True) -> str:
    """
    Formats a numeric amount in the Indian currency numbering format.
    Example: 312719 -> ₹3,12,719.00 or ₹3,12,719
    """
    if amount is None:
        amount = 0.0

    try:
        val = float(amount)
    except (ValueError, TypeError):
        return "₹0" if include_symbol else "0"

    is_negative = val < 0
    val = abs(val)

    # Separate integer and decimal part
    int_part = int(round(val))
    decimal_part = f"{(val - int_part):.2f}"[2:] if (val - int_part) >= 0.005 else ""

    s = str(int_part)
    if len(s) <= 3:
        formatted_int = s
    else:
        # Last 3 digits
        last_three = s[-3:]
        remaining = s[:-3]
        # Group remaining digits in pairs
        groups = []
        while len(remaining) > 2:
            groups.append(remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.append(remaining)
        groups.reverse()
        formatted_int = ",".join(groups) + "," + last_three

    result = formatted_int
    if decimal_part and decimal_part != "00":
        result = f"{formatted_int}.{decimal_part}"

    if is_negative:
        return f"-₹{result}" if include_symbol else f"-{result}"

    return f"₹{result}" if include_symbol else result


def format_compact_inr(amount: Union[float, int, None]) -> str:
    """
    Formats large currency amounts into compact dashboard badge format.
    Matches the reference screenshot (e.g. ₹710K, ₹553K, ₹1.2M).
    """
    if amount is None:
        return "₹0"

    try:
        val = float(amount)
    except (ValueError, TypeError):
        return "₹0"

    is_negative = val < 0
    val = abs(val)

    if val >= 10_000_000:  # 1 Crore+
        s = f"{val / 10_000_000:.1f}Cr".replace(".0Cr", "Cr")
    elif val >= 100_000:   # 1 Lakh+
        # In the reference UI, 710000 is displayed as ₹710K
        s = f"{val / 1_000:.0f}K"
    elif val >= 1_000:
        s = f"{val / 1_000:.0f}K"
    else:
        s = f"{val:.0f}"

    prefix = "-₹" if is_negative else "₹"
    return f"{prefix}{s}"


def format_pct(value: Union[float, int, None], decimals: int = 0) -> str:
    """Formats percentage safely (e.g. 78%)."""
    if value is None:
        return "0%"
    try:
        val = float(value)
        if decimals == 0:
            return f"{int(round(val))}%"
        return f"{val:.{decimals}f}%"
    except (ValueError, TypeError):
        return "0%"


def format_date_display(dt: Union[date, datetime, str, None]) -> str:
    """Formats a date object or ISO string to 'DD-Mon-YYYY' display."""
    if not dt:
        return ""
    if isinstance(dt, str):
        try:
            dt = datetime.strptime(dt[:10], "%Y-%m-%d").date()
        except Exception:
            return dt[:10]
    return dt.strftime("%d-%b-%Y")
