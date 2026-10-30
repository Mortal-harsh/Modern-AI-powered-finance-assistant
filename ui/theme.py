"""
UI Theme and Styles for Tkinter ttk widgets.
Sets up a cohesive purple-and-lavender modern dashboard styling.
"""

import tkinter as tk
from tkinter import ttk
from config.settings import ThemeColors, FontConfig


def apply_theme(root: tk.Tk):
    """Configures global TTK style tokens for modern purple aesthetics."""
    root.configure(bg=ThemeColors.BG_WINDOW)

    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # Configure General Styles
    style.configure(
        ".",
        background=ThemeColors.BG_WINDOW,
        foreground=ThemeColors.TEXT_MAIN,
        font=FontConfig.BODY
    )

    # Frame styles
    style.configure("Card.TFrame", background=ThemeColors.BG_CARD)
    style.configure("Window.TFrame", background=ThemeColors.BG_WINDOW)
    style.configure("Sidebar.TFrame", background=ThemeColors.BG_SIDEBAR)

    # Label styles
    style.configure("TLabel", background=ThemeColors.BG_CARD, foreground=ThemeColors.TEXT_MAIN)
    style.configure("Window.TLabel", background=ThemeColors.BG_WINDOW, foreground=ThemeColors.TEXT_MAIN)
    style.configure("Header.TLabel", font=FontConfig.HEADER_LARGE, foreground=ThemeColors.PRIMARY, background=ThemeColors.BG_WINDOW)
    style.configure("Subheader.TLabel", font=FontConfig.HEADER_MEDIUM, foreground=ThemeColors.TEXT_MAIN, background=ThemeColors.BG_CARD)
    style.configure("CardTitle.TLabel", font=FontConfig.HEADER_SMALL, foreground=ThemeColors.TEXT_MAIN, background=ThemeColors.BG_CARD)
    style.configure("Muted.TLabel", font=FontConfig.BODY_SMALL, foreground=ThemeColors.TEXT_MUTED, background=ThemeColors.BG_CARD)
    style.configure("MetricLarge.TLabel", font=FontConfig.METRIC_LARGE, foreground=ThemeColors.TEXT_MAIN, background=ThemeColors.BG_CARD)

    # Primary Button Style (Purple pill)
    style.configure(
        "Primary.TButton",
        background=ThemeColors.PRIMARY,
        foreground=ThemeColors.TEXT_ON_PRIMARY,
        font=FontConfig.BUTTON,
        borderwidth=0,
        focuscolor="none",
        padding=(14, 8)
    )
    style.map(
        "Primary.TButton",
        background=[("active", ThemeColors.PRIMARY_HOVER), ("disabled", "#CBD5E1")],
        foreground=[("disabled", "#94A3B8")]
    )

    # Secondary Outline Button
    style.configure(
        "Secondary.TButton",
        background=ThemeColors.BG_CARD,
        foreground=ThemeColors.PRIMARY,
        font=FontConfig.BUTTON,
        borderwidth=1,
        bordercolor=ThemeColors.PRIMARY,
        focuscolor="none",
        padding=(12, 6)
    )
    style.map(
        "Secondary.TButton",
        background=[("active", ThemeColors.PRIMARY_LIGHT)]
    )

    # Pill Active Button
    style.configure(
        "PillActive.TButton",
        background=ThemeColors.PRIMARY,
        foreground=ThemeColors.TEXT_ON_PRIMARY,
        font=(FontConfig.FAMILY, 9, "bold"),
        borderwidth=0,
        focuscolor="none",
        padding=(10, 4)
    )
    style.map(
        "PillActive.TButton",
        background=[("active", ThemeColors.PRIMARY_HOVER)]
    )

    # Pill Inactive Button
    style.configure(
        "PillInactive.TButton",
        background=ThemeColors.BG_MUTED,
        foreground=ThemeColors.TEXT_MUTED,
        font=(FontConfig.FAMILY, 9, "normal"),
        borderwidth=0,
        focuscolor="none",
        padding=(10, 4)
    )
    style.map(
        "PillInactive.TButton",
        background=[("active", "#E2E8F0")],
        foreground=[("active", ThemeColors.TEXT_MAIN)]
    )

    # Treeview (Modern Table Style)
    style.configure(
        "Treeview",
        background=ThemeColors.BG_CARD,
        foreground=ThemeColors.TEXT_MAIN,
        fieldbackground=ThemeColors.BG_CARD,
        font=FontConfig.BODY,
        rowheight=32,
        borderwidth=0
    )
    style.configure(
        "Treeview.Heading",
        background=ThemeColors.PRIMARY_LIGHT,
        foreground=ThemeColors.PRIMARY,
        font=(FontConfig.FAMILY, 10, "bold"),
        relief="flat",
        padding=(6, 6)
    )
    style.map(
        "Treeview",
        background=[("selected", ThemeColors.PRIMARY_LIGHT)],
        foreground=[("selected", ThemeColors.PRIMARY)]
    )
    style.map(
        "Treeview.Heading",
        background=[("active", "#DDD6FE")]
    )

    # Entry and Combobox
    style.configure(
        "TEntry",
        fieldbackground=ThemeColors.BG_CARD,
        foreground=ThemeColors.TEXT_MAIN,
        padding=6,
        borderwidth=1,
        relief="solid"
    )
    style.configure(
        "TCombobox",
        fieldbackground=ThemeColors.BG_CARD,
        foreground=ThemeColors.TEXT_MAIN,
        padding=5,
        borderwidth=1,
        relief="solid"
    )

    # Progressbar (For Budgets)
    style.configure(
        "Purple.Horizontal.TProgressbar",
        troughcolor=ThemeColors.BG_MUTED,
        background=ThemeColors.PRIMARY,
        thickness=10
    )
    style.configure(
        "Warning.Horizontal.TProgressbar",
        troughcolor=ThemeColors.BG_MUTED,
        background=ThemeColors.WARNING,
        thickness=10
    )
    style.configure(
        "Danger.Horizontal.TProgressbar",
        troughcolor=ThemeColors.BG_MUTED,
        background=ThemeColors.DANGER,
        thickness=10
    )
