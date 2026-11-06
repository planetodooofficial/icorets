# Journal Entry Company Assignment & Stock Picking Match (Odoo 19)

## Overview
This module integrates directly into the standard **Account Journal** (`account.journal`) form view, providing two powerful actions in the form header:

### 1. Button 1: Reassign Company (Manual / Batch)
- **Action**: Opens wizard `journal.company.reassign.wizard`.
- **Workflow**:
  1. Select **From / Source Company** (defaults to current company) and **To / Target Branch Company**.
  2. Click **`🔍 1. Fetch Matching Records`** to fetch and view exact counts of matching journal entries and items in this journal, plus any linked Sale Orders, Deliveries, Stock Moves, and Payments.
  3. Click **`🚀 2. Change Company on Records`** to atomically update all matching entries, lines, and linked Sale Order pipeline to the selected branch company (journal remains unchanged).

### 2. Button 2: Reassign by Stock Picking Match
- **Action**: Opens wizard `journal.picking.match.wizard`.
- **Workflow**:
  1. Scans journal entries whose `ref`, `name`, or line description matches a validated `stock.picking` number (e.g. `WH/IN/00001`, `WH/OUT/00002`, `BHI/IN/00010`, etc.), or direct stock moves.
  2. Resolves the branch company that owns each matched picking.
  3. Click **`🔍 1. Fetch & Preview Matches`** to inspect the itemized HTML summary showing which branch companies and pickings were matched.
  4. Click **`🚀 2. Reassign Company by Matched Picking`** to atomically reassign the entries, lines, and linked Sale Order operations to their matching picking's branch company (journal remains unchanged).

## Where to View Execution Logs
1. **Dedicated Menu**:
   - Go to **Invoicing / Accounting → Configuration → Journal Reassignment Logs**.
2. **From the Journal Form View**:
   - Open any journal (e.g. `Tax Invoices(MH)`) and click the **Transfer Logs** smart button in the top button box.

## Technical Details
- Persistent audit logs recorded in `journal.company.reassignment.log`.
- Safe atomic execution inside database savepoints.
- Automatic cache invalidation via `self.env.invalidate_all()`.
- Updates `account_move`, `account_move_line`, `sale_order`, `sale_order_line`, `stock_picking`, `stock_move`, `stock_move_line`, `account_payment`, and `account_partial_reconcile`.
- Flags all modified records with `is_company_transferred = TRUE`.
- No records deleted.
