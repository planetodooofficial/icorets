# -*- coding: utf-8 -*-
{
    "name": "Journal Entry Company Assignment & Stock Picking Match",
    "version": "19.0.1.0.0",
    "category": "Accounting/Accounting",
    "summary": "Reassign company on Journal Entries directly from Journal form view with manual selection and Stock Picking string matching",
    "description": """
Journal Entry Company Assignment & Stock Picking Match (Odoo 19)
================================================================
This module adds two dedicated company reassignment actions directly onto the Account Journal form view:

1. Button 1: Reassign Company (Manual / Batch)
   - Opens a dedicated company reassignment wizard for the active journal.
   - Choose Source Company (From) and Target Company / Branch (To).
   - Automatically maps to the matching journal in the destination company.
   - First action: "Fetch Records" to verify exact counts of journal entries and lines.
   - Second action: "Change Company" to atomically update all matched entries and lines.

2. Button 2: Reassign by Stock Picking Match
   - Scans all journal entries in the journal whose reference, name, or lines match a stock.picking number.
   - Identifies the target branch company that owns each matched picking.
   - First action: "Fetch & Preview Matches" to inspect how many entries match and which branch companies they belong to.
   - Second action: "Reassign by Stock Picking" to atomically reassign the entries and lines to the matching picking's branch company.
    """,
    "author": "Antigravity",
    "website": "https://planet-odoo.com/",
    "license": "LGPL-3",
    "depends": [
        "base",
        "sale",
        "sale_stock",
        "account",
        "stock",
        "stock_account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/journal_company_log_views.xml",
        "views/account_journal_views.xml",
        "views/journal_company_reassign_wizard_views.xml",
        "views/journal_picking_match_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
