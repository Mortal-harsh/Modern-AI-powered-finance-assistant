"""
Budget Management View.
Provides complete monthly overall and category budget allocation,
visual utilization progress bars, threshold warning badges, and PL/SQL integration.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional, List

from config.settings import ThemeColors, FontConfig
from services.budget_service import BudgetService
from services.transaction_service import TransactionService
from models.budget_model import Budget
from utils.formatters import format_inr, format_pct
from utils.validators import validate_amount, validate_threshold
from ui.components import CardFrame


class BudgetsView(tk.Frame):
    """Budget management and alert monitoring view."""

    def __init__(self, parent, on_navigate_callback=None, **kwargs):
        super().__init__(parent, bg=ThemeColors.BG_WINDOW, **kwargs)
        self.on_navigate_callback = on_navigate_callback

        self.budget_service = BudgetService()
        self.tx_service = TransactionService()

        # Filters
        self.selected_year = datetime.now().year
        self.selected_month = 1  # Jan default or current month

        self.budgets: List[Budget] = []

        self._build_ui()
        self.refresh_budgets()

    def _build_ui(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # -------------------------------------------------------------
        # 1. Header Toolbar
        # -------------------------------------------------------------
        header = tk.Frame(self, bg=ThemeColors.BG_WINDOW, padx=16, pady=12)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        title_lbl = tk.Label(
            header,
            text="Monthly Budget Planner",
            font=FontConfig.HEADER_LARGE,
            fg=ThemeColors.PRIMARY,
            bg=ThemeColors.BG_WINDOW
        )
        title_lbl.grid(row=0, column=0, sticky="w")

        btn_box = tk.Frame(header, bg=ThemeColors.BG_WINDOW)
        btn_box.grid(row=0, column=1, sticky="e")

        ttk.Button(
            btn_box,
            text="+ Set New Budget",
            style="Primary.TButton",
            command=self._open_set_budget_dialog
        ).pack(side="left", padx=4)

        ttk.Button(
            btn_box,
            text="Delete Selected",
            style="Secondary.TButton",
            command=self._delete_selected_budget
        ).pack(side="left", padx=4)

        # -------------------------------------------------------------
        # 2. Period Selector Bar
        # -------------------------------------------------------------
        filter_card = CardFrame(self)
        filter_card.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        fb = tk.Frame(filter_card.inner, bg=ThemeColors.BG_CARD, padx=14, pady=10)
        fb.pack(fill="x")

        tk.Label(fb, text="Select Year:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).pack(side="left", padx=(0, 4))
        self.year_var = tk.IntVar(value=self.selected_year)
        year_cb = ttk.Combobox(fb, textvariable=self.year_var, values=list(range(2020, 2026)), state="readonly", width=8)
        year_cb.pack(side="left", padx=(0, 16))
        year_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_budgets())

        tk.Label(fb, text="Select Month:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).pack(side="left", padx=(0, 4))
        months = ["1 - Jan", "2 - Feb", "3 - Mar", "4 - Apr", "5 - May", "6 - Jun",
                  "7 - Jul", "8 - Aug", "9 - Sep", "10 - Oct", "11 - Nov", "12 - Dec"]
        self.month_var = tk.StringVar(value="1 - Jan")
        month_cb = ttk.Combobox(fb, textvariable=self.month_var, values=months, state="readonly", width=12)
        month_cb.pack(side="left", padx=(0, 16))
        month_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_budgets())

        ttk.Button(fb, text="Refresh", style="Secondary.TButton", command=self.refresh_budgets).pack(side="left")

        # -------------------------------------------------------------
        # 3. Budgets Treeview Table
        # -------------------------------------------------------------
        table_card = CardFrame(self)
        table_card.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 12))
        table_card.inner.grid_rowconfigure(0, weight=1)
        table_card.inner.grid_columnconfigure(0, weight=1)

        columns = ("id", "scope", "budget", "spent", "remaining", "utilization", "threshold", "status")
        self.tree = ttk.Treeview(
            table_card.inner,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        self.tree.heading("id", text="# ID")
        self.tree.heading("scope", text="Budget Scope / Category")
        self.tree.heading("budget", text="Budget Allocated")
        self.tree.heading("spent", text="Actual Spending")
        self.tree.heading("remaining", text="Remaining")
        self.tree.heading("utilization", text="Utilization %")
        self.tree.heading("threshold", text="Alert Threshold")
        self.tree.heading("status", text="Alert Status")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("scope", width=220, anchor="w")
        self.tree.column("budget", width=130, anchor="e")
        self.tree.column("spent", width=130, anchor="e")
        self.tree.column("remaining", width=130, anchor="e")
        self.tree.column("utilization", width=110, anchor="center")
        self.tree.column("threshold", width=110, anchor="center")
        self.tree.column("status", width=110, anchor="center")

        v_scroll = ttk.Scrollbar(table_card.inner, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")

        # Tag styles for alerts
        self.tree.tag_configure("OK", foreground="#059669")
        self.tree.tag_configure("WARNING", foreground="#D97706")
        self.tree.tag_configure("EXCEEDED", foreground="#DC2626")

        # -------------------------------------------------------------
        # 4. Status Bar
        # -------------------------------------------------------------
        status_bar = tk.Frame(self, bg=ThemeColors.BG_WINDOW, padx=16, pady=4)
        status_bar.grid(row=3, column=0, sticky="ew")

        self.status_lbl = tk.Label(
            status_bar,
            text="",
            font=FontConfig.BODY_SMALL,
            fg=ThemeColors.TEXT_MUTED,
            bg=ThemeColors.BG_WINDOW
        )
        self.status_lbl.pack(side="left")

    def refresh_budgets(self):
        """Fetches budget data via PL/SQL procedure GET_BUDGET_STATUS."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        year = self.year_var.get()
        month_str = self.month_var.get()
        month = int(month_str.split(" - ")[0])

        self.budgets = self.budget_service.get_budget_status(year=year, month=month)

        warning_count = 0
        exceeded_count = 0

        for b in self.budgets:
            tag = b.alert_status
            if tag == "WARNING":
                warning_count += 1
            elif tag == "EXCEEDED":
                exceeded_count += 1

            self.tree.insert(
                "",
                "end",
                iid=str(b.budget_id),
                values=(
                    b.budget_id,
                    b.category_name,
                    format_inr(b.budget_amount),
                    format_inr(b.actual_spending),
                    format_inr(b.remaining_budget),
                    format_pct(b.utilization_pct),
                    f"{b.alert_threshold}%",
                    f"● {b.alert_status}"
                ),
                tags=(tag,)
            )

        status_text = f"Total Budgets Configured: {len(self.budgets)}"
        if exceeded_count > 0:
            status_text += f" | ⚠️ {exceeded_count} Budgets EXCEEDED!"
        if warning_count > 0:
            status_text += f" | ⚡ {warning_count} Warning Thresholds Reached"

        self.status_lbl.config(text=status_text)

    def _open_set_budget_dialog(self):
        """Opens dialog to set/edit a budget."""
        SetBudgetDialog(self, on_success=self.refresh_budgets)

    def _delete_selected_budget(self):
        """Deletes selected budget from database."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select a budget to delete.")
            return

        budget_id = int(selected[0])
        confirm = messagebox.askyesno("Confirm Delete", f"Delete budget #{budget_id} from database?")
        if confirm:
            ok, msg = self.budget_service.delete_budget(budget_id)
            if ok:
                messagebox.showinfo("Success", msg)
                self.refresh_budgets()
            else:
                messagebox.showerror("Error", msg)


class SetBudgetDialog(tk.Toplevel):
    """Dialog to create or update budget via PL/SQL SAVE_BUDGET."""

    def __init__(self, parent, on_success):
        super().__init__(parent)
        self.title("Set Budget")
        self.configure(bg=ThemeColors.BG_CARD)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.on_success = on_success
        self.budget_service = BudgetService()
        self.tx_service = TransactionService()

        self._build_form()
        self.geometry("440x400")

    def _build_form(self):
        tk.Label(self, text="Configure Monthly Budget", font=FontConfig.HEADER_MEDIUM, fg=ThemeColors.PRIMARY, bg=ThemeColors.BG_CARD).pack(anchor="w", padx=20, pady=14)

        container = tk.Frame(self, bg=ThemeColors.BG_CARD, padx=20)
        container.pack(fill="both", expand=True)

        grid_pad = {"padx": 10, "pady": 8}

        # Year
        tk.Label(container, text="Year:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=0, column=0, sticky="w", **grid_pad)
        self.year_var = tk.IntVar(value=datetime.now().year)
        ttk.Combobox(container, textvariable=self.year_var, values=list(range(2020, 2026)), state="readonly", width=12).grid(row=0, column=1, sticky="w", **grid_pad)

        # Month
        tk.Label(container, text="Month:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=1, column=0, sticky="w", **grid_pad)
        self.month_var = tk.IntVar(value=1)
        ttk.Combobox(container, textvariable=self.month_var, values=list(range(1, 13)), state="readonly", width=12).grid(row=1, column=1, sticky="w", **grid_pad)

        # Scope (Overall or Category)
        tk.Label(container, text="Scope:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=2, column=0, sticky="w", **grid_pad)
        self.cat_map = {"OVERALL MONTHLY BUDGET (All Categories)": None}
        for c in self.tx_service.get_categories(category_type="EXPENSE"):
            self.cat_map[c.category_name] = c.category_id

        self.scope_var = tk.StringVar(value="OVERALL MONTHLY BUDGET (All Categories)")
        ttk.Combobox(container, textvariable=self.scope_var, values=list(self.cat_map.keys()), state="readonly", width=28).grid(row=2, column=1, sticky="w", **grid_pad)

        # Budget Amount
        tk.Label(container, text="Budget Amount (₹):", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=3, column=0, sticky="w", **grid_pad)
        self.amt_var = tk.StringVar()
        ttk.Entry(container, textvariable=self.amt_var, width=16).grid(row=3, column=1, sticky="w", **grid_pad)

        # Alert Threshold %
        tk.Label(container, text="Alert Threshold (%):", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=4, column=0, sticky="w", **grid_pad)
        self.thresh_var = tk.StringVar(value="80")
        ttk.Entry(container, textvariable=self.thresh_var, width=10).grid(row=4, column=1, sticky="w", **grid_pad)

        # Buttons
        btn_box = tk.Frame(self, bg=ThemeColors.BG_CARD)
        btn_box.pack(fill="x", padx=20, pady=16)

        ttk.Button(btn_box, text="Save Budget", style="Primary.TButton", command=self._save).pack(side="right", padx=6)
        ttk.Button(btn_box, text="Cancel", style="Secondary.TButton", command=self.destroy).pack(side="right")

    def _save(self):
        amt_ok, amount, err_amt = validate_amount(self.amt_var.get())
        if not amt_ok:
            messagebox.showerror("Validation Error", err_amt, parent=self)
            return

        thr_ok, threshold, err_thr = validate_threshold(self.thresh_var.get())
        if not thr_ok:
            messagebox.showerror("Validation Error", err_thr, parent=self)
            return

        cat_id = self.cat_map.get(self.scope_var.get())
        year = self.year_var.get()
        month = self.month_var.get()

        # Call PL/SQL procedure SAVE_BUDGET
        ok, b_id, msg = self.budget_service.save_budget(
            month=month,
            year=year,
            amount=amount,
            category_id=cat_id,
            alert_threshold=threshold
        )

        if ok:
            messagebox.showinfo("Success", f"Budget #{b_id} saved successfully in Oracle Database!", parent=self)
            if self.on_success:
                self.on_success()
            self.destroy()
        else:
            messagebox.showerror("Database Error", msg, parent=self)
