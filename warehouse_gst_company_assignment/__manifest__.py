# -*- coding: utf-8 -*-
{
    "name": "Automatic Warehouse Company Assignment Based on GST Code",
    "version": "19.0.1.2.0",
    "category": "Inventory/Inventory",
    "summary": "Automatically assign correct branch company to existing warehouses based on GST code matching with complete audit logging and tracking",
    "description": """
Automatic Warehouse Company Assignment Based on GST Code (Odoo 19)
=================================================================
This module provides dynamic, hierarchy-aware, and safe assignment of branch
companies to existing warehouses based on GST code matching.

Key Features:
-------------
1. Company GST Matching Code:
   - Configurable `gst_code_matching_com` field on `res.company`.
   - Unique within the parent-company hierarchy (e.g. DL, CH, HR, MH).
   - Fully dynamic: works for any newly created branch without hardcoded values.

2. Warehouse Partner Matching:
   - Matches `warehouse.partner_id.gst_code == res.company.gst_code_matching_com`.
   - Restricts matching to the warehouse's parent company hierarchy.
   - Validates non-empty code, branch existence, and branch uniqueness.
   - Skips warehouses already assigned to the correct company.

3. Exclusive Warehouse Configuration & Quant Migration:
   - Reassigns company ownership ONLY on the 7 requested classes:
     * stock.warehouse (warehouse record)
     * stock.location (warehouse root and child hierarchy)
     * stock.picking.type (warehouse operation types)
     * stock.rule (warehouse routing rules)
     * stock.warehouse.orderpoint (warehouse reordering rules)
     * stock.route (warehouse exclusive routes)
     * stock.quant (warehouse on-hand inventory quants)
   - Sets `is_company_transferred = True` across all 7 modified tables.
   - Strictly preserves res.partner, ir.sequence, stock.move, and valuation layers without modification.

4. Single-Step Matching & Persistent Audit Logs:
   - Single-step execution: Select record(s) -> Action -> Run Matching.
   - Persistent audit log models (`warehouse.gst.assignment.log` and lines).
   - Itemized tracking of what was done and not done (`is_done`, status: success, already_matched, skipped, failed).
   - Dedicated menu: Inventory > Configuration > Warehouse GST Assignment Logs.
    """,
    "author": "Antigravity",
    "website": "https://planet-odoo.com/",
    "license": "LGPL-3",
    "depends": [
        "base",
        "stock",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_company_views.xml",
        "views/res_partner_views.xml",
        "views/stock_warehouse_views.xml",
        "views/stock_configuration_views.xml",
        "views/warehouse_gst_assignment_log_views.xml",
        "wizard/warehouse_gst_match_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
