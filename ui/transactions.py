"""
Transactions Management View.
Provides full transaction audit log, real-time search, multi-criteria filtering,
edit/delete dialogs invoking PL/SQL procedures, and CSV export.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, datetime
from typing import Optional, List

from config.settings import ThemeColors, FontConfig
from services.transaction_service import TransactionService
from services.report_service import ReportService
from models.transaction_model import Transaction
from utils.formatters import format_inr, format_date_display
from utils.validators import validate_amount, validate_date, validate_required_text
from ui.components import CardFrame


class TransactionsView(tk.Frame):
    """Transaction audit and management table view."""

    def __init__(self, parent, on_navigate_callback=None, **kwargs):
        super().__init__(parent, bg=ThemeColors.BG_WINDOW, **kwargs)
        self.on_navigate_callback = on_navigate_callback

        self.tx_service = TransactionService()
        self.report_service = ReportService()

        self.current_transactions: List[Transaction] = []

        self._build_ui()
        self.refresh_transactions()

    def _build_ui(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # -------------------------------------------------------------
        # 1. Header & Quick Action Buttons
        # -------------------------------------------------------------
        header_bar = tk.Frame(self, bg=ThemeColors.BG_WINDOW, padx=16, pady=12)
        header_bar.grid(row=0, column=0, sticky="ew")
        header_bar.grid_columnconfigure(0, weight=1)
        header_bar.grid_columnconfigure(1, weight=0)

        title_lbl = tk.Label(
            header_bar,
            text="Transaction History",
            font=FontConfig.HEADER_LARGE,
            fg=ThemeColors.PRIMARY,
            bg=ThemeColors.BG_WINDOW
        )
        title_lbl.grid(row=0, column=0, sticky="w")

        btn_box = tk.Frame(header_bar, bg=ThemeColors.BG_WINDOW)
        btn_box.grid(row=0, column=1, sticky="e")

        btn_add = ttk.Button(
            btn_box,
            text="+ Add Expense",
            style="Primary.TButton",
            command=lambda: self.on_navigate_callback("Add Expense") if self.on_navigate_callback else None
        )
        btn_add.pack(side="left", padx=4)

        btn_add_inc = ttk.Button(
            btn_box,
            text="+ Add Income",
            style="Secondary.TButton",
            command=lambda: self.on_navigate_callback("Add Income") if self.on_navigate_callback else None
        )
        btn_add_inc.pack(side="left", padx=4)

        btn_export = ttk.Button(
            btn_box,
            text="Export CSV",
            style="Secondary.TButton",
            command=self._export_csv
        )
        btn_export.pack(side="left", padx=4)

        # -------------------------------------------------------------
        # 2. Filter & Search Toolbar
        # -------------------------------------------------------------
        filter_card = CardFrame(self)
        filter_card.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        fb = tk.Frame(filter_card.inner, bg=ThemeColors.BG_CARD, padx=12, pady=10)
        fb.pack(fill="x", expand=True)

        # Search Bar
        tk.Label(fb, text="Search:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).pack(side="left", padx=(0, 4))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(fb, textvariable=self.search_var, width=22)
        self.search_entry.pack(side="left", padx=(0, 14))
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_transactions())

        # Type Filter
        tk.Label(fb, text="Type:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).pack(side="left", padx=(0, 4))
        self.type_filter_var = tk.StringVar(value="ALL")
        type_cb = ttk.Combobox(fb, textvariable=self.type_filter_var, values=["ALL", "EXPENSE", "INCOME"], state="readonly", width=10)
        type_cb.pack(side="left", padx=(0, 14))
        type_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_transactions())

        # Category Filter
        tk.Label(fb, text="Category:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).pack(side="left", padx=(0, 4))
        self.cat_filter_var = tk.StringVar(value="All Categories")
        self.categories_map = {"All Categories": None}
        for c in self.tx_service.get_categories():
            self.categories_map[c.category_name] = c.category_id

        self.cat_cb = ttk.Combobox(fb, textvariable=self.cat_filter_var, values=list(self.categories_map.keys()), state="readonly", width=18)
        self.cat_cb.pack(side="left", padx=(0, 14))
        self.cat_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_transactions())

        # Action Buttons on Table: Edit & Delete
        btn_edit = ttk.Button(fb, text="Edit Selected", style="Secondary.TButton", command=self._edit_selected_tx)
        btn_edit.pack(side="right", padx=4)

        btn_del = ttk.Button(fb, text="Delete Selected", style="Secondary.TButton", command=self._delete_selected_tx)
        btn_del.pack(side="right", padx=4)

        # -------------------------------------------------------------
        # 3. Treeview Table Card
        # -------------------------------------------------------------
        table_card = CardFrame(self)
        table_card.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 10))
        table_card.inner.grid_rowconfigure(0, weight=1)
        table_card.inner.grid_columnconfigure(0, weight=1)

        columns = ("id", "date", "type", "category", "scope", "amount", "method", "description")
        self.tree = ttk.Treeview(
            table_card.inner,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Setup Headings
        self.tree.heading("id", text="# ID", command=lambda: self._sort_column("id", False))
        self.tree.heading("date", text="Date ▼", command=lambda: self._sort_column("date", False))
        self.tree.heading("type", text="Type", command=lambda: self._sort_column("type", False))
        self.tree.heading("category", text="Category", command=lambda: self._sort_column("category", False))
        self.tree.heading("scope", text="Scope", command=lambda: self._sort_column("scope", False))
        self.tree.heading("amount", text="Amount", command=lambda: self._sort_column("amount", True))
        self.tree.heading("method", text="Payment Method", command=lambda: self._sort_column("method", False))
        self.tree.heading("description", text="Description")

        # Column widths & alignments
        self.tree.column("id", width=55, anchor="center")
        self.tree.column("date", width=100, anchor="center")
        self.tree.column("type", width=85, anchor="center")
        self.tree.column("category", width=150, anchor="w")
        self.tree.column("scope", width=95, anchor="center")
        self.tree.column("amount", width=120, anchor="e")
        self.tree.column("method", width=130, anchor="w")
        self.tree.column("description", width=260, anchor="w")

        # Scrollbars
        v_scroll = ttk.Scrollbar(table_card.inner, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(table_card.inner, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        # Double click to edit
        self.tree.bind("<Double-1>", lambda e: self._edit_selected_tx())

        # Tag styles for positive (Income) vs negative (Expense)
        self.tree.tag_configure("INCOME", foreground="#059669")
        self.tree.tag_configure("EXPENSE", foreground="#DC2626")

        # -------------------------------------------------------------
        # 4. Status Bar Counter
        # -------------------------------------------------------------
        status_bar = tk.Frame(self, bg=ThemeColors.BG_WINDOW, padx=16, pady=4)
        status_bar.grid(row=3, column=0, sticky="ew")

        self.status_lbl = tk.Label(
            status_bar,
            text="Loading transactions...",
            font=FontConfig.BODY_SMALL,
            fg=ThemeColors.TEXT_MUTED,
            bg=ThemeColors.BG_WINDOW
        )
        self.status_lbl.pack(side="left")

    def refresh_transactions(self):
        """Fetches transactions from Oracle database with active filters."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        tx_type = self.type_filter_var.get()
        if tx_type == "ALL":
            tx_type = None

        cat_name = self.cat_filter_var.get()
        cat_id = self.categories_map.get(cat_name)

        search_q = self.search_var.get()

        self.current_transactions = self.tx_service.get_transactions(
            transaction_type=tx_type,
            category_id=cat_id,
            search_query=search_q,
            limit=1000
        )

        total_amount = 0.0
        for tx in self.current_transactions:
            tag = tx.transaction_type
            amt_display = f"+{format_inr(tx.amount)}" if tag == "INCOME" else f"-{format_inr(tx.amount)}"
            if tag == "INCOME":
                total_amount += tx.amount
            else:
                total_amount -= tx.amount

            self.tree.insert(
                "",
                "end",
                iid=str(tx.transaction_id),
                values=(
                    tx.transaction_id,
                    format_date_display(tx.transaction_date),
                    tx.transaction_type,
                    tx.category_name,
                    tx.expense_type,
                    amt_display,
                    tx.payment_method,
                    tx.description
                ),
                tags=(tag,)
            )

        self.status_lbl.config(
            text=f"Showing {len(self.current_transactions)} transactions | Net Balance: {format_inr(total_amount)}"
        )

    def _sort_column(self, col: str, is_numeric: bool):
        """Sorts treeview column."""
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        if is_numeric:
            items.sort(key=lambda t: float(t[0].replace("₹", "").replace(",", "").replace("+", "").strip() or 0), reverse=True)
        else:
            items.sort(reverse=False)

        for index, (_, k) in enumerate(items):
            self.tree.move(k, "", index)

    def _delete_selected_tx(self):
        """Deletes selected transaction via PL/SQL procedure with confirmation."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select a transaction to delete.")
            return

        tx_id = int(selected[0])
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to permanently delete Transaction #{tx_id}?\nThis operation will delete the record from Oracle Database."
        )
        if confirm:
            ok, msg = self.tx_service.delete_transaction(tx_id)
            if ok:
                messagebox.showinfo("Success", msg)
                self.refresh_transactions()
            else:
                messagebox.showerror("Error", msg)

    def _edit_selected_tx(self):
        """Opens Edit Transaction dialog."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select a transaction to edit.")
            return

        tx_id = int(selected[0])
        tx = next((t for t in self.current_transactions if t.transaction_id == tx_id), None)
        if not tx:
            return

        # Open Edit Dialog
        EditTransactionDialog(self, tx, on_success=self.refresh_transactions)

    def _export_csv(self):
        """Exports currently loaded transactions to CSV."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Spreadsheet", "*.csv")],
            initialfile="expense_transactions.csv"
        )
        if file_path:
            ok, msg = self.report_service.export_transactions_csv(file_path)
            if ok:
                messagebox.showinfo("Export Successful", msg)
            else:
                messagebox.showerror("Export Failed", msg)


class EditTransactionDialog(tk.Toplevel):
    """Modal dialog to edit existing transaction and call PL/SQL UPDATE_TRANSACTION."""

    def __init__(self, parent, transaction: Transaction, on_success):
        super().__init__(parent)
        self.title(f"Edit Transaction #{transaction.transaction_id}")
        self.configure(bg=ThemeColors.BG_CARD)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.tx = transaction
        self.on_success = on_success
        self.tx_service = TransactionService()

        self._build_form()
        self.geometry("450x480")

    def _build_form(self):
        padding = {"padx": 16, "pady": 6}

        tk.Label(self, text=f"Edit Transaction #{self.tx.transaction_id}", font=FontConfig.HEADER_MEDIUM, fg=ThemeColors.PRIMARY, bg=ThemeColors.BG_CARD).pack(anchor="w", padx=16, pady=12)

        form_frame = tk.Frame(self, bg=ThemeColors.BG_CARD)
        form_frame.pack(fill="both", expand=True, padx=16)

        # Amount
        tk.Label(form_frame, text="Amount (₹):", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=0, column=0, sticky="w", **padding)
        self.amount_var = tk.StringVar(value=str(self.tx.amount))
        ttk.Entry(form_frame, textvariable=self.amount_var, width=28).grid(row=0, column=1, sticky="w", **padding)

        # Date
        tk.Label(form_frame, text="Date (YYYY-MM-DD):", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=1, column=0, sticky="w", **padding)
        self.date_var = tk.StringVar(value=str(self.tx.transaction_date)[:10])
        ttk.Entry(form_frame, textvariable=self.date_var, width=28).grid(row=1, column=1, sticky="w", **padding)

        # Category
        tk.Label(form_frame, text="Category:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=2, column=0, sticky="w", **padding)
        categories = self.tx_service.get_categories()
        self.cat_map = {c.category_name: c.category_id for c in categories}
        self.cat_var = tk.StringVar(value=self.tx.category_name)
        cat_cb = ttk.Combobox(form_frame, textvariable=self.cat_var, values=list(self.cat_map.keys()), state="readonly", width=26)
        cat_cb.grid(row=2, column=1, sticky="w", **padding)

        # Type
        tk.Label(form_frame, text="Transaction Type:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=3, column=0, sticky="w", **padding)
        self.type_var = tk.StringVar(value=self.tx.transaction_type)
        type_cb = ttk.Combobox(form_frame, textvariable=self.type_var, values=["EXPENSE", "INCOME"], state="readonly", width=26)
        type_cb.grid(row=3, column=1, sticky="w", **padding)

        # Scope
        tk.Label(form_frame, text="Expense Scope:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=4, column=0, sticky="w", **padding)
        self.scope_var = tk.StringVar(value=self.tx.expense_type)
        scope_cb = ttk.Combobox(form_frame, textvariable=self.scope_var, values=["NEED", "WANTS", "SELF", "ANONYMOUS", "INVESTMENT", "SAVINGS", "OTHER"], state="readonly", width=26)
        scope_cb.grid(row=4, column=1, sticky="w", **padding)

        # Payment Method
        tk.Label(form_frame, text="Payment Method:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=5, column=0, sticky="w", **padding)
        self.method_var = tk.StringVar(value=self.tx.payment_method)
        method_cb = ttk.Combobox(form_frame, textvariable=self.method_var, values=["UPI", "Net Banking", "Credit Card", "Debit Card", "Cash"], state="readonly", width=26)
        method_cb.grid(row=5, column=1, sticky="w", **padding)

        # Description
        tk.Label(form_frame, text="Description:", font=FontConfig.BODY_BOLD, bg=ThemeColors.BG_CARD).grid(row=6, column=0, sticky="w", **padding)
        self.desc_var = tk.StringVar(value=self.tx.description)
        ttk.Entry(form_frame, textvariable=self.desc_var, width=28).grid(row=6, column=1, sticky="w", **padding)

        # Buttons
        btn_frame = tk.Frame(self, bg=ThemeColors.BG_CARD)
        btn_frame.pack(fill="x", padx=16, pady=16)

        ttk.Button(btn_frame, text="Save Changes", style="Primary.TButton", command=self._save).pack(side="right", padx=6)
        ttk.Button(btn_frame, text="Cancel", style="Secondary.TButton", command=self.destroy).pack(side="right")

    def _save(self):
        amt_ok, amt, err_amt = validate_amount(self.amount_var.get())
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

        cat_id = self.cat_map.get(self.cat_var.get())
        if not cat_id:
            messagebox.showerror("Validation Error", "Please select a valid category.", parent=self)
            return

        # Invoke PL/SQL UPDATE_TRANSACTION
        ok, msg = self.tx_service.update_transaction(
            transaction_id=self.tx.transaction_id,
            category_id=cat_id,
            transaction_type=self.type_var.get(),
            expense_type=self.scope_var.get(),
            amount=amt,
            transaction_date=parsed_date,
            payment_method=self.method_var.get(),
            description=desc,
            notes=self.tx.notes or ""
        )

        if ok:
            messagebox.showinfo("Success", "Transaction successfully updated in Oracle Database!", parent=self)
            if self.on_success:
                self.on_success()
            self.destroy()
        else:
            messagebox.showerror("Error", msg, parent=self)
