"""
Settings and Database Configuration View.
Provides interactive Oracle Database connection management, live connection testing,
credentials configuration, schema compilation, and system diagnostics.
"""

import sys
import platform
import tkinter as tk
from tkinter import ttk, messagebox

from config.settings import AppConfig, ThemeColors, FontConfig
from database.connection import get_db
from database.initializer import initialize_database
from ui.components import CardFrame


class SettingsView(tk.Frame):
    """Settings view for configuring Oracle credentials and database tools."""

    def __init__(self, parent, on_navigate_callback=None, **kwargs):
        super().__init__(parent, bg=ThemeColors.BG_WINDOW, **kwargs)
        self.on_navigate_callback = on_navigate_callback
        self.db = get_db()

        self._build_ui()
        self._load_current_settings()

    def _build_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # -------------------------------------------------------------
        # Header
        # -------------------------------------------------------------
        header = tk.Frame(self, bg=ThemeColors.BG_WINDOW, padx=24, pady=16)
        header.grid(row=0, column=0, sticky="ew")

        tk.Label(
            header,
            text="Application & Database Settings",
            font=FontConfig.HEADER_LARGE,
            fg=ThemeColors.PRIMARY,
            bg=ThemeColors.BG_WINDOW
        ).pack(side="left")

        # -------------------------------------------------------------
        # Main Settings Panels (Left: Database Config | Right: System & Tools)
        # -------------------------------------------------------------
        main_content = tk.Frame(self, bg=ThemeColors.BG_WINDOW, padx=24, pady=4)
        main_content.grid(row=1, column=0, sticky="nsew")
        main_content.grid_rowconfigure(0, weight=1)
        main_content.grid_columnconfigure(0, weight=6)
        main_content.grid_columnconfigure(1, weight=4)

        # Left Panel: Oracle Connection Settings
        left_card = CardFrame(main_content)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        left_inner = tk.Frame(left_card.inner, bg=ThemeColors.BG_CARD, padx=24, pady=20)
        left_inner.pack(fill="both", expand=True)

        tk.Label(left_inner, text="Oracle Database Connection", font=FontConfig.HEADER_MEDIUM, fg=ThemeColors.TEXT_MAIN, bg=ThemeColors.BG_CARD).pack(anchor="w", pady=(0, 12))

        form = tk.Frame(left_inner, bg=ThemeColors.BG_CARD)
        form.pack(fill="x")
        pad = {"padx": 10, "pady": 6}

        # Username
        tk.Label(form, text="Oracle Username:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=0, column=0, sticky="w", **pad)
        self.user_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.user_var, width=28).grid(row=0, column=1, sticky="w", **pad)

        # Password
        tk.Label(form, text="Oracle Password:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=1, column=0, sticky="w", **pad)
        self.pass_var = tk.StringVar()
        self.pass_entry = ttk.Entry(form, textvariable=self.pass_var, show="*", width=28)
        self.pass_entry.grid(row=1, column=1, sticky="w", **pad)

        # Host
        tk.Label(form, text="Database Host:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=2, column=0, sticky="w", **pad)
        self.host_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.host_var, width=28).grid(row=2, column=1, sticky="w", **pad)

        # Port
        tk.Label(form, text="Port:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=3, column=0, sticky="w", **pad)
        self.port_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.port_var, width=14).grid(row=3, column=1, sticky="w", **pad)

        # Service Name / SID
        tk.Label(form, text="Service Name / SID:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=4, column=0, sticky="w", **pad)
        self.service_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.service_var, width=28).grid(row=4, column=1, sticky="w", **pad)

        # Oracle Client Directory (Thick mode path)
        tk.Label(form, text="Oracle Client Directory:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=5, column=0, sticky="w", **pad)
        self.client_dir_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.client_dir_var, width=28).grid(row=5, column=1, sticky="w", **pad)

        # Database Action Buttons
        btn_frame = tk.Frame(left_inner, bg=ThemeColors.BG_CARD)
        btn_frame.pack(fill="x", pady=(18, 0))

        ttk.Button(btn_frame, text="🔍 Test Oracle Connection", style="Secondary.TButton", command=self._test_connection).pack(side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="💾 Save Configuration", style="Primary.TButton", command=self._save_settings).pack(side="left")

        # Connection status feedback box
        self.status_box = tk.Label(
            left_inner,
            text="Ready to test connection.",
            font=FontConfig.BODY_SMALL,
            fg=ThemeColors.TEXT_MUTED,
            bg=ThemeColors.BG_MUTED,
            padx=12,
            pady=10,
            justify="left",
            wraplength=480
        )
        self.status_box.pack(fill="x", pady=(16, 0))

        # Right Panel: Maintenance & System Diagnostics
        right_card = CardFrame(main_content)
        right_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        right_inner = tk.Frame(right_card.inner, bg=ThemeColors.BG_CARD, padx=24, pady=20)
        right_inner.pack(fill="both", expand=True)

        tk.Label(right_inner, text="Database Tools & Setup", font=FontConfig.HEADER_MEDIUM, fg=ThemeColors.TEXT_MAIN, bg=ThemeColors.BG_CARD).pack(anchor="w", pady=(0, 12))

        ttk.Button(
            right_inner,
            text="⚡ Run Schema & Compile PL/SQL",
            style="Secondary.TButton",
            command=self._run_schema_setup
        ).pack(fill="x", pady=6)

        ttk.Button(
            right_inner,
            text="📦 Reload Demonstration Seed Data",
            style="Secondary.TButton",
            command=self._reload_seed_data
        ).pack(fill="x", pady=6)

        # System Information
        tk.Label(right_inner, text="System Diagnostics", font=FontConfig.HEADER_SMALL, fg=ThemeColors.TEXT_MAIN, bg=ThemeColors.BG_CARD).pack(anchor="w", pady=(20, 8))

        diag_frame = tk.Frame(right_inner, bg=ThemeColors.BG_MUTED, padx=12, pady=10)
        diag_frame.pack(fill="both", expand=True)

        info_lines = [
            f"Python Version: {platform.python_version()}",
            f"Operating System: {platform.system()} {platform.release()}",
            f"App Version: {AppConfig.VERSION}",
            f"Default User ID: {AppConfig.get_default_user_id()}",
            f"Default Profile: {AppConfig.get_default_username()}",
            f"Currency Symbol: {AppConfig.CURRENCY_SYMBOL} (INR)"
        ]
        for line in info_lines:
            tk.Label(diag_frame, text=line, font=FontConfig.BODY_SMALL, fg=ThemeColors.TEXT_MAIN, bg=ThemeColors.BG_MUTED).pack(anchor="w", pady=2)

    def _load_current_settings(self):
        self.user_var.set(AppConfig.get_oracle_user())
        self.pass_var.set(AppConfig.get_oracle_password())
        self.host_var.set(AppConfig.get_oracle_host())
        self.port_var.set(AppConfig.get_oracle_port())
        self.service_var.set(AppConfig.get_oracle_service_name())
        self.client_dir_var.set(AppConfig.get_oracle_client_dir())

    def _save_settings(self):
        user = self.user_var.get().strip()
        pwd = self.pass_var.get().strip()
        host = self.host_var.get().strip()
        port = self.port_var.get().strip()
        svc = self.service_var.get().strip()
        client = self.client_dir_var.get().strip()

        if not user or not host or not port or not svc:
            messagebox.showerror("Validation Error", "All connection fields are required.", parent=self)
            return

        AppConfig.save_settings(user, pwd, host, port, svc, client)
        messagebox.showinfo("Saved", "Database configuration saved to .env successfully!", parent=self)
        self._test_connection()

    def _test_connection(self):
        self.status_box.config(text="Connecting to Oracle Database...", fg=ThemeColors.TEXT_MUTED)
        self.update_idletasks()

        ok, msg, details = self.db.test_connection()
        if ok:
            mode = details.get("client_mode", "Thin")
            version = details.get("server_version", "Oracle")
            self.status_box.config(
                text=f"CONNECTED TO ORACLE DATABASE!\nMode: {mode} Mode\nVersion: {version}",
                fg="#059669"
            )
        else:
            self.status_box.config(
                text=f"CONNECTION FAILED:\n{msg}",
                fg="#DC2626"
            )

    def _run_schema_setup(self):
        confirm = messagebox.askyesno(
            "Confirm Setup",
            "This will create/re-create Oracle tables, triggers, and compile all PL/SQL stored procedures.\nDo you wish to proceed?",
            parent=self
        )
        if confirm:
            ok, msg = initialize_database(load_seed=False)
            if ok:
                messagebox.showinfo("Setup Complete", msg, parent=self)
            else:
                messagebox.showerror("Setup Failed", msg, parent=self)

    def _reload_seed_data(self):
        confirm = messagebox.askyesno(
            "Confirm Seed Data",
            "This will reload demonstration transactions and categories into Oracle Database.\nDo you wish to proceed?",
            parent=self
        )
        if confirm:
            ok, msg = initialize_database(load_seed=True)
            if ok:
                messagebox.showinfo("Seed Complete", msg, parent=self)
            else:
                messagebox.showerror("Seed Failed", msg, parent=self)
