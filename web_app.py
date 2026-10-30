"""
Web Dashboard Server for Smart Expense Tracker with Analytics.
Complete functional web app with full pages for:
- Dashboard (Reference UI design)
- Transactions Table (Audit log, Search, Filters, Delete)
- Add Transaction Modal (Invoking Oracle PL/SQL ADD_TRANSACTION)
- Budgets (Allocations, Real-time status, Utilization progress, Alerts)
- Analytics & Reports (CSV & PDF export)
All integrated directly with local Oracle Database XE.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, date
from flask import Flask, render_template_string, jsonify, request, send_file

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from services.transaction_service import TransactionService
from services.analytics_service import AnalyticsService
from services.budget_service import BudgetService
from services.report_service import ReportService
from database.connection import get_db
from utils.formatters import format_inr, format_compact_inr, format_pct, format_date_display

app = Flask(__name__)

tx_service = TransactionService()
analytics_service = AnalyticsService()
budget_service = BudgetService()
report_service = ReportService()
db = get_db()


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Expense Tracker with Analytics</title>
    <!-- Chart.js for interactive visualizations -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --primary: #7C5CFC;
            --primary-hover: #6949F0;
            --primary-light: #EDE9FE;
            --primary-muted: #B4A5F5;
            --bg-canvas: #F7F8FC;
            --bg-card: #FFFFFF;
            --border-subtle: #E8EBF2;
            --text-main: #1E1B4B;
            --text-muted: #64748B;
            --text-light: #94A3B8;
            --success: #10B981;
            --danger: #EF4444;
            --warning: #F59E0B;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }

        body {
            background-color: var(--bg-canvas);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
        }

        /* Left Dock Sidebar */
        .sidebar {
            width: 76px;
            background: #FFFFFF;
            border-right: 1px solid var(--border-subtle);
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 24px 0;
            gap: 16px;
            position: sticky;
            top: 0;
            height: 100vh;
            z-index: 50;
        }

        .nav-item {
            width: 46px;
            height: 46px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s ease;
            color: #64748B;
            border: none;
            background: transparent;
            position: relative;
        }

        .nav-item:hover {
            background-color: #F1F3F9;
            color: var(--primary);
        }

        .nav-item.active {
            background-color: var(--primary-light);
            color: var(--primary);
        }

        .nav-item svg {
            width: 22px;
            height: 22px;
            stroke-width: 2.2;
        }

        /* Tooltip on hover */
        .nav-item::after {
            content: attr(data-tooltip);
            position: absolute;
            left: 58px;
            background: #1E1B4B;
            color: #FFFFFF;
            padding: 5px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            white-space: nowrap;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.15s;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }

        .nav-item:hover::after {
            opacity: 1;
        }

        /* Main Container */
        .main-container {
            flex: 1;
            padding: 20px 32px 32px 32px;
            max-width: 1400px;
            overflow-y: auto;
        }

        /* Views (Tabs) */
        .view-page {
            display: none;
        }

        .view-page.active {
            display: block;
        }

        /* Top Header */
        .top-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }

        .app-title {
            font-family: Georgia, serif;
            font-size: 32px;
            font-weight: 700;
            color: var(--primary);
            letter-spacing: -0.5px;
        }

        .year-selector-wrap {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
        }

        .year-title {
            font-size: 11px;
            font-weight: 700;
            color: var(--text-main);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .year-pills {
            display: flex;
            gap: 4px;
            background: #FFFFFF;
            padding: 4px 6px;
            border-radius: 30px;
            border: 1px solid var(--border-subtle);
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        }

        .year-pill {
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            border: none;
            background: transparent;
            color: var(--text-muted);
            transition: all 0.18s ease;
        }

        .year-pill:hover {
            color: var(--primary);
        }

        .year-pill.active {
            background: var(--primary-muted);
            color: #FFFFFF;
        }

        /* Dashboard Grid Layout */
        .dashboard-grid {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .top-row {
            display: grid;
            grid-template-columns: 7fr 5fr;
            gap: 20px;
        }

        .bottom-row {
            display: grid;
            grid-template-columns: 3.5fr 4.2fr 4.3fr;
            gap: 20px;
        }

        /* Card Styles */
        .card {
            background: var(--bg-card);
            border-radius: 16px;
            border: 1px solid var(--border-subtle);
            padding: 20px 22px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.015);
            position: relative;
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }

        .card-title {
            font-size: 15px;
            font-weight: 700;
            color: var(--text-main);
        }

        /* Toggle Pills (Expenses vs Income) */
        .toggle-pills {
            display: flex;
            background: #F1F3F9;
            padding: 3px;
            border-radius: 20px;
        }

        .toggle-btn {
            border: none;
            background: transparent;
            padding: 4px 14px;
            border-radius: 16px;
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
            cursor: pointer;
            transition: all 0.2s;
        }

        .toggle-btn.active {
            background: var(--primary-muted);
            color: #FFFFFF;
        }

        /* 2x2 Stat Cards Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            height: 100%;
        }

        .stat-card {
            background: #FFFFFF;
            border-radius: 16px;
            border: 1px solid var(--border-subtle);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 24px 16px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.015);
        }

        .stat-value {
            font-size: 34px;
            font-weight: 800;
            color: var(--text-main);
            letter-spacing: -0.5px;
            margin-bottom: 4px;
        }

        .stat-label {
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
        }

        /* Month Filter Floating Grid */
        .month-filter-dropdown {
            position: relative;
            display: inline-block;
        }

        .month-pill-btn {
            background: #F1F3F9;
            border: 1px solid #E2E8F0;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 700;
            color: var(--text-muted);
            cursor: pointer;
        }

        .month-grid-popup {
            display: none;
            position: absolute;
            top: 32px;
            left: 0;
            background: #FFFFFF;
            border: 1px solid var(--border-subtle);
            border-radius: 14px;
            padding: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.08);
            z-index: 100;
            grid-template-columns: repeat(3, 1fr);
            gap: 6px;
            width: 190px;
        }

        .month-grid-popup.show {
            display: grid;
        }

        .m-item {
            padding: 6px 4px;
            text-align: center;
            font-size: 11px;
            font-weight: 600;
            border-radius: 8px;
            border: 1px solid #E2E8F0;
            background: #F8FAFC;
            cursor: pointer;
        }

        .m-item:hover, .m-item.active {
            background: var(--primary);
            color: #FFFFFF;
            border-color: var(--primary);
        }

        /* Summary Table */
        .category-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }

        .category-table th {
            text-align: left;
            font-weight: 700;
            color: var(--text-main);
            padding: 6px 8px 12px 8px;
            font-size: 13px;
        }

        .category-table th.amount-col {
            text-align: right;
            color: var(--text-muted);
            font-weight: 600;
        }

        .category-table td {
            padding: 7px 8px;
            border-bottom: 1px solid #F1F5F9;
            color: var(--text-main);
            font-weight: 500;
        }

        .category-table td.amount-cell {
            text-align: right;
            font-weight: 600;
            color: var(--text-main);
        }

        .category-table tr.total-row td {
            border-top: 2px solid #E2E8F0;
            border-bottom: none;
            font-weight: 800;
            color: var(--primary);
            padding-top: 12px;
        }

        .tree-icon {
            display: inline-block;
            width: 14px;
            height: 14px;
            border: 1px solid #94A3B8;
            border-radius: 3px;
            text-align: center;
            line-height: 12px;
            font-size: 10px;
            color: #64748B;
            margin-right: 6px;
        }

        /* Oracle Status Badge */
        .oracle-badge {
            background: #ECFDF5;
            color: #059669;
            border: 1px solid #A7F3D0;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .oracle-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #10B981;
        }

        /* Buttons & Badges */
        .btn-primary {
            background: var(--primary);
            color: #FFFFFF;
            border: none;
            padding: 9px 18px;
            border-radius: 10px;
            font-size: 13px;
            font-weight: 700;
            cursor: pointer;
            transition: background 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        .btn-primary:hover {
            background: var(--primary-hover);
        }

        .btn-secondary {
            background: #FFFFFF;
            color: var(--primary);
            border: 1px solid var(--border-subtle);
            padding: 8px 16px;
            border-radius: 10px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-secondary:hover {
            background: #F8FAFC;
            border-color: var(--primary);
        }

        .badge-income {
            background: #ECFDF5;
            color: #059669;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 700;
        }

        .badge-expense {
            background: #FEF2F2;
            color: #DC2626;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 700;
        }

        /* Transactions Full Table Page */
        .tx-toolbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            flex-wrap: wrap;
            gap: 12px;
        }

        .search-box {
            display: flex;
            align-items: center;
            background: #FFFFFF;
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            padding: 7px 12px;
            width: 260px;
        }

        .search-box input {
            border: none;
            outline: none;
            width: 100%;
            font-size: 13px;
            margin-left: 6px;
        }

        .filter-select {
            padding: 8px 12px;
            border-radius: 10px;
            border: 1px solid var(--border-subtle);
            background: #FFFFFF;
            font-size: 13px;
            font-weight: 600;
            color: var(--text-main);
            outline: none;
        }

        .tx-table-container {
            background: #FFFFFF;
            border: 1px solid var(--border-subtle);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 2px 6px rgba(0,0,0,0.015);
        }

        .full-tx-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }

        .full-tx-table th {
            background: var(--primary-light);
            color: var(--primary);
            text-align: left;
            padding: 12px 14px;
            font-weight: 700;
            border-bottom: 1px solid var(--border-subtle);
        }

        .full-tx-table td {
            padding: 11px 14px;
            border-bottom: 1px solid #F1F5F9;
        }

        .full-tx-table tr:hover {
            background: #F8F9FE;
        }

        .btn-delete-row {
            background: #FEE2E2;
            color: #DC2626;
            border: none;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            cursor: pointer;
        }

        .btn-delete-row:hover {
            background: #FCA5A5;
        }

        /* Modal Overlay */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(15, 23, 42, 0.45);
            backdrop-filter: blur(2px);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }

        .modal-overlay.show {
            display: flex;
        }

        .modal-card {
            background: #FFFFFF;
            border-radius: 20px;
            width: 480px;
            max-width: 90vw;
            padding: 28px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
            animation: modalFadeIn 0.2s ease;
        }

        @keyframes modalFadeIn {
            from { transform: scale(0.96); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }

        .modal-title {
            font-size: 20px;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 20px;
        }

        .form-group {
            margin-bottom: 14px;
        }

        .form-label {
            display: block;
            font-size: 12px;
            font-weight: 700;
            color: var(--text-main);
            margin-bottom: 6px;
        }

        .form-input, .form-select {
            width: 100%;
            padding: 9px 12px;
            border-radius: 8px;
            border: 1px solid var(--border-subtle);
            font-size: 13px;
            outline: none;
        }

        .form-input:focus, .form-select:focus {
            border-color: var(--primary);
        }

        .modal-actions {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            margin-top: 24px;
        }
    </style>
</head>
<body>

    <!-- Left Navigation Dock -->
    <div class="sidebar">
        <!-- 1. Dashboard -->
        <button class="nav-item active" id="nav-dashboard" onclick="switchTab('dashboard')" data-tooltip="Dashboard">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
        </button>

        <!-- 2. Transactions Table -->
        <button class="nav-item" id="nav-transactions" onclick="switchTab('transactions')" data-tooltip="Transactions">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
        </button>

        <!-- 3. Add Transaction -->
        <button class="nav-item" onclick="openAddModal('EXPENSE')" data-tooltip="+ Add Expense">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"/></svg>
        </button>

        <!-- 4. Budgets -->
        <button class="nav-item" id="nav-budgets" onclick="switchTab('budgets')" data-tooltip="Budgets">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"/></svg>
        </button>

        <!-- 5. Analytics -->
        <button class="nav-item" id="nav-analytics" onclick="switchTab('analytics')" data-tooltip="Analytics">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
        </button>

        <!-- 6. Reports (CSV/PDF) -->
        <button class="nav-item" id="nav-reports" onclick="switchTab('reports')" data-tooltip="Reports">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
        </button>
    </div>

    <!-- Main App Container -->
    <div class="main-container">

        <!-- ======================================================== -->
        <!-- VIEW 1: DASHBOARD (Exact reference visual layout) -->
        <!-- ======================================================== -->
        <div id="view-dashboard" class="view-page active">
            <!-- Header -->
            <div class="top-header">
                <div>
                    <h1 class="app-title">Expense Tracker</h1>
                </div>
                
                <!-- Year Selector Pills -->
                <div class="year-selector-wrap">
                    <span class="year-title">Year</span>
                    <div class="year-pills">
                        <button class="year-pill" onclick="changeYear(null, this)">Select all</button>
                        <button class="year-pill" onclick="changeYear(2017, this)">2017</button>
                        <button class="year-pill" onclick="changeYear(2018, this)">2018</button>
                        <button class="year-pill" onclick="changeYear(2019, this)">2019</button>
                        <button class="year-pill" onclick="changeYear(2020, this)">2020</button>
                        <button class="year-pill" onclick="changeYear(2021, this)">2021</button>
                        <button class="year-pill" onclick="changeYear(2022, this)">2022</button>
                        <button class="year-pill" onclick="changeYear(2023, this)">2023</button>
                        <button class="year-pill active" onclick="changeYear(2024, this)">2024</button>
                    </div>
                </div>

                <!-- Oracle Database Status Badge -->
                <div class="oracle-badge">
                    <span class="oracle-dot"></span>
                    <span>Oracle XE Database Active</span>
                </div>
            </div>

            <!-- Dashboard Content Grid -->
            <div class="dashboard-grid">

                <!-- Top Row: Expenses by Month Chart + 4 Stat Cards -->
                <div class="top-row">

                    <!-- Expenses by Month Card -->
                    <div class="card">
                        <div class="card-header">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span class="card-title" id="monthly-chart-title">Expenses by Month</span>
                                
                                <!-- Month Filter Dropdown -->
                                <div class="month-filter-dropdown">
                                    <button class="month-pill-btn" onclick="toggleMonthPopup()">Month: <span id="selected-m-label">All</span> ▼</button>
                                    <div class="month-grid-popup" id="monthPopup">
                                        <div class="m-item active" onclick="selectMonth(null, 'All')">All</div>
                                        <div class="m-item" onclick="selectMonth(1, 'Jan')">Jan</div>
                                        <div class="m-item" onclick="selectMonth(2, 'Feb')">Feb</div>
                                        <div class="m-item" onclick="selectMonth(3, 'Mar')">Mar</div>
                                        <div class="m-item" onclick="selectMonth(4, 'Apr')">Apr</div>
                                        <div class="m-item" onclick="selectMonth(5, 'May')">May</div>
                                        <div class="m-item" onclick="selectMonth(6, 'Jun')">Jun</div>
                                        <div class="m-item" onclick="selectMonth(7, 'Jul')">Jul</div>
                                        <div class="m-item" onclick="selectMonth(8, 'Aug')">Aug</div>
                                        <div class="m-item" onclick="selectMonth(9, 'Sep')">Sep</div>
                                        <div class="m-item" onclick="selectMonth(10, 'Oct')">Oct</div>
                                        <div class="m-item" onclick="selectMonth(11, 'Nov')">Nov</div>
                                        <div class="m-item" onclick="selectMonth(12, 'Dec')">Dec</div>
                                    </div>
                                </div>
                            </div>

                            <!-- Toggle Pills -->
                            <div class="toggle-pills">
                                <button class="toggle-btn active" id="btn-toggle-exp" onclick="setChartMode('EXPENSES')">Expenses</button>
                                <button class="toggle-btn" id="btn-toggle-inc" onclick="setChartMode('INCOME')">Income</button>
                            </div>
                        </div>

                        <!-- Smooth Area Chart Canvas -->
                        <div style="height: 195px; width: 100%;">
                            <canvas id="monthlyAreaChart"></canvas>
                        </div>
                    </div>

                    <!-- 2x2 Stat Cards -->
                    <div class="stats-grid">
                        <div class="stat-card">
                            <span class="stat-value" id="card-income">₹710K</span>
                            <span class="stat-label">Total Deposite</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-value" id="card-expenses">₹553K</span>
                            <span class="stat-label">Total Expenses</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-value" id="card-expense-pct">78%</span>
                            <span class="stat-label">Expense %</span>
                        </div>
                        <div class="stat-card">
                            <span class="stat-value" id="card-savings-pct">22%</span>
                            <span class="stat-label">Saving %</span>
                        </div>
                    </div>

                </div>

                <!-- Bottom Row: Donut TYPE | Donut Category | Category Summary Table -->
                <div class="bottom-row">

                    <!-- 1. Total Expenses by TYPE Donut -->
                    <div class="card">
                        <div class="card-header">
                            <span class="card-title">Total Expenses by TYPE</span>
                        </div>
                        <div style="height: 220px; position: relative;">
                            <canvas id="typeDonutChart"></canvas>
                        </div>
                    </div>

                    <!-- 2. Total Expenses by Category Donut -->
                    <div class="card">
                        <div class="card-header">
                            <span class="card-title">Total Expenses by Category</span>
                        </div>
                        <div style="height: 220px; position: relative;">
                            <canvas id="categoryDonutChart"></canvas>
                        </div>
                    </div>

                    <!-- 3. Category Summary Table Card -->
                    <div class="card" style="padding: 16px 20px;">
                        <table class="category-table">
                            <thead>
                                <tr>
                                    <th>Category</th>
                                    <th class="amount-col">Total Expenses ▼</th>
                                </tr>
                            </thead>
                            <tbody id="categoryTableBody">
                                <!-- Populated dynamically from Oracle DB -->
                            </tbody>
                            <tfoot>
                                <tr class="total-row">
                                    <td>Total</td>
                                    <td class="amount-cell" id="categoryTableTotal">₹5,52,810</td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>

                </div>

            </div>
        </div>

        <!-- ======================================================== -->
        <!-- VIEW 2: TRANSACTIONS MANAGEMENT TABLE -->
        <!-- ======================================================== -->
        <div id="view-transactions" class="view-page">
            <div class="top-header">
                <div>
                    <h1 class="app-title">Transaction History</h1>
                    <p style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">Live transaction ledger queried directly from Oracle Database table</p>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button class="btn-primary" onclick="openAddModal('EXPENSE')">+ Add Expense</button>
                    <button class="btn-secondary" onclick="openAddModal('INCOME')">+ Add Income</button>
                </div>
            </div>

            <!-- Toolbar -->
            <div class="tx-toolbar">
                <div class="search-box">
                    <span>🔍</span>
                    <input type="text" id="txSearchInput" placeholder="Search description, category..." onkeyup="filterTransactionsTable()">
                </div>
                <div style="display: flex; gap: 10px;">
                    <select class="filter-select" id="txTypeFilter" onchange="filterTransactionsTable()">
                        <option value="ALL">All Types</option>
                        <option value="EXPENSE">Expenses Only</option>
                        <option value="INCOME">Income Only</option>
                    </select>
                    <a href="/api/export/csv" class="btn-secondary" style="text-decoration: none;">📥 Export CSV</a>
                </div>
            </div>

            <!-- Transactions Table -->
            <div class="tx-table-container">
                <table class="full-tx-table">
                    <thead>
                        <tr>
                            <th># ID</th>
                            <th>Date</th>
                            <th>Type</th>
                            <th>Category</th>
                            <th>Scope</th>
                            <th>Amount</th>
                            <th>Payment Method</th>
                            <th>Description</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody id="fullTxTableBody">
                        <!-- Populated via API -->
                    </tbody>
                </table>
            </div>
        </div>

        <!-- ======================================================== -->
        <!-- VIEW 3: BUDGETS MANAGEMENT -->
        <!-- ======================================================== -->
        <div id="view-budgets" class="view-page">
            <div class="top-header">
                <div>
                    <h1 class="app-title">Monthly Budgets & Alerts</h1>
                    <p style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">Evaluated in real-time via PL/SQL procedure GET_BUDGET_STATUS</p>
                </div>
                <button class="btn-primary" onclick="openBudgetModal()">+ Set New Budget</button>
            </div>

            <div class="tx-table-container">
                <table class="full-tx-table">
                    <thead>
                        <tr>
                            <th># ID</th>
                            <th>Scope / Category</th>
                            <th>Allocated Budget</th>
                            <th>Actual Spending</th>
                            <th>Remaining</th>
                            <th>Utilization %</th>
                            <th>Threshold</th>
                            <th>Alert Status</th>
                        </tr>
                    </thead>
                    <tbody id="budgetTableBody">
                        <!-- Populated via API -->
                    </tbody>
                </table>
            </div>
        </div>

        <!-- ======================================================== -->
        <!-- VIEW 4: ANALYTICS -->
        <!-- ======================================================== -->
        <div id="view-analytics" class="view-page">
            <div class="top-header">
                <div>
                    <h1 class="app-title">Financial Analytics & Insights</h1>
                    <p style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">Computed with Pandas and NumPy aggregations</p>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div class="card">
                    <div class="card-header"><span class="card-title">12-Month Income vs Expense Bar Chart</span></div>
                    <div style="height: 280px;"><canvas id="analyticsBarChart"></canvas></div>
                </div>
                <div class="card">
                    <div class="card-header"><span class="card-title">Category Spending Share</span></div>
                    <div style="height: 280px;"><canvas id="analyticsCatBarChart"></canvas></div>
                </div>
            </div>
        </div>

        <!-- ======================================================== -->
        <!-- VIEW 5: REPORTS -->
        <!-- ======================================================== -->
        <div id="view-reports" class="view-page">
            <div class="top-header">
                <div>
                    <h1 class="app-title">Reports & Statements</h1>
                    <p style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">Export official spreadsheets and printable PDF financial statements</p>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div class="card" style="text-align: center; padding: 40px 20px;">
                    <div style="font-size: 48px; margin-bottom: 12px;">📊</div>
                    <h3 style="margin-bottom: 8px;">Export All Transactions to CSV</h3>
                    <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 20px;">Download complete spreadsheet audit log compatible with Microsoft Excel & Google Sheets.</p>
                    <a href="/api/export/csv" class="btn-primary" style="text-decoration: none;">Download CSV Spreadsheet</a>
                </div>
                <div class="card" style="text-align: center; padding: 40px 20px;">
                    <div style="font-size: 48px; margin-bottom: 12px;">📄</div>
                    <h3 style="margin-bottom: 8px;">PDF Financial Statement</h3>
                    <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 20px;">Generate formatted PDF statement with executive KPI summary, category table, and recent transactions.</p>
                    <a href="/api/export/pdf" class="btn-primary" style="text-decoration: none;">Download PDF Statement</a>
                </div>
            </div>
        </div>

    </div>

    <!-- ======================================================== -->
    <!-- ADD TRANSACTION MODAL (Calls PL/SQL ADD_TRANSACTION) -->
    <!-- ======================================================== -->
    <div class="modal-overlay" id="addTxModal">
        <div class="modal-card">
            <h2 class="modal-title" id="modalTxTitle">Record New Transaction</h2>

            <div class="form-group">
                <label class="form-label">Transaction Type</label>
                <select class="form-select" id="formTxType" onchange="onModalTypeChange()">
                    <option value="EXPENSE">Expense</option>
                    <option value="INCOME">Income</option>
                </select>
            </div>

            <div class="form-group">
                <label class="form-label">Amount (₹) *</label>
                <input type="number" step="0.01" class="form-input" id="formTxAmount" placeholder="e.g. 1500.00" required>
            </div>

            <div class="form-group">
                <label class="form-label">Category *</label>
                <select class="form-select" id="formTxCategory">
                    <!-- Populated via API -->
                </select>
            </div>

            <div class="form-group" id="formScopeGroup">
                <label class="form-label">Expense Scope</label>
                <select class="form-select" id="formTxScope">
                    <option value="NEED">NEED</option>
                    <option value="WANTS">WANTS</option>
                    <option value="SELF">SELF</option>
                    <option value="ANONYMOUS">ANONYMOUS</option>
                    <option value="INVESTMENT">INVESTMENT</option>
                    <option value="SAVINGS">SAVINGS</option>
                    <option value="OTHER">OTHER</option>
                </select>
            </div>

            <div class="form-group">
                <label class="form-label">Date *</label>
                <input type="date" class="form-input" id="formTxDate" value="${new Date().toISOString().slice(0, 10)}">
            </div>

            <div class="form-group">
                <label class="form-label">Payment Method</label>
                <select class="form-select" id="formTxMethod">
                    <option value="UPI">UPI</option>
                    <option value="Net Banking">Net Banking</option>
                    <option value="Credit Card">Credit Card</option>
                    <option value="Debit Card">Debit Card</option>
                    <option value="Cash">Cash</option>
                </select>
            </div>

            <div class="form-group">
                <label class="form-label">Description *</label>
                <input type="text" class="form-input" id="formTxDesc" placeholder="e.g. Grocery shopping">
            </div>

            <div class="modal-actions">
                <button class="btn-secondary" onclick="closeAddModal()">Cancel</button>
                <button class="btn-primary" onclick="submitTransaction()">Save to Oracle DB</button>
            </div>
        </div>
    </div>

    <!-- ======================================================== -->
    <!-- SET BUDGET MODAL (Calls PL/SQL SAVE_BUDGET) -->
    <!-- ======================================================== -->
    <div class="modal-overlay" id="setBudgetModal">
        <div class="modal-card">
            <h2 class="modal-title">Set Monthly Budget</h2>

            <div class="form-group">
                <label class="form-label">Year</label>
                <input type="number" class="form-input" id="budgetYear" value="2024">
            </div>

            <div class="form-group">
                <label class="form-label">Month</label>
                <select class="form-select" id="budgetMonth">
                    <option value="1">1 - January</option>
                    <option value="2">2 - February</option>
                    <option value="3">3 - March</option>
                    <option value="4">4 - April</option>
                    <option value="5">5 - May</option>
                    <option value="6">6 - June</option>
                    <option value="7">7 - July</option>
                    <option value="8">8 - August</option>
                    <option value="9">9 - September</option>
                    <option value="10">10 - October</option>
                    <option value="11">11 - November</option>
                    <option value="12">12 - December</option>
                </select>
            </div>

            <div class="form-group">
                <label class="form-label">Scope</label>
                <select class="form-select" id="budgetCategory">
                    <option value="">OVERALL MONTHLY BUDGET (All Categories)</option>
                    <!-- Categories populated -->
                </select>
            </div>

            <div class="form-group">
                <label class="form-label">Budget Amount (₹) *</label>
                <input type="number" class="form-input" id="budgetAmount" placeholder="e.g. 50000">
            </div>

            <div class="form-group">
                <label class="form-label">Alert Threshold (%)</label>
                <input type="number" class="form-input" id="budgetThreshold" value="80">
            </div>

            <div class="modal-actions">
                <button class="btn-secondary" onclick="closeBudgetModal()">Cancel</button>
                <button class="btn-primary" onclick="submitBudget()">Save Budget</button>
            </div>
        </div>
    </div>

    <!-- JavaScript Application Logic -->
    <script>
        let currentYear = 2024;
        let currentMonth = null;
        let chartMode = 'EXPENSES';
        let allTransactionsCache = [];
        let allCategoriesCache = [];

        let monthlyChartInstance = null;
        let typeDonutInstance = null;
        let categoryDonutInstance = null;
        let analyticsBarInstance = null;
        let analyticsCatBarInstance = null;

        // Switch Tabs
        function switchTab(tabName) {
            document.querySelectorAll('.view-page').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

            const target = document.getElementById(`view-${tabName}`);
            if (target) target.classList.add('active');

            const navBtn = document.getElementById(`nav-${tabName}`);
            if (navBtn) navBtn.classList.add('active');

            if (tabName === 'dashboard') {
                loadDashboardData();
            } else if (tabName === 'transactions') {
                loadTransactionsTable();
            } else if (tabName === 'budgets') {
                loadBudgetsTable();
            } else if (tabName === 'analytics') {
                loadAnalyticsCharts();
            }
        }

        // Toggle Month Popup
        function toggleMonthPopup() {
            document.getElementById('monthPopup').classList.toggle('show');
        }

        function selectMonth(m, label) {
            currentMonth = m;
            document.getElementById('selected-m-label').innerText = label;
            document.getElementById('monthPopup').classList.remove('show');
            loadDashboardData();
        }

        function changeYear(yr, btn) {
            currentYear = yr;
            document.querySelectorAll('.year-pill').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            loadDashboardData();
        }

        function setChartMode(mode) {
            chartMode = mode;
            document.getElementById('btn-toggle-exp').classList.toggle('active', mode === 'EXPENSES');
            document.getElementById('btn-toggle-inc').classList.toggle('active', mode === 'INCOME');
            document.getElementById('monthly-chart-title').innerText = (mode === 'EXPENSES') ? 'Expenses by Month' : 'Income by Month';
            loadDashboardData();
        }

        // Load Dashboard Data
        async function loadDashboardData() {
            let url = `/api/summary?year=${currentYear || ''}&month=${currentMonth || ''}`;
            const res = await fetch(url);
            const data = await res.json();

            // 1. Update 4 Stat Cards
            document.getElementById('card-income').innerText = data.kpi.formatted_income;
            document.getElementById('card-expenses').innerText = data.kpi.formatted_expenses;
            document.getElementById('card-expense-pct').innerText = data.kpi.expense_pct + '%';
            document.getElementById('card-savings-pct').innerText = data.kpi.savings_pct + '%';

            // 2. Render Monthly Area Chart
            renderMonthlyChart(data.monthly);

            // 3. Render Type Donut Chart
            renderTypeDonut(data.types);

            // 4. Render Category Donut Chart
            renderCategoryDonut(data.categories);

            // 5. Populate Category Summary Table
            renderCategoryTable(data.categories);
        }

        function renderMonthlyChart(monthlyData) {
            const ctx = document.getElementById('monthlyAreaChart').getContext('2d');
            const labels = monthlyData.map(m => m.MONTH_NAME);
            const values = (chartMode === 'EXPENSES') ? monthlyData.map(m => m.EXPENSES) : monthlyData.map(m => m.INCOME);

            const gradient = ctx.createLinearGradient(0, 0, 0, 180);
            gradient.addColorStop(0, 'rgba(124, 92, 252, 0.40)');
            gradient.addColorStop(1, 'rgba(237, 233, 254, 0.05)');

            if (monthlyChartInstance) monthlyChartInstance.destroy();

            monthlyChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        borderColor: '#7C5CFC',
                        borderWidth: 2.5,
                        backgroundColor: gradient,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#7C5CFC',
                        pointRadius: 3,
                        pointHoverRadius: 5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: {
                            grid: { color: 'rgba(226, 232, 240, 0.6)', borderDash: [4, 4] },
                            ticks: {
                                font: { size: 10 },
                                color: '#94A3B8',
                                callback: val => '₹' + (val >= 1000 ? Math.round(val/1000) + 'K' : val)
                            }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { font: { size: 10 }, color: '#94A3B8' }
                        }
                    }
                }
            });
        }

        function renderTypeDonut(typeData) {
            const ctx = document.getElementById('typeDonutChart').getContext('2d');
            if (typeDonutInstance) typeDonutInstance.destroy();

            const labels = typeData.map(t => t.EXPENSE_TYPE);
            const dataVals = typeData.map(t => t.AMOUNT);

            typeDonutInstance = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: dataVals,
                        backgroundColor: ['#7C5CFC', '#B4A5F5', '#818CF8', '#C4B5FD', '#DDD6FE', '#38BDF8'],
                        borderWidth: 2,
                        borderColor: '#FFFFFF'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '72%',
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                boxWidth: 10,
                                font: { size: 10 },
                                color: '#1E1B4B'
                            }
                        }
                    }
                }
            });
        }

        function renderCategoryDonut(catData) {
            const ctx = document.getElementById('categoryDonutChart').getContext('2d');
            if (categoryDonutInstance) categoryDonutInstance.destroy();

            const topCats = catData.slice(0, 7);
            const labels = topCats.map(c => c.CATEGORY_NAME);
            const dataVals = topCats.map(c => c.AMOUNT);

            categoryDonutInstance = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: dataVals,
                        backgroundColor: [
                            '#7C5CFC', '#A78BFA', '#C4B5FD', '#DDD6FE',
                            '#F472B6', '#38BDF8', '#FBBF24', '#34D399'
                        ],
                        borderWidth: 2,
                        borderColor: '#FFFFFF'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '72%',
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                boxWidth: 10,
                                font: { size: 9 },
                                color: '#1E1B4B'
                            }
                        }
                    }
                }
            });
        }

        function renderCategoryTable(catData) {
            const tbody = document.getElementById('categoryTableBody');
            tbody.innerHTML = '';
            let total = 0;

            catData.forEach(item => {
                total += item.AMOUNT;
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td><span class="tree-icon">+</span>${item.CATEGORY_NAME}</td>
                    <td class="amount-cell">₹${item.AMOUNT.toLocaleString('en-IN')}</td>
                `;
                tbody.appendChild(row);
            });

            document.getElementById('categoryTableTotal').innerText = '₹' + total.toLocaleString('en-IN');
        }

        // ========================================================
        // TRANSACTIONS TABLE MANAGEMENT
        // ========================================================
        async function loadTransactionsTable() {
            const res = await fetch('/api/transactions');
            allTransactionsCache = await res.json();
            filterTransactionsTable();
        }

        function filterTransactionsTable() {
            const q = document.getElementById('txSearchInput').value.toLowerCase();
            const typeFilter = document.getElementById('txTypeFilter').value;
            const tbody = document.getElementById('fullTxTableBody');
            tbody.innerHTML = '';

            const filtered = allTransactionsCache.filter(tx => {
                const matchType = (typeFilter === 'ALL' || tx.transaction_type === typeFilter);
                const matchQuery = (
                    tx.description.toLowerCase().includes(q) ||
                    tx.category_name.toLowerCase().includes(q) ||
                    tx.payment_method.toLowerCase().includes(q)
                );
                return matchType && matchQuery;
            });

            if (filtered.length === 0) {
                tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: #94A3B8; padding: 24px;">No transactions matching filter</td></tr>`;
                return;
            }

            filtered.forEach(tx => {
                const isInc = tx.transaction_type === 'INCOME';
                const badge = isInc ? `<span class="badge-income">INCOME</span>` : `<span class="badge-expense">EXPENSE</span>`;
                const amtColor = isInc ? '#059669' : '#DC2626';
                const amtPrefix = isInc ? '+₹' : '-₹';

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="font-weight: 700; color: #64748B;">#${tx.transaction_id}</td>
                    <td>${tx.transaction_date}</td>
                    <td>${badge}</td>
                    <td style="font-weight: 600;">${tx.category_name}</td>
                    <td><span style="font-size: 11px; background: #F1F5F9; padding: 2px 6px; border-radius: 4px;">${tx.expense_type}</span></td>
                    <td style="font-weight: 700; color: ${amtColor};">${amtPrefix}${tx.amount.toLocaleString('en-IN')}</td>
                    <td>${tx.payment_method}</td>
                    <td>${tx.description}</td>
                    <td><button class="btn-delete-row" onclick="deleteTransaction(${tx.transaction_id})">Delete</button></td>
                `;
                tbody.appendChild(tr);
            });
        }

        async function deleteTransaction(txId) {
            if (!confirm(`Are you sure you want to permanently delete transaction #${txId} from Oracle Database?`)) {
                return;
            }
            const res = await fetch('/api/delete-transaction', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ transaction_id: txId })
            });
            const data = await res.json();
            if (data.success) {
                alert('Transaction deleted successfully from Oracle DB!');
                loadTransactionsTable();
                loadDashboardData();
            } else {
                alert('Error: ' + data.error);
            }
        }

        // ========================================================
        // ADD TRANSACTION MODAL
        // ========================================================
        async function openAddModal(defaultType) {
            document.getElementById('formTxType').value = defaultType;
            onModalTypeChange();
            await populateCategoryDropdown(defaultType);
            document.getElementById('formTxDate').value = new Date().toISOString().slice(0, 10);
            document.getElementById('addTxModal').classList.add('show');
        }

        function closeAddModal() {
            document.getElementById('addTxModal').classList.remove('show');
        }

        function onModalTypeChange() {
            const t = document.getElementById('formTxType').value;
            document.getElementById('modalTxTitle').innerText = (t === 'EXPENSE') ? 'Add New Expense' : 'Add New Income';
            document.getElementById('formScopeGroup').style.display = (t === 'EXPENSE') ? 'block' : 'none';
            populateCategoryDropdown(t);
        }

        async function populateCategoryDropdown(type) {
            if (allCategoriesCache.length === 0) {
                const res = await fetch('/api/categories');
                allCategoriesCache = await res.json();
            }
            const select = document.getElementById('formTxCategory');
            select.innerHTML = '';
            const filtered = allCategoriesCache.filter(c => type === 'ALL' || c.category_type === type || c.category_type === 'BOTH');
            filtered.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.category_id;
                opt.text = c.category_name;
                select.appendChild(opt);
            });
        }

        async function submitTransaction() {
            const type = document.getElementById('formTxType').value;
            const amount = parseFloat(document.getElementById('formTxAmount').value);
            const category_id = parseInt(document.getElementById('formTxCategory').value);
            const scope = (type === 'EXPENSE') ? document.getElementById('formTxScope').value : 'SAVINGS';
            const date = document.getElementById('formTxDate').value;
            const method = document.getElementById('formTxMethod').value;
            const desc = document.getElementById('formTxDesc').value.trim();

            if (!amount || amount <= 0) {
                alert('Please enter a valid amount strictly greater than zero.');
                return;
            }
            if (!desc) {
                alert('Please enter a description.');
                return;
            }

            const res = await fetch('/api/add-transaction', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    transaction_type: type,
                    amount: amount,
                    category_id: category_id,
                    expense_type: scope,
                    transaction_date: date,
                    payment_method: method,
                    description: desc
                })
            });

            const data = await res.json();
            if (data.success) {
                alert(`Transaction #${data.transaction_id} recorded in Oracle Database!`);
                closeAddModal();
                loadDashboardData();
                loadTransactionsTable();
            } else {
                alert('Database Error: ' + data.error);
            }
        }

        // ========================================================
        // BUDGETS MODULE
        // ========================================================
        async function loadBudgetsTable() {
            const res = await fetch(`/api/budgets?year=${currentYear}&month=1`);
            const budgets = await res.json();
            const tbody = document.getElementById('budgetTableBody');
            tbody.innerHTML = '';

            budgets.forEach(b => {
                let badge = '<span class="badge-income">● OK</span>';
                if (b.alert_status === 'WARNING') badge = '<span style="background: #FEF3C7; color: #D97706; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: 700;">● WARNING</span>';
                if (b.alert_status === 'EXCEEDED') badge = '<span class="badge-expense">● EXCEEDED</span>';

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="font-weight: 700; color: #64748B;">#${b.budget_id}</td>
                    <td style="font-weight: 600;">${b.category_name}</td>
                    <td style="font-weight: 700;">₹${b.budget_amount.toLocaleString('en-IN')}</td>
                    <td style="color: #64748B;">₹${b.actual_spending.toLocaleString('en-IN')}</td>
                    <td style="font-weight: 700;">₹${b.remaining_budget.toLocaleString('en-IN')}</td>
                    <td>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <div style="flex: 1; height: 8px; background: #E2E8F0; border-radius: 4px; overflow: hidden;">
                                <div style="width: ${Math.min(b.utilization_pct, 100)}%; height: 100%; background: ${b.alert_status === 'EXCEEDED' ? '#DC2626' : (b.alert_status === 'WARNING' ? '#D97706' : '#7C5CFC')};"></div>
                            </div>
                            <span style="font-size: 11px; font-weight: 700;">${b.utilization_pct}%</span>
                        </div>
                    </td>
                    <td>${b.alert_threshold}%</td>
                    <td>${badge}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        async function openBudgetModal() {
            if (allCategoriesCache.length === 0) {
                const res = await fetch('/api/categories');
                allCategoriesCache = await res.json();
            }
            const select = document.getElementById('budgetCategory');
            select.innerHTML = '<option value="">OVERALL MONTHLY BUDGET (All Categories)</option>';
            allCategoriesCache.filter(c => c.category_type === 'EXPENSE').forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.category_id;
                opt.text = c.category_name;
                select.appendChild(opt);
            });
            document.getElementById('setBudgetModal').classList.add('show');
        }

        function closeBudgetModal() {
            document.getElementById('setBudgetModal').classList.remove('show');
        }

        async function submitBudget() {
            const yr = parseInt(document.getElementById('budgetYear').value);
            const mo = parseInt(document.getElementById('budgetMonth').value);
            const catId = document.getElementById('budgetCategory').value ? parseInt(document.getElementById('budgetCategory').value) : null;
            const amt = parseFloat(document.getElementById('budgetAmount').value);
            const thr = parseInt(document.getElementById('budgetThreshold').value);

            if (!amt || amt <= 0) {
                alert('Please enter a valid budget amount.');
                return;
            }

            const res = await fetch('/api/save-budget', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    year: yr,
                    month: mo,
                    category_id: catId,
                    amount: amt,
                    alert_threshold: thr
                })
            });
            const data = await res.json();
            if (data.success) {
                alert(`Budget saved successfully in Oracle DB!`);
                closeBudgetModal();
                loadBudgetsTable();
            } else {
                alert('Error: ' + data.error);
            }
        }

        // ========================================================
        // ANALYTICS MODULE
        // ========================================================
        async function loadAnalyticsCharts() {
            const res = await fetch(`/api/summary?year=${currentYear}`);
            const data = await res.json();

            // Bar Chart
            const ctx1 = document.getElementById('analyticsBarChart').getContext('2d');
            if (analyticsBarInstance) analyticsBarInstance.destroy();

            analyticsBarInstance = new Chart(ctx1, {
                type: 'bar',
                data: {
                    labels: data.monthly.map(m => m.MONTH_NAME),
                    datasets: [
                        { label: 'Income', data: data.monthly.map(m => m.INCOME), backgroundColor: '#10B981', borderRadius: 4 },
                        { label: 'Expenses', data: data.monthly.map(m => m.EXPENSES), backgroundColor: '#7C5CFC', borderRadius: 4 }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { ticks: { callback: v => '₹' + (v >= 1000 ? Math.round(v/1000) + 'K' : v) } }
                    }
                }
            });

            // Category Horizontal Bar Chart
            const ctx2 = document.getElementById('analyticsCatBarChart').getContext('2d');
            if (analyticsCatBarInstance) analyticsCatBarInstance.destroy();

            const topCats = data.categories.slice(0, 6);
            analyticsCatBarInstance = new Chart(ctx2, {
                type: 'bar',
                data: {
                    labels: topCats.map(c => c.CATEGORY_NAME),
                    datasets: [{
                        label: 'Spending',
                        data: topCats.map(c => c.AMOUNT),
                        backgroundColor: '#8B5CF6',
                        borderRadius: 4
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { ticks: { callback: v => '₹' + (v >= 1000 ? Math.round(v/1000) + 'K' : v) } }
                    }
                }
            });
        }

        // Initial Load
        loadDashboardData();
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/summary")
def api_summary():
    year_param = request.args.get("year")
    month_param = request.args.get("month")

    year = int(year_param) if year_param and year_param.isdigit() else None
    month = int(month_param) if month_param and month_param.isdigit() else None

    # Call Analytics & PL/SQL functions
    kpi = analytics_service.get_kpi_metrics(year=year, month=month)
    kpi["formatted_income"] = format_compact_inr(kpi["total_income"])
    kpi["formatted_expenses"] = format_compact_inr(kpi["total_expenses"])
    kpi["formatted_savings"] = format_compact_inr(kpi["savings"])

    monthly_df = analytics_service.get_monthly_trend_analysis(year=year)
    monthly_data = monthly_df.to_dict(orient="records")

    cat_df = analytics_service.get_category_distribution(year=year, month=month)
    categories_data = cat_df.to_dict(orient="records")

    type_df = analytics_service.get_expense_type_distribution(year=year, month=month)
    type_data = type_df.to_dict(orient="records")

    return jsonify({
        "kpi": kpi,
        "monthly": monthly_data,
        "categories": categories_data,
        "types": type_data
    })


@app.route("/api/transactions")
def api_transactions():
    txs = tx_service.get_transactions(limit=200)
    data = []
    for t in txs:
        data.append({
            "transaction_id": t.transaction_id,
            "transaction_date": format_date_display(t.transaction_date),
            "transaction_type": t.transaction_type,
            "category_name": t.category_name,
            "expense_type": t.expense_type,
            "amount": t.amount,
            "payment_method": t.payment_method,
            "description": t.description
        })
    return jsonify(data)


@app.route("/api/categories")
def api_categories():
    cats = tx_service.get_categories()
    return jsonify([{
        "category_id": c.category_id,
        "category_name": c.category_name,
        "category_type": c.category_type
    } for c in cats])


@app.route("/api/add-transaction", methods=["POST"])
def api_add_transaction():
    data = request.json or {}
    try:
        ok, tx_id, msg = tx_service.add_transaction(
            category_id=int(data["category_id"]),
            transaction_type=data["transaction_type"],
            expense_type=data.get("expense_type", "NEED"),
            amount=float(data["amount"]),
            transaction_date=datetime.strptime(data["transaction_date"], "%Y-%m-%d").date(),
            payment_method=data.get("payment_method", "UPI"),
            description=data["description"],
            notes=data.get("notes", "")
        )
        return jsonify({"success": ok, "transaction_id": tx_id, "message": msg})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/delete-transaction", methods=["POST"])
def api_delete_transaction():
    data = request.json or {}
    tx_id = int(data.get("transaction_id", 0))
    ok, msg = tx_service.delete_transaction(tx_id)
    return jsonify({"success": ok, "message": msg})


@app.route("/api/budgets")
def api_budgets():
    year = int(request.args.get("year", 2024))
    month = int(request.args.get("month", 1))
    budgets = budget_service.get_budget_status(year=year, month=month)
    return jsonify([{
        "budget_id": b.budget_id,
        "category_name": b.category_name,
        "budget_amount": b.budget_amount,
        "actual_spending": b.actual_spending,
        "remaining_budget": b.remaining_budget,
        "utilization_pct": b.utilization_pct,
        "alert_threshold": b.alert_threshold,
        "alert_status": b.alert_status
    } for b in budgets])


@app.route("/api/save-budget", methods=["POST"])
def api_save_budget():
    data = request.json or {}
    try:
        ok, b_id, msg = budget_service.save_budget(
            year=int(data["year"]),
            month=int(data["month"]),
            category_id=int(data["category_id"]) if data.get("category_id") else None,
            amount=float(data["amount"]),
            alert_threshold=int(data.get("alert_threshold", 80))
        )
        return jsonify({"success": ok, "budget_id": b_id, "message": msg})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/export/csv")
def api_export_csv():
    file_path = BASE_DIR / "expense_transactions.csv"
    ok, _ = report_service.export_transactions_csv(str(file_path))
    if ok and file_path.exists():
        return send_file(str(file_path), as_attachment=True, download_name="expense_transactions.csv")
    return jsonify({"error": "Failed to generate CSV export"}), 500


@app.route("/api/export/pdf")
def api_export_pdf():
    file_path = BASE_DIR / "financial_statement_2024.pdf"
    ok, _ = report_service.export_pdf_report(str(file_path), year=2024)
    if ok and file_path.exists():
        return send_file(str(file_path), as_attachment=True, download_name="financial_statement_2024.pdf")
    return jsonify({"error": "Failed to generate PDF export"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
