"""
Reusable UI Components for Smart Expense Tracker.
Includes rounded-style card containers, KPI metric cards, pill toggle bars,
and filter popup selectors matching the reference dashboard.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Optional
from config.settings import ThemeColors, FontConfig


class CardFrame(tk.Frame):
    """
    White card container frame with subtle border and padding,
    resembling modern SaaS/dashboard card widgets.
    """
    def __init__(self, parent, bg: str = ThemeColors.BG_CARD, border_color: str = ThemeColors.BORDER_SUBTLE, **kwargs):
        super().__init__(
            parent,
            bg=border_color,
            bd=1,
            relief="solid",
            **kwargs
        )
        self.inner = tk.Frame(self, bg=bg)
        self.inner.pack(fill="both", expand=True, padx=1, pady=1)


class StatCard(CardFrame):
    """
    Stat summary card matching reference UI 2x2 grid.
    Displays big metric (e.g. ₹710K, 78%) and descriptive label underneath.
    """
    def __init__(self, parent, title: str = "", value: str = "₹0", **kwargs):
        super().__init__(parent, **kwargs)

        self.container = tk.Frame(self.inner, bg=ThemeColors.BG_CARD, padx=18, pady=16)
        self.container.pack(fill="both", expand=True)

        self.val_label = tk.Label(
            self.container,
            text=value,
            font=FontConfig.METRIC_LARGE,
            fg=ThemeColors.TEXT_MAIN,
            bg=ThemeColors.BG_CARD
        )
        self.val_label.pack(anchor="center", pady=(4, 2))

        self.title_label = tk.Label(
            self.container,
            text=title,
            font=FontConfig.METRIC_LABEL,
            fg=ThemeColors.TEXT_MUTED,
            bg=ThemeColors.BG_CARD
        )
        self.title_label.pack(anchor="center", pady=(0, 4))

    def update_value(self, value: str):
        self.val_label.config(text=value)


class PillButton(tk.Button):
    """Rounded-style pill button with active purple state."""
    def __init__(self, parent, text: str, command: Optional[Callable] = None, is_active: bool = False, **kwargs):
        self.is_active = is_active
        self._custom_command = command
        bg_col = ThemeColors.PRIMARY if is_active else ThemeColors.BG_MUTED
        fg_col = ThemeColors.TEXT_ON_PRIMARY if is_active else ThemeColors.TEXT_MUTED

        super().__init__(
            parent,
            text=text,
            command=self._on_click,
            bg=bg_col,
            fg=fg_col,
            activebackground=ThemeColors.PRIMARY_HOVER if is_active else "#E2E8F0",
            activeforeground=ThemeColors.TEXT_ON_PRIMARY if is_active else ThemeColors.TEXT_MAIN,
            font=(FontConfig.FAMILY, 9, "bold" if is_active else "normal"),
            bd=0,
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
            **kwargs
        )

    def _on_click(self):
        if self._custom_command:
            self._custom_command()

    def set_active(self, active: bool):
        self.is_active = active
        bg_col = ThemeColors.PRIMARY if active else ThemeColors.BG_MUTED
        fg_col = ThemeColors.TEXT_ON_PRIMARY if active else ThemeColors.TEXT_MUTED
        self.config(
            bg=bg_col,
            fg=fg_col,
            font=(FontConfig.FAMILY, 9, "bold" if active else "normal"),
            activebackground=ThemeColors.PRIMARY_HOVER if active else "#E2E8F0",
            activeforeground=ThemeColors.TEXT_ON_PRIMARY if active else ThemeColors.TEXT_MAIN
        )


class YearPillSelector(tk.Frame):
    """
    Horizontal year pill selector matching the header in reference image:
    ['Select all', '2017', '2018', ... '2024']
    """
    def __init__(self, parent, years: List[int], on_year_changed: Callable[[Optional[int]], None], **kwargs):
        super().__init__(parent, bg=ThemeColors.BG_WINDOW, **kwargs)
        self.on_year_changed = on_year_changed
        self.years = years
        self.selected_year: Optional[int] = 2024 if 2024 in years else (years[0] if years else None)
        self.buttons: List[PillButton] = []

        self._build_pills()

    def _build_pills(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.buttons.clear()

        # Label "Year"
        lbl = tk.Label(self, text="Year", font=(FontConfig.FAMILY, 10, "bold"), fg=ThemeColors.TEXT_MAIN, bg=ThemeColors.BG_WINDOW)
        lbl.pack(side="top", anchor="center", pady=(0, 4))

        pills_bar = tk.Frame(self, bg=ThemeColors.BG_WINDOW)
        pills_bar.pack(side="top", anchor="center")

        # 'Select all' pill
        all_btn = PillButton(
            pills_bar,
            text="Select all",
            command=lambda: self._select_year(None),
            is_active=(self.selected_year is None)
        )
        all_btn.pack(side="left", padx=2)
        self.buttons.append(all_btn)

        # Year pills (e.g. 2017 to 2024 or database years in ascending display order)
        disp_years = sorted(self.years)
        for y in disp_years:
            btn = PillButton(
                pills_bar,
                text=str(y),
                command=lambda year_val=y: self._select_year(year_val),
                is_active=(self.selected_year == y)
            )
            btn.pack(side="left", padx=2)
            self.buttons.append(btn)

    def _select_year(self, year: Optional[int]):
        self.selected_year = year
        for btn in self.buttons:
            text = btn.cget("text")
            is_active = (text == "Select all" and year is None) or (text == str(year))
            btn.set_active(is_active)
        if self.on_year_changed:
            self.on_year_changed(self.selected_year)


class MonthGridSelector(tk.Toplevel):
    """
    Month grid popup (Jan - Dec) matching the popup card from the screenshot.
    """
    def __init__(self, parent, current_month: Optional[int], on_month_selected: Callable[[Optional[int]], None]):
        super().__init__(parent)
        self.title("Select Month")
        self.configure(bg=ThemeColors.BG_CARD)
        self.resizable(False, False)
        self.transient(parent)
        self.on_month_selected = on_month_selected
        self.current_month = current_month

        # Month buttons grid
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        header = tk.Label(self, text="Filter by Month", font=FontConfig.HEADER_SMALL, fg=ThemeColors.PRIMARY, bg=ThemeColors.BG_CARD)
        header.grid(row=0, column=0, columnspan=3, pady=(12, 8))

        row, col = 1, 0
        for i, m in enumerate(months, start=1):
            is_sel = (self.current_month == i)
            btn = tk.Button(
                self,
                text=m,
                font=(FontConfig.FAMILY, 9, "bold" if is_sel else "normal"),
                bg=ThemeColors.PRIMARY if is_sel else ThemeColors.BG_MUTED,
                fg=ThemeColors.TEXT_ON_PRIMARY if is_sel else ThemeColors.TEXT_MAIN,
                bd=0,
                padx=14,
                pady=8,
                cursor="hand2",
                command=lambda m_idx=i: self._select(m_idx)
            )
            btn.grid(row=row, column=col, padx=6, pady=6)
            col += 1
            if col == 3:
                col = 0
                row += 1

        # Clear month filter button
        clear_btn = tk.Button(
            self,
            text="All Months",
            font=(FontConfig.FAMILY, 9, "bold"),
            bg=ThemeColors.PRIMARY_LIGHT,
            fg=ThemeColors.PRIMARY,
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=lambda: self._select(None)
        )
        clear_btn.grid(row=row, column=0, columnspan=3, pady=(8, 12))

        # Center over parent
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 80, parent.winfo_rooty() + 100))

    def _select(self, month: Optional[int]):
        self.on_month_selected(month)
        self.destroy()
