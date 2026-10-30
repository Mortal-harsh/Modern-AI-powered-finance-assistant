"""
Dashboard View.
Recreates the reference UI dashboard layout with:
- "Expense Tracker" purple header and year pill selector
- "Expenses by Month" Matplotlib area chart with Expenses/Income toggle
- 2x2 KPI Stat Cards (Total Deposit, Total Expenses, Expense %, Saving %)
- Donut chart: Total Expenses by TYPE
- Donut chart: Total Expenses by Category
- Category Expense Summary Treeview with bold total footer
All data is populated dynamically from Oracle Database via PL/SQL procedures.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Dict, Any

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from config.settings import ThemeColors, FontConfig
from services.transaction_service import TransactionService
from services.analytics_service import AnalyticsService
from utils.formatters import format_inr, format_compact_inr, format_pct
from ui.components import CardFrame, StatCard, PillButton, YearPillSelector, MonthGridSelector


class DashboardView(tk.Frame):
    """Main dashboard page."""

    def __init__(self, parent, on_navigate_callback=None, **kwargs):
        super().__init__(parent, bg=ThemeColors.BG_WINDOW, **kwargs)
        self.on_navigate_callback = on_navigate_callback

        self.tx_service = TransactionService()
        self.analytics_service = AnalyticsService()

        # State filters
        self.selected_year: Optional[int] = 2024
        self.selected_month: Optional[int] = None
        self.monthly_chart_mode: str = "EXPENSES"  # "EXPENSES" or "INCOME"

        # Matplotlib figures
        self.fig_monthly = None
        self.canvas_monthly = None
        self.fig_type_donut = None
        self.canvas_type_donut = None
        self.fig_cat_donut = None
        self.canvas_cat_donut = None

        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        """Constructs layout matching reference screenshot."""
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # -------------------------------------------------------------
        # 1. TOP HEADER: "Expense Tracker" Title + Year Pill Selector
        # -------------------------------------------------------------
        header_frame = tk.Frame(self, bg=ThemeColors.BG_WINDOW, pady=10, padx=16)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)

        # Big Title
        title_label = tk.Label(
            header_frame,
            text="Expense Tracker",
            font=(FontConfig.FAMILY, 26, "bold"),
            fg=ThemeColors.PRIMARY,
            bg=ThemeColors.BG_WINDOW
        )
        title_label.grid(row=0, column=0, sticky="w")

        # Year Pills
        available_years = self.tx_service.get_available_years()
        # Ensure 2017 to 2024 years exist in list if desired
        display_years = list(range(2017, 2025))
        for y in available_years:
            if y not in display_years:
                display_years.append(y)

        self.year_selector = YearPillSelector(
            header_frame,
            years=display_years,
            on_year_changed=self._on_year_filter_changed
        )
        self.year_selector.grid(row=0, column=1, sticky="e")

        # -------------------------------------------------------------
        # 2. TOP SECTION (Row 1): Monthly Chart (Left) + 4 Stat Cards (Right)
        # -------------------------------------------------------------
        top_section = tk.Frame(self, bg=ThemeColors.BG_WINDOW, padx=16, pady=4)
        top_section.grid(row=1, column=0, sticky="nsew")
        top_section.grid_rowconfigure(0, weight=1)
        top_section.grid_columnconfigure(0, weight=6)  # 60% width for monthly chart
        top_section.grid_columnconfigure(1, weight=4)  # 40% width for 4 stat cards

        # --- Top Left: "Expenses by Month" Card ---
        self.monthly_card = CardFrame(top_section)
        self.monthly_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)
        self._build_monthly_card()

        # --- Top Right: 2x2 Stat Cards ---
        stats_grid = tk.Frame(top_section, bg=ThemeColors.BG_WINDOW)
        stats_grid.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=4)
        stats_grid.grid_rowconfigure(0, weight=1)
        stats_grid.grid_rowconfigure(1, weight=1)
        stats_grid.grid_columnconfigure(0, weight=1)
        stats_grid.grid_columnconfigure(1, weight=1)

        self.card_income = StatCard(stats_grid, title="Total Deposite", value="₹0")
        self.card_income.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=(0, 6))

        self.card_expenses = StatCard(stats_grid, title="Total Expenses", value="₹0")
        self.card_expenses.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=(0, 6))

        self.card_expense_pct = StatCard(stats_grid, title="Expense %", value="0%")
        self.card_expense_pct.grid(row=1, column=0, sticky="nsew", padx=(0, 6), pady=(6, 0))

        self.card_savings_pct = StatCard(stats_grid, title="Saving %", value="0%")
        self.card_savings_pct.grid(row=1, column=1, sticky="nsew", padx=(6, 0), pady=(6, 0))

        # -------------------------------------------------------------
        # 3. BOTTOM SECTION (Row 2):
        #    Col 0: Donut by TYPE | Col 1: Donut by Category | Col 2: Category Table
        # -------------------------------------------------------------
        bottom_section = tk.Frame(self, bg=ThemeColors.BG_WINDOW, padx=16, pady=8)
        bottom_section.grid(row=2, column=0, sticky="nsew")
        bottom_section.grid_rowconfigure(0, weight=1)
        bottom_section.grid_columnconfigure(0, weight=3)
        bottom_section.grid_columnconfigure(1, weight=4)
        bottom_section.grid_columnconfigure(2, weight=4)

        # Bottom Left: Expenses by TYPE Donut
        self.type_donut_card = CardFrame(bottom_section)
        self.type_donut_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=4)
        self._build_type_donut_card()

        # Bottom Middle: Expenses by Category Donut
        self.cat_donut_card = CardFrame(bottom_section)
        self.cat_donut_card.grid(row=0, column=1, sticky="nsew", padx=6, pady=4)
        self._build_cat_donut_card()

        # Bottom Right: Category Summary Table Card
        self.table_card = CardFrame(bottom_section)
        self.table_card.grid(row=0, column=2, sticky="nsew", padx=(6, 0), pady=4)
        self._build_category_table_card()

    def _build_monthly_card(self):
        """Builds monthly chart container with toggle pill & month filter button."""
        container = self.monthly_card.inner
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Card Top Toolbar
        tb = tk.Frame(container, bg=ThemeColors.BG_CARD, padx=14, pady=10)
        tb.grid(row=0, column=0, sticky="ew")
        tb.grid_columnconfigure(0, weight=1)
        tb.grid_columnconfigure(1, weight=0)

        # Title + Month Filter button
        title_box = tk.Frame(tb, bg=ThemeColors.BG_CARD)
        title_box.grid(row=0, column=0, sticky="w")

        self.monthly_title_lbl = tk.Label(
            title_box,
            text="Expenses by Month",
            font=FontConfig.HEADER_SMALL,
            fg=ThemeColors.TEXT_MAIN,
            bg=ThemeColors.BG_CARD
        )
        self.monthly_title_lbl.pack(side="left")

        # Month Filter pill button
        self.month_filter_btn = tk.Button(
            title_box,
            text="Month: All ▼",
            font=(FontConfig.FAMILY, 8, "bold"),
            bg=ThemeColors.BG_MUTED,
            fg=ThemeColors.TEXT_MUTED,
            bd=0,
            padx=8,
            pady=2,
            cursor="hand2",
            command=self._open_month_selector
        )
        self.month_filter_btn.pack(side="left", padx=(10, 0))

        # Toggle Pills: Expenses vs Income
        toggles_box = tk.Frame(tb, bg=ThemeColors.BG_MUTED, bd=1, relief="flat")
        toggles_box.grid(row=0, column=1, sticky="e")

        self.btn_toggle_exp = PillButton(
            toggles_box,
            text="Expenses",
            command=lambda: self._set_monthly_mode("EXPENSES"),
            is_active=True
        )
        self.btn_toggle_exp.pack(side="left")

        self.btn_toggle_inc = PillButton(
            toggles_box,
            text="Income",
            command=lambda: self._set_monthly_mode("INCOME"),
            is_active=False
        )
        self.btn_toggle_inc.pack(side="left")

        # Matplotlib Area Chart Canvas Frame
        self.monthly_plot_frame = tk.Frame(container, bg=ThemeColors.BG_CARD)
        self.monthly_plot_frame.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))

        self.fig_monthly = Figure(figsize=(5.5, 2.2), dpi=100)
        self.fig_monthly.patch.set_facecolor(ThemeColors.BG_CARD)
        self.canvas_monthly = FigureCanvasTkAgg(self.fig_monthly, master=self.monthly_plot_frame)
        self.canvas_monthly.get_tk_widget().pack(fill="both", expand=True)

    def _build_type_donut_card(self):
        """Card for Total Expenses by TYPE Donut Chart."""
        container = self.type_donut_card.inner
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)

        title = tk.Label(
            container,
            text="Total Expenses by TYPE",
            font=FontConfig.HEADER_SMALL,
            fg=ThemeColors.TEXT_MAIN,
            bg=ThemeColors.BG_CARD,
            padx=14,
            pady=10
        )
        title.grid(row=0, column=0, sticky="w")

        plot_frame = tk.Frame(container, bg=ThemeColors.BG_CARD)
        plot_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))

        self.fig_type_donut = Figure(figsize=(3.2, 2.4), dpi=100)
        self.fig_type_donut.patch.set_facecolor(ThemeColors.BG_CARD)
        self.canvas_type_donut = FigureCanvasTkAgg(self.fig_type_donut, master=plot_frame)
        self.canvas_type_donut.get_tk_widget().pack(fill="both", expand=True)

    def _build_cat_donut_card(self):
        """Card for Total Expenses by Category Donut Chart."""
        container = self.cat_donut_card.inner
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)

        title = tk.Label(
            container,
            text="Total Expenses by Category",
            font=FontConfig.HEADER_SMALL,
            fg=ThemeColors.TEXT_MAIN,
            bg=ThemeColors.BG_CARD,
            padx=14,
            pady=10
        )
        title.grid(row=0, column=0, sticky="w")

        plot_frame = tk.Frame(container, bg=ThemeColors.BG_CARD)
        plot_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))

        self.fig_cat_donut = Figure(figsize=(3.8, 2.4), dpi=100)
        self.fig_cat_donut.patch.set_facecolor(ThemeColors.BG_CARD)
        self.canvas_cat_donut = FigureCanvasTkAgg(self.fig_cat_donut, master=plot_frame)
        self.canvas_cat_donut.get_tk_widget().pack(fill="both", expand=True)

    def _build_category_table_card(self):
        """Card for Category Summary Table."""
        container = self.table_card.inner
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Header Title
        tb = tk.Frame(container, bg=ThemeColors.BG_CARD, padx=14, pady=8)
        tb.grid(row=0, column=0, sticky="ew")
        tb.grid_columnconfigure(0, weight=1)
        tb.grid_columnconfigure(1, weight=1)

        cat_lbl = tk.Label(tb, text="Category", font=FontConfig.HEADER_SMALL, fg=ThemeColors.TEXT_MAIN, bg=ThemeColors.BG_CARD)
        cat_lbl.grid(row=0, column=0, sticky="w")

        exp_lbl = tk.Label(tb, text="Total Expenses ▼", font=(FontConfig.FAMILY, 9, "bold"), fg=ThemeColors.TEXT_MUTED, bg=ThemeColors.BG_CARD)
        exp_lbl.grid(row=0, column=1, sticky="e")

        # Treeview inside Frame with Scrollbar
        table_frame = tk.Frame(container, bg=ThemeColors.BG_CARD, padx=8, pady=2)
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        columns = ("category", "amount")
        self.cat_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="tree",  # show tree with folder icons
            selectmode="browse",
            height=6
        )
        self.cat_tree.heading("#0", text="")
        self.cat_tree.column("#0", width=22, stretch=False)
        self.cat_tree.column("category", anchor="w", width=140)
        self.cat_tree.column("amount", anchor="e", width=110)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.cat_tree.yview)
        self.cat_tree.configure(yscrollcommand=scrollbar.set)

        self.cat_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Footer Row (Total)
        footer_frame = tk.Frame(container, bg=ThemeColors.PRIMARY_LIGHT, padx=14, pady=6)
        footer_frame.grid(row=2, column=0, sticky="ew")
        footer_frame.grid_columnconfigure(0, weight=1)
        footer_frame.grid_columnconfigure(1, weight=1)

        tot_lbl = tk.Label(
            footer_frame,
            text="Total",
            font=(FontConfig.FAMILY, 10, "bold"),
            fg=ThemeColors.PRIMARY,
            bg=ThemeColors.PRIMARY_LIGHT
        )
        tot_lbl.grid(row=0, column=0, sticky="w")

        self.total_exp_footer_lbl = tk.Label(
            footer_frame,
            text="₹0",
            font=(FontConfig.FAMILY, 10, "bold"),
            fg=ThemeColors.PRIMARY,
            bg=ThemeColors.PRIMARY_LIGHT
        )
        self.total_exp_footer_lbl.grid(row=0, column=1, sticky="e")

    # -----------------------------------------------------------------
    # Filter Actions & Callbacks
    # -----------------------------------------------------------------
    def _on_year_filter_changed(self, year: Optional[int]):
        self.selected_year = year
        self.refresh_data()

    def _open_month_selector(self):
        MonthGridSelector(self, self.selected_month, self._on_month_selected)

    def _on_month_selected(self, month: Optional[int]):
        self.selected_month = month
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        if month:
            self.month_filter_btn.config(text=f"Month: {months[month-1]} ▼")
        else:
            self.month_filter_btn.config(text="Month: All ▼")
        self.refresh_data()

    def _set_monthly_mode(self, mode: str):
        self.monthly_chart_mode = mode
        self.btn_toggle_exp.set_active(mode == "EXPENSES")
        self.btn_toggle_inc.set_active(mode == "INCOME")
        self.monthly_title_lbl.config(text="Expenses by Month" if mode == "EXPENSES" else "Income by Month")
        self._render_monthly_chart()

    # -----------------------------------------------------------------
    # Data Refresh & Chart Rendering
    # -----------------------------------------------------------------
    def refresh_data(self):
        """Queries Oracle Database and re-renders all widgets."""
        # 1. Update 4 KPI Stat Cards
        kpi = self.analytics_service.get_kpi_metrics(year=self.selected_year, month=self.selected_month)
        self.card_income.update_value(format_compact_inr(kpi["total_income"]))
        self.card_expenses.update_value(format_compact_inr(kpi["total_expenses"]))
        self.card_expense_pct.update_value(format_pct(kpi["expense_pct"]))
        self.card_savings_pct.update_value(format_pct(kpi["savings_pct"]))

        # 2. Render Charts
        self._render_monthly_chart()
        self._render_type_donut_chart()
        self._render_category_donut_chart()

        # 3. Render Category Summary Table
        self._render_category_table()

    def _render_monthly_chart(self):
        """Renders the top-left area chart with lavender gradient under curve."""
        self.fig_monthly.clear()
        ax = self.fig_monthly.add_subplot(111)
        ax.set_facecolor(ThemeColors.BG_CARD)

        # Retrieve 12-month data from PL/SQL or Analytics
        monthly_df = self.analytics_service.get_monthly_trend_analysis(year=self.selected_year)
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        y_col = "EXPENSES" if self.monthly_chart_mode == "EXPENSES" else "INCOME"
        y_values = monthly_df[y_col].values

        x = list(range(12))

        # Purple curve line and area fill matching screenshot
        line_color = ThemeColors.PRIMARY
        fill_color = ThemeColors.PRIMARY_LIGHT

        ax.plot(x, y_values, color=line_color, linewidth=2.5, marker="o", markersize=4, markerfacecolor=line_color)
        ax.fill_between(x, y_values, color=fill_color, alpha=0.55)

        # Style axes
        ax.set_xticks(x)
        ax.set_xticklabels(months, fontsize=8, color=ThemeColors.TEXT_MUTED)
        ax.tick_params(axis="y", labelsize=8, colors=ThemeColors.TEXT_MUTED)

        # Clean borders
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_color(ThemeColors.BORDER_SUBTLE)
        ax.grid(axis="y", linestyle="--", alpha=0.25, color=ThemeColors.TEXT_MUTED)

        # Indian currency formatter on Y-axis
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda val, pos: format_compact_inr(val)))

        self.fig_monthly.tight_layout(pad=1.2)
        self.canvas_monthly.draw()

    def _render_type_donut_chart(self):
        """Renders the 'Total Expenses by TYPE' Donut Chart."""
        self.fig_type_donut.clear()
        ax = self.fig_type_donut.add_subplot(111)
        ax.set_facecolor(ThemeColors.BG_CARD)

        type_df = self.analytics_service.get_expense_type_distribution(year=self.selected_year, month=self.selected_month)

        if type_df.empty or type_df["AMOUNT"].sum() == 0:
            ax.text(0.5, 0.5, "No Data", ha="center", va="center", color=ThemeColors.TEXT_MUTED, fontsize=10)
            ax.axis("off")
        else:
            labels = type_df["EXPENSE_TYPE"].tolist()
            sizes = type_df["AMOUNT"].tolist()

            # Elegant purple palette
            colors_list = ["#7C5CFC", "#B4A5F5", "#818CF8", "#C4B5FD", "#DDD6FE", "#38BDF8"]

            wedges, _ = ax.pie(
                sizes,
                colors=colors_list[:len(sizes)],
                startangle=90,
                wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2)
            )

            # Legend
            ax.legend(
                wedges,
                [l[:9] for l in labels],
                title="TYPE",
                loc="center left",
                bbox_to_anchor=(0.95, 0.5),
                fontsize=7.5,
                title_fontsize=8,
                frameon=False
            )

        self.fig_type_donut.tight_layout(pad=0.5)
        self.canvas_type_donut.draw()

    def _render_category_donut_chart(self):
        """Renders the 'Total Expenses by Category' Donut Chart."""
        self.fig_cat_donut.clear()
        ax = self.fig_cat_donut.add_subplot(111)
        ax.set_facecolor(ThemeColors.BG_CARD)

        cat_df = self.analytics_service.get_category_distribution(year=self.selected_year, month=self.selected_month)

        if cat_df.empty or cat_df["AMOUNT"].sum() == 0:
            ax.text(0.5, 0.5, "No Data", ha="center", va="center", color=ThemeColors.TEXT_MUTED, fontsize=10)
            ax.axis("off")
        else:
            # Group beyond top 7 into 'OTHER' for readable legend
            if len(cat_df) > 7:
                top7 = cat_df.iloc[:6]
                other_sum = cat_df.iloc[6:]["AMOUNT"].sum()
                other_row = {"CATEGORY_NAME": "OTHER", "AMOUNT": other_sum}
                labels = top7["CATEGORY_NAME"].tolist() + ["OTHER"]
                sizes = top7["AMOUNT"].tolist() + [other_sum]
            else:
                labels = cat_df["CATEGORY_NAME"].tolist()
                sizes = cat_df["AMOUNT"].tolist()

            colors_list = [
                "#7C5CFC", "#A78BFA", "#C4B5FD", "#DDD6FE",
                "#F472B6", "#38BDF8", "#FBBF24", "#34D399"
            ]

            wedges, _ = ax.pie(
                sizes,
                colors=colors_list[:len(sizes)],
                startangle=90,
                wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2)
            )

            ax.legend(
                wedges,
                [l[:10] for l in labels],
                title="Category",
                loc="center left",
                bbox_to_anchor=(0.95, 0.5),
                fontsize=7.5,
                title_fontsize=8,
                frameon=False
            )

        self.fig_cat_donut.tight_layout(pad=0.5)
        self.canvas_cat_donut.draw()

    def _render_category_table(self):
        """Populates the category summary treeview and total footer."""
        for item in self.cat_tree.get_children():
            self.cat_tree.delete(item)

        # Call PL/SQL procedure GET_CATEGORY_SUMMARY
        cat_data = self.tx_service.get_category_summary(year=self.selected_year, month=self.selected_month)

        total_sum = 0.0
        for item in cat_data:
            c_name = item.get("CATEGORY_NAME", "")
            amt = float(item.get("TOTAL_AMOUNT", 0.0))
            total_sum += amt
            # Insert row into tree
            self.cat_tree.insert(
                "",
                "end",
                text="⊞",  # Expandable icon
                values=(c_name, format_inr(amt))
            )

        self.total_exp_footer_lbl.config(text=format_inr(total_sum))
