"""
Add Transaction View.
Dedicated form view for recording new Expenses and Incomes.
Validates inputs and calls Oracle PL/SQL stored procedure ADD_TRANSACTION.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta
from typing import Optional

from config.settings import ThemeColors, FontConfig
from services.transaction_service import TransactionService
from utils.validators import validate_amount, validate_date, validate_required_text
from ui.components import CardFrame


class AddTransactionView(tk.Frame):
    """Form view for creating Income or Expense transactions."""

    def __init__(self, parent, default_type: str = "EXPENSE", on_navigate_callback=None, **kwargs):
        super().__init__(parent, bg=ThemeColors.BG_WINDOW, **kwargs)
        self.default_type = default_type
        self.on_navigate_callback = on_navigate_callback
        self.tx_service = TransactionService()

        self._build_ui()
        self.set_type(default_type)

    def _build_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # -------------------------------------------------------------
        # Header
        # -------------------------------------------------------------
        header = tk.Frame(self, bg=ThemeColors.BG_WINDOW, padx=24, pady=16)
        header.grid(row=0, column=0, sticky="ew")

        self.title_lbl = tk.Label(
            header,
            text="Add New Expense",
            font=FontConfig.HEADER_LARGE,
            fg=ThemeColors.PRIMARY,
            bg=ThemeColors.BG_WINDOW
        )
        self.title_lbl.pack(side="left")

        # -------------------------------------------------------------
        # Form Card Container
        # -------------------------------------------------------------
        form_card = CardFrame(self)
        form_card.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 24))

        container = tk.Frame(form_card.inner, bg=ThemeColors.BG_CARD, padx=32, pady=24)
        container.pack(fill="both", expand=True)

        grid_pad = {"padx": 16, "pady": 10}

        # 1. Transaction Type Toggle
        tk.Label(container, text="Transaction Type:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=0, column=0, sticky="w", **grid_pad)
        type_frame = tk.Frame(container, bg=ThemeColors.BG_CARD)
        type_frame.grid(row=0, column=1, sticky="w", **grid_pad)

        self.type_var = tk.StringVar(value=self.default_type)
        self.r_exp = tk.Radiobutton(
            type_frame, text="Expense", value="EXPENSE", variable=self.type_var,
            font=FontConfig.BODY_BOLD, fg=ThemeColors.DANGER, bg=ThemeColors.BG_CARD,
            activebackground=ThemeColors.BG_CARD, command=self._on_type_changed
        )
        self.r_exp.pack(side="left", padx=(0, 16))

        self.r_inc = tk.Radiobutton(
            type_frame, text="Income", value="INCOME", variable=self.type_var,
            font=FontConfig.BODY_BOLD, fg=ThemeColors.SUCCESS, bg=ThemeColors.BG_CARD,
            activebackground=ThemeColors.BG_CARD, command=self._on_type_changed
        )
        self.r_inc.pack(side="left")

        # 2. Amount Field
        tk.Label(container, text="Amount (₹) *:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=1, column=0, sticky="w", **grid_pad)
        self.amount_var = tk.StringVar()
        amt_entry = ttk.Entry(container, textvariable=self.amount_var, font=(FontConfig.FAMILY, 12), width=30)
        amt_entry.grid(row=1, column=1, sticky="w", **grid_pad)

        # 3. Category Dropdown
        tk.Label(container, text="Category *:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=2, column=0, sticky="w", **grid_pad)
        self.cat_var = tk.StringVar()
        self.cat_cb = ttk.Combobox(container, textvariable=self.cat_var, state="readonly", width=28)
        self.cat_cb.grid(row=2, column=1, sticky="w", **grid_pad)

        # 4. Expense Scope / Type (Need, Want, Self, etc.)
        self.scope_label = tk.Label(container, text="Expense Scope:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD)
        self.scope_label.grid(row=3, column=0, sticky="w", **grid_pad)
        self.scope_var = tk.StringVar(value="NEED")
        self.scope_cb = ttk.Combobox(
            container,
            textvariable=self.scope_var,
            values=["NEED", "WANTS", "SELF", "ANONYMOUS", "INVESTMENT", "SAVINGS", "OTHER"],
            state="readonly",
            width=28
        )
        self.scope_cb.grid(row=3, column=1, sticky="w", **grid_pad)

        # 5. Date Field + Presets
        tk.Label(container, text="Transaction Date *:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=4, column=0, sticky="w", **grid_pad)
        date_box = tk.Frame(container, bg=ThemeColors.BG_CARD)
        date_box.grid(row=4, column=1, sticky="w", **grid_pad)

        self.date_var = tk.StringVar(value=str(date.today()))
        ttk.Entry(date_box, textvariable=self.date_var, width=16).pack(side="left", padx=(0, 8))

        btn_today = tk.Button(
            date_box, text="Today", font=(FontConfig.FAMILY, 8), bg=ThemeColors.BG_MUTED, fg=ThemeColors.TEXT_MAIN,
            bd=0, padx=6, pady=2, cursor="hand2", command=lambda: self.date_var.set(str(date.today()))
        )
        btn_today.pack(side="left", padx=2)

        btn_yesterday = tk.Button(
            date_box, text="Yesterday", font=(FontConfig.FAMILY, 8), bg=ThemeColors.BG_MUTED, fg=ThemeColors.TEXT_MAIN,
            bd=0, padx=6, pady=2, cursor="hand2", command=lambda: self.date_var.set(str(date.today() - timedelta(days=1)))
        )
        btn_yesterday.pack(side="left", padx=2)

        # 6. Payment Method
        tk.Label(container, text="Payment Method:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=5, column=0, sticky="w", **grid_pad)
        self.method_var = tk.StringVar(value="UPI")
        method_cb = ttk.Combobox(
            container,
            textvariable=self.method_var,
            values=["UPI", "Net Banking", "Credit Card", "Debit Card", "Cash", "Cheque"],
            state="readonly",
            width=28
        )
        method_cb.grid(row=5, column=1, sticky="w", **grid_pad)

        # 7. Description
        tk.Label(container, text="Description *:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=6, column=0, sticky="w", **grid_pad)
        self.desc_var = tk.StringVar()
        ttk.Entry(container, textvariable=self.desc_var, width=38).grid(row=6, column=1, sticky="w", **grid_pad)

        # 8. Notes
        tk.Label(container, text="Optional Notes:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=7, column=0, sticky="nw", **grid_pad)
        self.notes_entry = tk.Text(container, width=38, height=3, font=FontConfig.BODY, bd=1, relief="solid")
        self.notes_entry.grid(row=7, column=1, sticky="w", **grid_pad)

        # 9. Form Submission Buttons
        btn_frame = tk.Frame(container, bg=ThemeColors.BG_CARD)
        btn_frame.grid(row=8, column=1, sticky="w", pady=(18, 0), padx=16)

        submit_btn = ttk.Button(
            btn_frame,
            text="Save to Oracle Database",
            style="Primary.TButton",
            command=self._submit_transaction
        )
        submit_btn.pack(side="left", padx=(0, 10))

        reset_btn = ttk.Button(
            btn_frame,
            text="Clear Form",
            style="Secondary.TButton",
            command=self._reset_form
        )
        reset_btn.pack(side="left")

    def set_type(self, tx_type: str):
        """Switches form between Expense and Income."""
        self.type_var.set(tx_type)
        self._on_type_changed()

    def _on_type_changed(self):
        t = self.type_var.get()
        if t == "EXPENSE":
            self.title_lbl.config(text="Add New Expense")
            self.scope_label.grid()
            self.scope_cb.grid()
        else:
            self.title_lbl.config(text="Add New Income")
            self.scope_label.grid_remove()
            self.scope_cb.grid_remove()

        # Reload categories
        categories = self.tx_service.get_categories(category_type=t)
        self.cat_map = {c.category_name: c.category_id for c in categories}
        cat_names = list(self.cat_map.keys())
        self.cat_cb["values"] = cat_names
        if cat_names:
            self.cat_cb.current(0)

    def _submit_transaction(self):
        """Validates inputs and calls PL/SQL procedure ADD_TRANSACTION."""
        amt_ok, amount, err_amt = validate_amount(self.amount_var.get())
        if not amt_ok:
            messagebox.showerror("Validation Error", err_amt, parent=self)
            return

        date_ok, parsed_date, err_date = validate_date(self.date_var.get())
        if not date_ok:
            messagebox.showerror("Validation Error", err_date, parent=self)
            return

        desc_ok, desc, err_desc = validate_required_text(self.desc_var.get(), "Description")
        if not desc_ok:
            messagebox.showerror("Validation Error", err_desc, parent=self)
            return

        cat_name = self.cat_var.get()
        cat_id = self.cat_map.get(cat_name)
        if not cat_id:
            messagebox.showerror("Validation Error", "Please select a category.", parent=self)
            return

        tx_type = self.type_var.get()
        scope = self.scope_var.get() if tx_type == "EXPENSE" else "SAVINGS"
        method = self.method_var.get()
        notes = self.notes_entry.get("1.0", "end").strip()

        # Call PL/SQL procedure ADD_TRANSACTION
        ok, new_id, msg = self.tx_service.add_transaction(
            category_id=cat_id,
            transaction_type=tx_type,
            expense_type=scope,
            amount=amount,
            transaction_date=parsed_date,
            payment_method=method,
            description=desc,
            notes=notes
        )

        if ok:
            messagebox.showinfo(
                "Success",
                f"Successfully saved {tx_type.lower()} #{new_id} to Oracle Database!\nAmount: ₹{amount:,.2f}",
                parent=self
            )
            self._reset_form()
            # Optionally switch to Transactions view
            if self.on_navigate_callback:
                self.on_navigate_callback("Transactions")
        else:
            messagebox.showerror("Database Error", msg, parent=self)

    def _reset_form(self):
        self.amount_var.set("")
        self.desc_var.set("")
        self.notes_entry.delete("1.0", "end")
        self.date_var.set(str(date.today()))
        if self.cat_cb["values"]:
            self.cat_cb.current(0)
