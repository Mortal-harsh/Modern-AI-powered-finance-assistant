"""
Script to generate clean navigation icons using Pillow.
Produces purple-themed minimalist UI icons for the vertical sidebar.
"""

from pathlib import Path
from PIL import Image, ImageDraw

ICONS_DIR = Path(__file__).resolve().parent / "icons"
ICONS_DIR.mkdir(parents=True, exist_ok=True)

SIZE = 36
PURPLE = (124, 92, 252, 255)
LIGHT_PURPLE = (237, 233, 254, 255)
CYAN_ACCENT = (14, 165, 233, 255)


def make_dashboard_icon():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # House / Home roof and body
    # Roof
    d.polygon([(18, 6), (8, 16), (28, 16)], fill=PURPLE)
    # Base
    d.rounded_rectangle([10, 16, 26, 29], radius=2, fill=PURPLE)
    # Door
    d.rounded_rectangle([15, 20, 21, 29], radius=1, fill=(255, 255, 255, 255))
    img.save(ICONS_DIR / "dashboard.png")


def make_transactions_icon():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Calendar body
    d.rounded_rectangle([7, 8, 29, 29], radius=4, outline=CYAN_ACCENT, width=2)
    d.line([7, 14, 29, 14], fill=CYAN_ACCENT, width=2)
    # Calendar rings
    d.rectangle([11, 5, 13, 8], fill=CYAN_ACCENT)
    d.rectangle([23, 5, 25, 8], fill=CYAN_ACCENT)
    # Grid dots
    d.ellipse([11, 18, 14, 21], fill=CYAN_ACCENT)
    d.ellipse([17, 18, 20, 21], fill=CYAN_ACCENT)
    d.ellipse([23, 18, 26, 21], fill=CYAN_ACCENT)
    d.ellipse([11, 23, 14, 26], fill=CYAN_ACCENT)
    d.ellipse([17, 23, 20, 26], fill=CYAN_ACCENT)
    img.save(ICONS_DIR / "transactions.png")


def make_add_expense_icon():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Circle with minus / down arrow
    d.ellipse([5, 5, 31, 31], fill=PURPLE)
    d.rectangle([11, 16, 25, 20], fill=(255, 255, 255, 255))
    img.save(ICONS_DIR / "add_expense.png")


def make_add_income_icon():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Circle with plus
    d.ellipse([5, 5, 31, 31], fill=(16, 185, 129, 255))
    d.rectangle([11, 16, 25, 20], fill=(255, 255, 255, 255))
    d.rectangle([16, 11, 20, 25], fill=(255, 255, 255, 255))
    img.save(ICONS_DIR / "add_income.png")


def make_budgets_icon():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Wallet / Safe shape
    d.rounded_rectangle([6, 9, 30, 27], radius=3, outline=PURPLE, width=2)
    d.rounded_rectangle([20, 15, 31, 21], radius=2, fill=PURPLE)
    d.ellipse([23, 17, 25, 19], fill=(255, 255, 255, 255))
    img.save(ICONS_DIR / "budgets.png")


def make_analytics_icon():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Three rising bar charts
    d.rounded_rectangle([7, 20, 12, 29], radius=1, fill=PURPLE)
    d.rounded_rectangle([15, 13, 20, 29], radius=1, fill=PURPLE)
    d.rounded_rectangle([23, 7, 28, 29], radius=1, fill=PURPLE)
    img.save(ICONS_DIR / "analytics.png")


def make_reports_icon():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Document with lines
    d.rounded_rectangle([8, 6, 28, 30], radius=2, outline=PURPLE, width=2)
    d.line([13, 12, 23, 12], fill=PURPLE, width=2)
    d.line([13, 17, 23, 17], fill=PURPLE, width=2)
    d.line([13, 22, 19, 22], fill=PURPLE, width=2)
    img.save(ICONS_DIR / "reports.png")


def make_settings_icon():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Gear
    d.ellipse([9, 9, 27, 27], outline=PURPLE, width=3)
    d.ellipse([15, 15, 21, 21], fill=PURPLE)
    # Teeth
    d.rectangle([16, 5, 20, 9], fill=PURPLE)
    d.rectangle([16, 27, 20, 31], fill=PURPLE)
    d.rectangle([5, 16, 9, 20], fill=PURPLE)
    d.rectangle([27, 16, 31, 20], fill=PURPLE)
    img.save(ICONS_DIR / "settings.png")


if __name__ == "__main__":
    make_dashboard_icon()
    make_transactions_icon()
    make_add_expense_icon()
    make_add_income_icon()
    make_budgets_icon()
    make_analytics_icon()
    make_reports_icon()
    make_settings_icon()
    print("All icons successfully generated in assets/icons/!")
