"""
Smart Expense Tracker with Analytics.
Main Desktop Application Entry Point.
Orchestrates sidebar navigation, dynamic frame swapping, Oracle Database lifecycle,
and global styling.
"""

import os
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

# Add current directory to path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import AppConfig, ThemeColors, FontConfig
from database.connection import get_db
from database.initializer import initialize_database
from ui.theme import apply_theme
from ui.dashboard import DashboardView
from ui.transactions import TransactionsView
from ui.add_transaction import AddTransactionView
from ui.budgets import BudgetsView
from ui.analytics import AnalyticsView
from ui.reports import ReportsView
from ui.settings import SettingsView


class ExpenseTrackerApp(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.title(AppConfig.APP_NAME)
        self.minsize(AppConfig.MIN_WINDOW_WIDTH, AppConfig.MIN_WINDOW_HEIGHT)
        self.geometry(f"{AppConfig.DEFAULT_WINDOW_WIDTH}x{AppConfig.DEFAULT_WINDOW_HEIGHT}")

        # Center window on screen
        self._center_window()

        # Database Manager
        self.db = get_db()

        # Apply global theme
        apply_theme(self)

        # State
        self.current_page_name = "Dashboard"
        self.pages = {}
        self.nav_buttons = {}

        # Load icons
        self._load_nav_icons()

        # Build main layout
        self._build_layout()

        # Test initial database connection
        self._check_db_status()

        # Show Dashboard initially
        self.navigate_to("Dashboard")

    def _center_window(self):
        self.update_idletasks()
        w = AppConfig.DEFAULT_WINDOW_WIDTH
        h = AppConfig.DEFAULT_WINDOW_HEIGHT
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _load_nav_icons(self):
        """Loads sidebar icons with fallback."""
        icons_dir = BASE_DIR / "assets" / "icons"
        self.icons = {}
        icon_names = [
            "dashboard", "transactions", "add_expense", "add_income",
            "budgets", "analytics", "reports", "settings"
        ]

        for name in icon_names:
            icon_path = icons_dir / f"{name}.png"
            if icon_path.exists():
                try:
                    img = Image.open(icon_path).resize((22, 22), Image.Resampling.LANCZOS)
                    self.icons[name] = ImageTk.PhotoImage(img)
                except Exception:
                    self.icons[name] = None
            else:
                self.icons[name] = None

    def _build_layout(self):
        """Builds vertical sidebar on left and content area on right."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)  # Status bar
        self.grid_columnconfigure(0, weight=0)  # Sidebar
        self.grid_columnconfigure(1, weight=1)  # Main Content

        # -------------------------------------------------------------
        # Left Vertical Sidebar (Matching reference design)
        # -------------------------------------------------------------
        self.sidebar = tk.Frame(self, bg=ThemeColors.BG_SIDEBAR, width=220, bd=1, relief="solid")
        self.sidebar.grid(row=0, column=0, sticky="ns", padx=(0, 1))
        self.sidebar.grid_propagate(False)

        # App Brand Header
        brand_frame = tk.Frame(self.sidebar, bg=ThemeColors.BG_SIDEBAR, pady=20, padx=16)
        brand_frame.pack(fill="x")

        brand_badge = tk.Label(
            brand_frame,
            text="✨ AGY Finance",
            font=(FontConfig.FAMILY, 12, "bold"),
            fg=ThemeColors.PRIMARY,
            bg=ThemeColors.BG_SIDEBAR
        )
        brand_badge.pack(anchor="w")

        # Sidebar Separator
        sep = tk.Frame(self.sidebar, height=1, bg=ThemeColors.BORDER_SUBTLE)
        sep.pack(fill="x", padx=12, pady=(0, 14))

        # Navigation Menu Items
        nav_items = [
            ("Dashboard", "dashboard", "Dashboard"),
            ("Transactions", "transactions", "Transactions"),
            ("Add Expense", "add_expense", "Add Expense"),
            ("Add Income", "add_income", "Add Income"),
            ("Budgets", "budgets", "Budgets"),
            ("Analytics", "analytics", "Analytics"),
            ("Reports", "reports", "Reports"),
            ("Settings", "settings", "Settings")
        ]

        self.nav_menu_container = tk.Frame(self.sidebar, bg=ThemeColors.BG_SIDEBAR, padx=10)
        self.nav_menu_container.pack(fill="both", expand=True)

        for page_name, icon_key, label in nav_items:
            btn = self._create_sidebar_button(page_name, icon_key, label)
            btn.pack(fill="x", pady=3)
            self.nav_buttons[page_name] = btn

        # Sidebar Footer Profile
        user_frame = tk.Frame(self.sidebar, bg=ThemeColors.BG_MUTED, padx=12, pady=10)
        user_frame.pack(side="bottom", fill="x", padx=12, pady=16)

        user_title = tk.Label(
            user_frame,
            text="Active Profile",
            font=(FontConfig.FAMILY, 8, "bold"),
            fg=ThemeColors.TEXT_MUTED,
            bg=ThemeColors.BG_MUTED
        )
        user_title.pack(anchor="w")

        user_name = tk.Label(
            user_frame,
            text=f"👤 {AppConfig.get_default_username()}",
            font=FontConfig.BODY_BOLD,
            fg=ThemeColors.TEXT_MAIN,
            bg=ThemeColors.BG_MUTED
        )
        user_name.pack(anchor="w", pady=(2, 0))

        # -------------------------------------------------------------
        # Right Main Content Container
        # -------------------------------------------------------------
        self.content_container = tk.Frame(self, bg=ThemeColors.BG_WINDOW)
        self.content_container.grid(row=0, column=1, sticky="nsew")
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        # -------------------------------------------------------------
        # Bottom Global Status Bar
        # -------------------------------------------------------------
        self.status_bar = tk.Frame(self, bg=ThemeColors.BG_CARD, height=28, bd=1, relief="solid")
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.db_status_lbl = tk.Label(
            self.status_bar,
            text="Checking Oracle Database...",
            font=FontConfig.BODY_SMALL,
            fg=ThemeColors.TEXT_MUTED,
            bg=ThemeColors.BG_CARD,
            padx=12
        )
        self.db_status_lbl.pack(side="left")

        self.global_tip_lbl = tk.Label(
            self.status_bar,
            text="Tip: Real Oracle PL/SQL procedures and functions active.",
            font=FontConfig.BODY_SMALL,
            fg=ThemeColors.TEXT_MUTED,
            bg=ThemeColors.BG_CARD,
            padx=12
        )
        self.global_tip_lbl.pack(side="right")

    def _create_sidebar_button(self, page_name: str, icon_key: str, label: str) -> tk.Frame:
        """Creates an interactive navigation pill button."""
        frame = tk.Frame(
            self.nav_menu_container,
            bg=ThemeColors.BG_SIDEBAR,
            padx=10,
            pady=8,
            cursor="hand2"
        )

        icon = self.icons.get(icon_key)
        if icon:
            icon_lbl = tk.Label(frame, image=icon, bg=ThemeColors.BG_SIDEBAR)
            icon_lbl.pack(side="left", padx=(0, 10))
            frame.icon_lbl = icon_lbl

        text_lbl = tk.Label(
            frame,
            text=label,
            font=FontConfig.BODY_BOLD,
            fg=ThemeColors.TEXT_MAIN,
            bg=ThemeColors.BG_SIDEBAR
        )
        text_lbl.pack(side="left")
        frame.text_lbl = text_lbl

        # Click event handlers
        for widget in [frame, text_lbl] + ([frame.icon_lbl] if icon else []):
            widget.bind("<Button-1>", lambda e, p=page_name: self.navigate_to(p))
            widget.bind("<Enter>", lambda e, f=frame, p=page_name: self._on_nav_hover(f, p, True))
            widget.bind("<Leave>", lambda e, f=frame, p=page_name: self._on_nav_hover(f, p, False))

        return frame

    def _on_nav_hover(self, frame: tk.Frame, page_name: str, is_hover: bool):
        if page_name == self.current_page_name:
            return
        bg = ThemeColors.BG_MUTED if is_hover else ThemeColors.BG_SIDEBAR
        frame.config(bg=bg)
        frame.text_lbl.config(bg=bg)
        if hasattr(frame, "icon_lbl"):
            frame.icon_lbl.config(bg=bg)

    def navigate_to(self, page_name: str):
        """Swaps content frame and refreshes data."""
        self.current_page_name = page_name

        # Update sidebar active highlights
        for p_name, frame in self.nav_buttons.items():
            is_active = (p_name == page_name)
            bg = ThemeColors.PRIMARY_LIGHT if is_active else ThemeColors.BG_SIDEBAR
            fg = ThemeColors.PRIMARY if is_active else ThemeColors.TEXT_MAIN
            frame.config(bg=bg)
            frame.text_lbl.config(bg=bg, fg=fg)
            if hasattr(frame, "icon_lbl"):
                frame.icon_lbl.config(bg=bg)

        # Lazy initialize pages or raise existing
        if page_name not in self.pages:
            self.pages[page_name] = self._create_page(page_name)
            self.pages[page_name].grid(row=0, column=0, sticky="nsew")

        # Bring to front
        view = self.pages[page_name]
        view.tkraise()

        # Trigger data refresh if view supports it
        if hasattr(view, "refresh_data"):
            view.refresh_data()
        elif hasattr(view, "refresh_transactions"):
            view.refresh_transactions()
        elif hasattr(view, "refresh_budgets"):
            view.refresh_budgets()
        elif hasattr(view, "refresh_analytics"):
            view.refresh_analytics()
        elif hasattr(view, "refresh_report_data"):
            view.refresh_report_data()

    def _create_page(self, page_name: str) -> tk.Widget:
        """Instantiates view classes."""
        if page_name == "Dashboard":
            return DashboardView(self.content_container, on_navigate_callback=self.navigate_to)
        elif page_name == "Transactions":
            return TransactionsView(self.content_container, on_navigate_callback=self.navigate_to)
        elif page_name == "Add Expense":
            return AddTransactionView(self.content_container, default_type="EXPENSE", on_navigate_callback=self.navigate_to)
        elif page_name == "Add Income":
            return AddTransactionView(self.content_container, default_type="INCOME", on_navigate_callback=self.navigate_to)
        elif page_name == "Budgets":
            return BudgetsView(self.content_container, on_navigate_callback=self.navigate_to)
        elif page_name == "Analytics":
            return AnalyticsView(self.content_container, on_navigate_callback=self.navigate_to)
        elif page_name == "Reports":
            return ReportsView(self.content_container, on_navigate_callback=self.navigate_to)
        elif page_name == "Settings":
            return SettingsView(self.content_container, on_navigate_callback=self.navigate_to)
        else:
            frame = tk.Frame(self.content_container, bg=ThemeColors.BG_WINDOW)
            tk.Label(frame, text=f"Page {page_name} under development", font=FontConfig.HEADER_MEDIUM).pack(expand=True)
            return frame

    def _check_db_status(self):
        """Verifies database connection on startup."""
        ok, msg, details = self.db.test_connection()
        if ok:
            mode = details.get("client_mode", "Thin")
            dsn = details.get("dsn", "localhost:1521/xe")
            user = details.get("user", "expense_tracker")
            self.db_status_lbl.config(
                text=f"🟢 Connected to Oracle DB ({mode} Mode) | User: {user} | {dsn}",
                fg="#059669"
            )
        else:
            self.db_status_lbl.config(
                text="🔴 Oracle Database: Disconnected (Configure in Settings)",
                fg="#DC2626"
            )


def main():
    app = ExpenseTrackerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
