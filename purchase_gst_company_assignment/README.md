# Purchase Order & Pipeline Company Assignment Based on GST

## Overview
This module automates the reassignment of company ownership across the **Purchase Orders and linked pipeline records** in Odoo 19:
- **Purchase Orders (`purchase.order`)**
- **Purchase Order Lines (`purchase.order.line`)**
- **Incoming Receipts / Pickings (`stock.picking`)**
- **Stock Moves & Move Lines (`stock.move`, `stock.move.line`)**
- **Vendor Bills / Account Moves (`account.move`)**
- **Bill Lines / Journal Items (`account.move.line`)**
- **Payments (`account.payment`)**
- **Payment Journal Entries & Lines (`account.move`, `account.move.line`)**
- **Reconciliations (`account.partial.reconcile`)**
- **Bank Statement Lines & Statements (`account.bank.statement.line`, `account.bank.statement`)**

## Key Features
1. **Hierarchy-Aware GST Matching**:
   Matches the vendor's GST code (`res.partner.gst_code` or first 2 digits of `vat`) with target branch companies (`res.company.gst_code_matching_com`).
2. **Atomic High-Performance Pipeline Update**:
   Updates all matching records in one single atomic transaction using optimized SQL execution.
3. **Audit Tracking**:
   Flags `is_company_transferred = True` on all modified records and records full run logs in `purchase.company.reassignment.log`.
4. **Clean UI**:
   - Menu: **Purchase > Configuration > PO Company Reassignment by GST**
   - **Fetch Record Counts**: Displays real-time matching count via toast notification.
   - **Update Entire Pipeline**: Executes batch reassignment with confirmation safety dialog.
   - **Audit Execution History**: Shows history table of previous runs directly on the session form.
