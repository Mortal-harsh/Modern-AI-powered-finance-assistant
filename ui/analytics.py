"""
Analytics View.
Advanced visual analytics using Pandas, NumPy, and Matplotlib:
- 12-Month Grouped Bar Chart: Income vs Expenses
- Spending Trend & 3-Month Moving Average
- Category Spending Horizontal Bar Chart
- Summary Financial Statistics Cards (Top Category, Average Monthly Expense, Peak Month)
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from config.settings import ThemeColors, FontConfig
from services.analytics_service import AnalyticsService
from services.transaction_service import TransactionService
from utils.formatters import format_inr, format_compact_inr, format_pct
from ui.components import CardFrame, StatCard


class AnalyticsView(tk.Frame):
    """Deep analytics and data science visualization view."""

    def __init__(self, parent, on_navigate_callback=None, **kwargs):
        super().__init__(parent, bg=ThemeColors.BG_WINDOW, **kwargs)
        self.on_navigate_callback = on_navigate_callback

        self.analytics_service = AnalyticsService()
        self.tx_service = TransactionService()

        self.selected_year = 2024

        self._build_ui()
        self.refresh_analytics()

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

        title = tk.Label(
            header,
            text="Financial Analytics & Trends",
            font=FontConfig.HEADER_LARGE,
            fg=ThemeColors.PRIMARY,
            bg=ThemeColors.BG_WINDOW
        )
        title.grid(row=0, column=0, sticky="w")

        filter_box = tk.Frame(header, bg=ThemeColors.BG_WINDOW)
        filter_box.grid(row=0, column=1, sticky="e")

        tk.Label(filter_box, text="Year:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_WINDOW).pack(side="left", padx=(0, 4))
        self.year_var = tk.IntVar(value=self.selected_year)
        years = self.tx_service.get_available_years()
        year_cb = ttk.Combobox(filter_box, textvariable=self.year_var, values=years, state="readonly", width=8)
        year_cb.pack(side="left", padx=(0, 8))
        year_cb.bind("<<ComboboxSelected>>", lambda e: self._on_year_changed())

        ttk.Button(filter_box, text="Refresh", style="Secondary.TButton", command=self.refresh_analytics).pack(side="left")

        # -------------------------------------------------------------
        # 2. Key Statistical Insights Cards (Row 1)
        # -------------------------------------------------------------
        stat_bar = tk.Frame(self, bg=ThemeColors.BG_WINDOW, padx=16, pady=4)
        stat_bar.grid(row=1, column=0, sticky="ew")
        for i in range(4):
            stat_bar.grid_columnconfigure(i, weight=1)

        self.card_top_cat = StatCard(stat_bar, title="Highest Spending Category", value="-")
        self.card_top_cat.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.card_avg_monthly = StatCard(stat_bar, title="Avg Monthly Expenses", value="₹0")
        self.card_avg_monthly.grid(row=0, column=1, sticky="nsew", padx=6)

        self.card_peak_month = StatCard(stat_bar, title="Peak Spending Month", value="-")
        self.card_peak_month.grid(row=0, column=2, sticky="nsew", padx=6)

        self.card_median_tx = StatCard(stat_bar, title="Median Transaction", value="₹0")
        self.card_median_tx.grid(row=0, column=3, sticky="nsew", padx=(6, 0))

        # -------------------------------------------------------------
        # 3. Analytics Charts Grid (Row 2)
        # -------------------------------------------------------------
        charts_grid = tk.Frame(self, bg=ThemeColors.BG_WINDOW, padx=16, pady=8)
        charts_grid.grid(row=2, column=0, sticky="nsew")
        charts_grid.grid_rowconfigure(0, weight=1)
        charts_grid.grid_columnconfigure(0, weight=6)  # Left: Bar chart (Income vs Expenses)
        charts_grid.grid_columnconfigure(1, weight=4)  # Right: Category Horizontal Bars

        # Chart 1: Income vs Expenses (Grouped Bar Chart)
        card_bar = CardFrame(charts_grid)
        card_bar.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        card_bar.inner.grid_rowconfigure(1, weight=1)
        card_bar.inner.grid_columnconfigure(0, weight=1)

        tk.Label(
            card_bar.inner,
            text="Monthly Income vs Expenses Comparison",
            font=FontConfig.HEADER_SMALL,
            fg=ThemeColors.TEXT_MAIN,
            bg=ThemeColors.BG_CARD,
            padx=14,
            pady=10
        ).grid(row=0, column=0, sticky="w")

        bar_frame = tk.Frame(card_bar.inner, bg=ThemeColors.BG_CARD)
        bar_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        self.fig_bar = Figure(figsize=(5.5, 3.2), dpi=100)
        self.fig_bar.patch.set_facecolor(ThemeColors.BG_CARD)
        self.canvas_bar = FigureCanvasTkAgg(self.fig_bar, master=bar_frame)
        self.canvas_bar.get_tk_widget().pack(fill="both", expand=True)

        # Chart 2: Category Breakdown Horizontal Bar Chart
        card_cat = CardFrame(charts_grid)
        card_cat.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        card_cat.inner.grid_rowconfigure(1, weight=1)
        card_cat.inner.grid_columnconfigure(0, weight=1)

        tk.Label(
            card_cat.inner,
            text="Category Spending Distribution",
            font=FontConfig.HEADER_SMALL,
            fg=ThemeColors.TEXT_MAIN,
            bg=ThemeColors.BG_CARD,
            padx=14,
            pady=10
        ).grid(row=0, column=0, sticky="w")

        cat_frame = tk.Frame(card_cat.inner, bg=ThemeColors.BG_CARD)
        cat_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        self.fig_cat = Figure(figsize=(4.0, 3.2), dpi=100)
        self.fig_cat.patch.set_facecolor(ThemeColors.BG_CARD)
        self.canvas_cat = FigureCanvasTkAgg(self.fig_cat, master=cat_frame)
        self.canvas_cat.get_tk_widget().pack(fill="both", expand=True)

    def _on_year_changed(self):
        self.selected_year = self.year_var.get()
        self.refresh_analytics()

    def refresh_analytics(self):
        """Re-computes aggregations via Pandas & NumPy and renders charts."""
        # 1. Statistical Insights
        stats = self.analytics_service.get_statistical_insights(year=self.selected_year)
        self.card_top_cat.update_value(str(stats["top_category"]))
        self.card_avg_monthly.update_value(format_compact_inr(stats["avg_monthly_expense"]))
        self.card_peak_month.update_value(str(stats["peak_month"]))
        self.card_median_tx.update_value(format_inr(stats["median_transaction"]))

        # 2. Render Income vs Expenses Bar Chart
        self._render_bar_chart()

        # 3. Render Category Horizontal Bar Chart
        self._render_category_bar_chart()

    def _render_bar_chart(self):
        self.fig_bar.clear()
        ax = self.fig_bar.add_subplot(111)
        ax.set_facecolor(ThemeColors.BG_CARD)

        monthly_df = self.analytics_service.get_monthly_trend_analysis(year=self.selected_year)
        months = monthly_df["MONTH_NAME"].tolist()
        income_vals = monthly_df["INCOME"].values
        expense_vals = monthly_df["EXPENSES"].values

        x = np.arange(len(months))
        width = 0.35

        # Grouped Bars
        rects1 = ax.bar(x - width/2, income_vals, width, label="Income", color="#10B981", alpha=0.9, edgecolor="none")
        rects2 = ax.bar(x + width/2, expense_vals, width, label="Expenses", color=ThemeColors.PRIMARY, alpha=0.9, edgecolor="none")

        ax.set_xticks(x)
        ax.set_xticklabels(months, fontsize=8, color=ThemeColors.TEXT_MUTED)
        ax.tick_params(axis="y", labelsize=8, colors=ThemeColors.TEXT_MUTED)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_color(ThemeColors.BORDER_SUBTLE)
        ax.grid(axis="y", linestyle="--", alpha=0.25, color=ThemeColors.TEXT_MUTED)

        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda val, pos: format_compact_inr(val)))
        ax.legend(frameon=False, fontsize=8, loc="upper right")

        self.fig_bar.tight_layout(pad=1.2)
        self.canvas_bar.draw()

    def _render_category_bar_chart(self):
        self.fig_cat.clear()
        ax = self.fig_cat.add_subplot(111)
        ax.set_facecolor(ThemeColors.BG_CARD)

        cat_df = self.analytics_service.get_category_distribution(year=self.selected_year)

        if cat_df.empty or cat_df["AMOUNT"].sum() == 0:
            ax.text(0.5, 0.5, "No Expense Data", ha="center", va="center", color=ThemeColors.TEXT_MUTED)
            ax.axis("off")
        else:
            top_cats = cat_df.head(8).iloc[::-1]  # Top 8 reversed for horizontal display
            y_pos = np.arange(len(top_cats))
            amounts = top_cats["AMOUNT"].values
            cat_names = [name[:14] for name in top_cats["CATEGORY_NAME"]]

            bars = ax.barh(y_pos, amounts, height=0.55, color="#8B5CF6", alpha=0.85)

            ax.set_yticks(y_pos)
            ax.set_yticklabels(cat_names, fontsize=8, color=ThemeColors.TEXT_MAIN)
            ax.tick_params(axis="x", labelsize=8, colors=ThemeColors.TEXT_MUTED)

            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_visible(False)
            ax.spines["bottom"].set_color(ThemeColors.BORDER_SUBTLE)
            ax.grid(axis="x", linestyle="--", alpha=0.25, color=ThemeColors.TEXT_MUTED)

            ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda val, pos: format_compact_inr(val)))

        self.fig_cat.tight_layout(pad=1.2)
        self.canvas_cat.draw()
