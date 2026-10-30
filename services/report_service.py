"""
Report Service.
Generates structured CSV exports and printable PDF financial statements using ReportLab.
"""

import os
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
except ImportError:
    SimpleDocTemplate = None

from utils.formatters import format_inr, format_pct, format_date_display
from services.transaction_service import TransactionService
from services.budget_service import BudgetService
from services.analytics_service import AnalyticsService

logger = logging.getLogger("ReportService")


class ReportService:
    """Exports transactions and financial summaries to CSV and PDF."""

    def __init__(self):
        self.tx_service = TransactionService()
        self.budget_service = BudgetService()
        self.analytics_service = AnalyticsService()

    def export_transactions_csv(self, file_path: str, year: Optional[int] = None, month: Optional[int] = None) -> Tuple[bool, str]:
        """Exports filtered transactions to a CSV spreadsheet."""
        try:
            txs = self.tx_service.get_transactions(year=year, month=month, limit=5000)
            if not txs:
                return False, "No transactions found for the selected period to export."

            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Transaction ID", "Date", "Type", "Expense Scope",
                    "Category", "Amount (INR)", "Payment Method", "Description", "Notes"
                ])
                for t in txs:
                    writer.writerow([
                        t.transaction_id,
                        t.transaction_date.strftime("%Y-%m-%d") if hasattr(t.transaction_date, "strftime") else str(t.transaction_date),
                        t.transaction_type,
                        t.expense_type,
                        t.category_name,
                        f"{t.amount:.2f}",
                        t.payment_method,
                        t.description,
                        t.notes or ""
                    ])

            return True, f"Successfully exported {len(txs)} transactions to {file_path}"
        except Exception as e:
            logger.error("CSV Export failed: %s", e)
            return False, f"Failed to export CSV: {e}"

    def export_pdf_report(self, file_path: str, year: Optional[int] = None, month: Optional[int] = None) -> Tuple[bool, str]:
        """
        Generates a professional financial summary PDF report using ReportLab.
        """
        if SimpleDocTemplate is None:
            return False, "ReportLab package is not installed."

        try:
            doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
            styles = getSampleStyleSheet()

            # Custom styles
            title_style = ParagraphStyle(
                "DocTitle",
                parent=styles["Heading1"],
                fontSize=20,
                leading=24,
                textColor=colors.HexColor("#7C5CFC"),
                spaceAfter=6
            )
            subtitle_style = ParagraphStyle(
                "DocSubtitle",
                parent=styles["Normal"],
                fontSize=10,
                leading=14,
                textColor=colors.HexColor("#64748B"),
                spaceAfter=14
            )
            section_style = ParagraphStyle(
                "SectionHeading",
                parent=styles["Heading2"],
                fontSize=13,
                leading=16,
                textColor=colors.HexColor("#1E1B4B"),
                spaceBefore=12,
                spaceAfter=6
            )
            cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=9, leading=11)
            cell_bold = ParagraphStyle("CellBold", parent=styles["Normal"], fontSize=9, leading=11, fontName="Helvetica-Bold")

            story = []

            # 1. Header
            story.append(Paragraph("Smart Expense Tracker with Analytics", title_style))
            period_str = f"Year: {year or 'All Time'}"
            if month:
                period_str += f" | Month: {month}"
            gen_time = datetime.now().strftime("%d-%b-%Y %H:%M")
            story.append(Paragraph(f"Financial Performance Report | {period_str} | Generated on {gen_time}", subtitle_style))
            story.append(Spacer(1, 10))

            # 2. Executive KPI Summary Table
            kpi = self.analytics_service.get_kpi_metrics(year=year, month=month)
            kpi_data = [
                ["Total Income", "Total Expenses", "Net Savings", "Expense Rate", "Savings Rate"],
                [
                    format_inr(kpi["total_income"]),
                    format_inr(kpi["total_expenses"]),
                    format_inr(kpi["savings"]),
                    format_pct(kpi["expense_pct"]),
                    format_pct(kpi["savings_pct"])
                ]
            ]
            kpi_table = Table(kpi_data, colWidths=[105, 105, 105, 100, 100])
            kpi_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDE9FE")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#6C5CE7")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ]))
            story.append(Paragraph("Executive Summary", section_style))
            story.append(kpi_table)
            story.append(Spacer(1, 15))

            # 3. Category Expense Breakdown Table
            cat_df = self.analytics_service.get_category_distribution(year=year, month=month)
            story.append(Paragraph("Category-wise Spending Breakdown", section_style))
            if not cat_df.empty:
                cat_rows = [["Category", "Transactions", "Total Spending", "Share %"]]
                for _, row in cat_df.iterrows():
                    cat_rows.append([
                        str(row["CATEGORY_NAME"]),
                        str(int(row["COUNT"])),
                        format_inr(row["AMOUNT"]),
                        f"{row['SHARE_PCT']}%"
                    ])
                cat_table = Table(cat_rows, colWidths=[180, 100, 135, 100])
                cat_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7C5CFC")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FE")]),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(cat_table)
            else:
                story.append(Paragraph("No expense records available for this period.", cell_style))
            story.append(Spacer(1, 15))

            # 4. Recent Transactions Table (Top 15)
            txs = self.tx_service.get_transactions(year=year, month=month, limit=15)
            story.append(Paragraph("Recent Transactions Audit Log", section_style))
            if txs:
                tx_rows = [["Date", "Type", "Category", "Description", "Amount"]]
                for t in txs:
                    tx_rows.append([
                        format_date_display(t.transaction_date),
                        t.transaction_type,
                        t.category_name,
                        Paragraph(t.description[:35], cell_style),
                        format_inr(t.amount)
                    ])
                tx_table = Table(tx_rows, colWidths=[80, 65, 120, 150, 100])
                tx_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#64748B")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FE")]),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("ALIGN", (4, 1), (4, -1), "RIGHT"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]))
                story.append(tx_table)
            else:
                story.append(Paragraph("No transaction records found.", cell_style))

            # Build document
            doc.build(story)
            return True, f"Successfully created PDF report: {file_path}"
        except Exception as e:
            logger.error("PDF generation failed: %s", e)
            return False, f"Failed to generate PDF report: {e}"
