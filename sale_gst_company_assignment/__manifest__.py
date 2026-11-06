# -*- coding: utf-8 -*-
{
    "name": "Sale Order & Pipeline Company Assignment Based on GST",
    "version": "19.0.1.0.0",
    "category": "Sales/Sales",
    "summary": "Reassign branch company on Sale Orders, Lines, Deliveries, Stock Moves, Invoices, Payments, and Reconciliations based on GST matching",
    "description": """
Sale Order & Pipeline Company Assignment Based on GST (Odoo 19)
===============================================================
This module extends the hierarchy-aware GST company assignment architecture
to the entire Sales pipeline.

Key Capabilities:
-----------------
1. Matching Logic:
   - Uses the GST code from the warehouse/partner GST module (`warehouse_gst_company_assignment`).
   - Automatically matches `gstin_id` / partner GST code with branch companies (`res.company.gst_code_matching_com`) under the company hierarchy.

2. Comprehensive Operational Tool / Dashboard:
   - Form view with `gstin_id` selection, source company, and target branch.
   - Real-time count query button ("Fetch Record Counts") across all related pipeline models:
     * Sale Orders (sale.order)
     * Sale Order Lines (sale.order.line)
     * Delivery Pickings (stock.picking)
     * Stock Moves & Move Lines (stock.move, stock.move.line)
     * Invoices / Journal Entries (account.move)
     * Invoice Lines / Journal Items (account.move.line)
     * Payments (account.payment)
     * Payment Journal Entries & Items (account.move, account.move.line)
     * Reconciliations (account.partial.reconcile)
   - Step-by-step individual action buttons for each model.
   - Batch pipeline update button ("Update Entire Pipeline").
   - Direct high-performance SQL execution to handle large volumes of records without timeouts.

3. Complete Audit & Tracking:
   - Sets `is_company_transferred = True` across all modified records.
   - Persistent audit logging tracking executed actions, counts, users, and timestamps.
   - Dedicated menu: Sales > Configuration > SO Company Reassignment by GST.
    """,
    "author": "Antigravity",
    "website": "https://planet-odoo.com/",
    "license": "LGPL-3",
    "depends": [
        "base",
        "sale",
        "sale_stock",
        "stock",
        "account",
        "warehouse_gst_company_assignment",
        "gts_account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_company_tool_views.xml",
        "views/sale_company_log_views.xml",
        "views/sale_order_views.xml",
        "views/account_move_views.xml",
        "views/stock_picking_views.xml",
        "views/account_payment_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
