# Automatic Warehouse Company Assignment Based on GST Code (Odoo 19)

## 📌 Overview
This custom Odoo 19 module provides an automated, hierarchy-aware, and safe mechanism to assign branch companies to existing warehouses based on GST code matching, complete with persistent audit tracking and historical flags on all affected tables.

---

## 🎯 Features

### 1. Company GST Matching Code (`res.company`)
- New field: `gst_code_matching_com` (Char) added to the Company form view.
- Configurable per branch (e.g., Delhi: `DL`, Chennai: `CH`, Haryana: `HR`, Maharashtra: `MH`, etc.).
- **Unique per parent company hierarchy**: Verified via `@api.constrains('gst_code_matching_com', 'parent_id')`.
- **Dynamic**: Supports any newly created branch purely by configuration; no hardcoded states or codes in Python.

### 2. Warehouse Matching (`stock.warehouse`)
- Matches:
  ```text
  warehouse.partner_id.gst_code == res.company.gst_code_matching_com
  ```
- Uses the existing `partner_id` and its `gst_code`.
- **No redundant GST code field** on `stock.warehouse`.
- Case-insensitive, trimmed comparison.
- Restricts matching to the warehouse's parent company hierarchy.
- Skips warehouses already assigned to the correct destination company.

### 3. Historical Flag (`is_company_transferred`) Across All 7 Modified Tables
To track which records were changed in the past and clearly identify them in the future, the boolean field `is_company_transferred` (`True` when transferred) is added and automatically updated across strictly the following 7 models:
- `stock.warehouse` (`stock_warehouse`)
- `stock.location` (`stock_location`)
- `stock.picking.type` (`stock_picking_type`)
- `stock.rule` (`stock_rule`)
- `stock.warehouse.orderpoint` (`stock_warehouse_orderpoint`)
- `stock.route` (`stock_route`)
- `stock.quant` (`stock_quant`)

Users and administrators can filter, view, or query `is_company_transferred = True` at any time to inspect all past assignments.

### 4. Comprehensive Audit Logging & Tracking (What is Done and Not Done)
Every execution (whether triggered from the Single Warehouse button or the Mass Batch Wizard) creates a persistent audit log:
- **Master Log Model (`warehouse.gst.assignment.log`)**:
  - `name`: Generated reference (e.g. `GST-LOG/20261104-123000`)
  - `execution_date`: Date and time of execution
  - `user_id`: User who executed the action
  - `source`: `single` (Warehouse button) or `wizard` (Batch wizard)
  - `total_processed`, `total_success`, `total_already_matched`, `total_skipped`, `total_failed`
  - Full execution summary text
- **Itemized Details Model (`warehouse.gst.assignment.log.line`)**:
  - Records exact status per warehouse:
    - ✅ **Done / Updated** (`success`): Warehouse and configuration reallocated
    - ℹ️ **Already Matched** (`already_matched`): Already assigned to target company
    - ⚠️ **Skipped** (`skipped`): Contact lacks GST code
    - ❌ **Failed** (`failed`): Validation/safety blocked with exact reason/error message
  - **`is_done` flag**: Easily filter what was completed (`is_done = True`) vs what was not (`is_done = False`).
  - Breakdown of affected record counts (`locations_count`, `picking_types_count`, `rules_count`, `orderpoints_count`).

### 5. User Interface & Reporting
- **Dedicated Navigation**: **Inventory > Configuration > Warehouse GST Assignment Logs**.
- **Batch Processing Wizard (`warehouse.gst.company.match.wizard`)**:
  - Single-step batch execution: processes all selected warehouses directly.
  - "View Saved Audit Log" button to immediately jump to the persistent tracking report.

---

## 🚀 Installation & Configuration

### 1. Installation
Place `warehouse_gst_company_assignment` into your Odoo 19 addons directory and upgrade the module via **Apps > Update Apps List > Upgrade**.

### 2. Configure Branch Companies
1. Navigate to **Settings > Users & Companies > Companies**.
2. Open each branch company (e.g. "Delhi Branch").
3. Set the **GST Matching Code** (`gst_code_matching_com`) to its corresponding code (e.g. `DL`).
4. Save the company.

### 3. Configure Warehouse Contacts
1. Navigate to **Inventory > Configuration > Warehouses**.
2. Open the warehouse and click on its **Address** contact (`partner_id`).
3. Set the **GST Code** (`gst_code`) to the desired matching code (e.g. `DL`).
4. Save the contact.

---

## 🛠️ Usage

### Single Warehouse Assignment
1. Open any warehouse in **Inventory > Configuration > Warehouses**.
2. Click the **Match Company by GST Code** button in the header.
3. The warehouse and exclusive configuration records are updated and marked with `is_company_transferred = True`.
4. A persistent audit log entry is saved and accessible via the **GST Match Logs** smart button.

### Batch Processing
1. In **Inventory > Configuration > Warehouses**, switch to the List view.
2. Select the warehouses you want to evaluate.
3. Click **Actions > Mass Match Company by GST Code**.
4. Click **Run Matching**.
5. The wizard updates the matching warehouses, displays execution metrics, and links directly to the saved persistent audit log.
