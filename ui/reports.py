"""
Reports and Export View.
Provides comprehensive financial statements, monthly/yearly summaries,
one-click CSV spreadsheet generation, and professional PDF report exports via ReportLab.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from typing import Optional

from config.settings import ThemeColors, FontConfig
from services.transaction_service import TransactionService
from services.budget_service import BudgetService
from services.analytics_service import AnalyticsService
from services.report_service import ReportService
from utils.formatters import format_inr, format_pct
from ui.components import CardFrame


class ReportsView(tk.Frame):
    """Reports generation and export view."""

    def __init__(self, parent, on_navigate_callback=None, **kwargs):
        super().__init__(parent, bg=ThemeColors.BG_WINDOW, **kwargs)
        self.on_navigate_callback = on_navigate_callback

        self.tx_service = TransactionService()
        self.budget_service = BudgetService()
        self.analytics_service = AnalyticsService()
        self.report_service = ReportService()

        self.selected_year = 2024
        self.selected_month = None

        self._build_ui()
        self.refresh_report_data()

    def _build_ui(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # -------------------------------------------------------------
        # 1. Header Toolbar & Action Buttons
        # -------------------------------------------------------------
        header = tk.Frame(self, bg=ThemeColors.BG_WINDOW, padx=16, pady=12)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        title = tk.Label(
            header,
            text="Financial Reports & Statements",
            font=FontConfig.HEADER_LARGE,
            fg=ThemeColors.PRIMARY,
            bg=ThemeColors.BG_WINDOW
        )
        title.grid(row=0, column=0, sticky="w")

        btn_box = tk.Frame(header, bg=ThemeColors.BG_WINDOW)
        btn_box.grid(row=0, column=1, sticky="e")

        ttk.Button(
            btn_box,
            text="📄 Export PDF Report",
            style="Primary.TButton",
            command=self._export_pdf
        ).pack(side="left", padx=4)

        ttk.Button(
            btn_box,
            text="📊 Export CSV Data",
            style="Secondary.TButton",
            command=self._export_csv
        ).pack(side="left", padx=4)

        # -------------------------------------------------------------
        # 2. Scope Filter Toolbar
        # -------------------------------------------------------------
        filter_card = CardFrame(self)
        filter_card.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        fb = tk.Frame(filter_card.inner, bg=ThemeColors.BG_CARD, padx=14, pady=10)
        fb.pack(fill="x")

        tk.Label(fb, text="Select Year:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).pack(side="left", padx=(0, 4))
        self.year_var = tk.IntVar(value=self.selected_year)
        years = self.tx_service.get_available_years()
        year_cb = ttk.Combobox(fb, textvariable=self.year_var, values=years, state="readonly", width=8)
        year_cb.pack(side="left", padx=(0, 16))
        year_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_report_data())

        tk.Label(fb, text="Select Month:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).pack(side="left", padx=(0, 4))
        months = ["All Months", "1 - Jan", "2 - Feb", "3 - Mar", "4 - Apr", "5 - May", "6 - Jun",
                  "7 - Jul", "8 - Aug", "9 - Sep", "10 - Oct", "11 - Nov", "12 - Dec"]
        self.month_var = tk.StringVar(value="All Months")
        month_cb = ttk.Combobox(fb, textvariable=self.month_var, values=months, state="readonly", width=12)
        month_cb.pack(side="left", padx=(0, 16))
        month_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_report_data())

        ttk.Button(fb, text="Generate Statement", style="Secondary.TButton", command=self.refresh_report_data).pack(side="left")

        # -------------------------------------------------------------
        # 3. Report Content Panels (Monthly Summary & Category Breakdown)
        # -------------------------------------------------------------
        content_frame = tk.Frame(self, bg=ThemeColors.BG_WINDOW, padx=16, pady=4)
        content_frame.grid(row=2, column=0, sticky="nsew")
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=6)
        content_frame.grid_columnconfigure(1, weight=4)

        # Left: 12-Month Summary Table
        left_card = CardFrame(content_frame)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left_card.inner.grid_rowconfigure(1, weight=1)
        left_card.inner.grid_columnconfigure(0, weight=1)

        tk.Label(
            left_card.inner,
            text="Monthly Financial Summary Statement",
            font=FontConfig.HEADER_SMALL,
            fg=ThemeColors.TEXT_MAIN,
            bg=ThemeColors.BG_CARD,
            padx=14,
            pady=10
        ).grid(row=0, column=0, sticky="w")

        m_cols = ("month", "income", "expenses", "savings", "savings_rate")
        self.monthly_tree = ttk.Treeview(left_card.inner, columns=m_cols, show="headings", height=12)
        self.monthly_tree.heading("month", text="Month")
        self.monthly_tree.heading("income", text="Total Income")
        self.monthly_tree.heading("expenses", text="Total Expenses")
        self.monthly_tree.heading("savings", text="Net Savings")
        self.monthly_tree.heading("savings_rate", text="Savings Rate %")

        self.monthly_tree.column("month", width=80, anchor="center")
        self.monthly_tree.column("income", width=120, anchor="e")
        self.monthly_tree.column("expenses", width=120, anchor="e")
        self.monthly_tree.column("savings", width=120, anchor="e")
        self.monthly_tree.column("savings_rate", width=100, anchor="center")

        self.monthly_tree.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        # Right: Category Breakdown Table
        right_card = CardFrame(content_frame)
        right_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right_card.inner.grid_rowconfigure(1, weight=1)
        right_card.inner.grid_columnconfigure(0, weight=1)

        tk.Label(
            right_card.inner,
            text="Category Spending Share",
            font=FontConfig.HEADER_SMALL,
            fg=ThemeColors.TEXT_MAIN,
            bg=ThemeColors.BG_CARD,
            padx=14,
            pady=10
        ).grid(row=0, column=0, sticky="w")

        c_cols = ("category", "amount", "share")
        self.cat_tree = ttk.Treeview(right_card.inner, columns=c_cols, show="headings", height=12)
        self.cat_tree.heading("category", text="Category")
        self.cat_tree.heading("amount", text="Amount (₹)")
        self.cat_tree.heading("share", text="Share %")

        self.cat_tree.column("category", width=140, anchor="w")
        self.cat_tree.column("amount", width=100, anchor="e")
        self.cat_tree.column("share", width=70, anchor="center")

        self.cat_tree.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

    def refresh_report_data(self):
        """Loads statement data from PL/SQL and Pandas aggregations."""
        year = self.year_var.get()
        m_str = self.month_var.get()
        month = None if m_str == "All Months" else int(m_str.split(" - ")[0])

        # 1. Populate Monthly Table
        for item in self.monthly_tree.get_children():
            self.monthly_tree.delete(item)

        monthly_df = self.analytics_service.get_monthly_trend_analysis(year=year)
        for _, row in monthly_df.iterrows():
            inc = row["INCOME"]
            exp = row["EXPENSES"]
            sav = row["SAVINGS"]
            sav_rate = (sav / inc * 100) if inc > 0 else 0.0

            self.monthly_tree.insert(
                "",
                "end",
                values=(
                    row["MONTH_NAME"],
                    format_inr(inc),
                    format_inr(exp),
                    format_inr(sav),
                    format_pct(sav_rate)
                )
            )

        # 2. Populate Category Table
        for item in self.cat_tree.get_children():
            self.cat_tree.delete(item)

        cat_df = self.analytics_service.get_category_distribution(year=year, month=month)
        for _, row in cat_df.iterrows():
            self.cat_tree.insert(
                "",
                "end",
                values=(
                    row["CATEGORY_NAME"],
                    format_inr(row["AMOUNT"]),
                    f"{row['SHARE_PCT']}%"
                )
            )

    def _export_csv(self):
        year = self.year_var.get()
        m_str = self.month_var.get()
        month = None if m_str == "All Months" else int(m_str.split(" - ")[0])

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Spreadsheet", "*.csv")],
            initialfile=f"financial_report_{year}.csv"
        )
        if file_path:
            ok, msg = self.report_service.export_transactions_csv(file_path, year=year, month=month)
            if ok:
                messagebox.showinfo("Success", msg)
            else:
                messagebox.showerror("Error", msg)

    def _export_pdf(self):
        year = self.year_var.get()
        m_str = self.month_var.get()
        month = None if m_str == "All Months" else int(m_str.split(" - ")[0])

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Document", "*.pdf")],
            initialfile=f"expense_statement_{year}.pdf"
        )
        if file_path:
            ok, msg = self.report_service.export_pdf_report(file_path, year=year, month=month)
            if ok:
                messagebox.showinfo("Success", msg)
            else:
                messagebox.showerror("Error", msg)
