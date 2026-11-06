# -*- coding: utf-8 -*-
{
    "name": "Purchase Order & Pipeline Company Assignment Based on GST",
    "version": "19.0.1.0.0",
    "category": "Inventory/Purchase",
    "summary": "Reassign branch company on Purchase Orders, Lines, Receipts, Stock Moves, Vendor Bills, Payments, and Reconciliations based on GST matching",
    "description": """
Purchase Order & Pipeline Company Assignment Based on GST (Odoo 19)
===================================================================
This module provides the complete automated GST company reassignment architecture
for the entire Purchase pipeline.

Key Capabilities:
-----------------
1. Matching Logic:
   - Uses the partner GST code from the warehouse/partner GST module (`warehouse_gst_company_assignment`).
   - Automatically resolves target branch companies (`res.company.gst_code_matching_com`) matching the vendor's GST code.

2. Comprehensive Operational Tool:
   - Control dashboard with source company, vendor GSTIN, and target branch.
   - Real-time count query button ("Fetch Record Counts") across all related purchase pipeline models:
     * Purchase Orders (purchase.order)
     * Purchase Order Lines (purchase.order.line)
     * Incoming Shipments / Receipts (stock.picking)
     * Stock Moves & Move Lines (stock.move, stock.move.line)
     * Vendor Bills / Account Moves (account.move)
     * Bill Lines / Journal Items (account.move.line)
     * Payments (account.payment)
     * Payment Journal Entries & Lines (account.move, account.move.line)
     * Reconciliations (account.partial.reconcile)
     * Bank Statement Lines & Bank Statements (account.bank.statement.line, account.bank.statement)
   - Atomic pipeline update button ("Update Entire Pipeline") to transfer all matching records in one transaction.
   - Direct high-performance SQL execution to handle large volumes of records without timeouts.

3. Complete Audit & Tracking:
   - Sets `is_company_transferred = True` across all modified records for tracking.
   - Persistent audit log records showing run history, counts, user, and timestamps.
   - Menu: Purchase > Configuration > PO Company Reassignment by GST.
    """,
    "author": "Antigravity",
    "website": "https://planet-odoo.com/",
    "license": "LGPL-3",
    "depends": [
        "base",
        "purchase",
        "purchase_stock",
        "stock",
        "account",
        "warehouse_gst_company_assignment",
        "gts_account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/purchase_company_tool_views.xml",
        "views/purchase_company_log_views.xml",
        "views/purchase_order_views.xml",
        "views/account_move_views.xml",
        "views/stock_picking_views.xml",
        "views/account_payment_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
