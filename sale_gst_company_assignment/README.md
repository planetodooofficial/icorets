# Sale Order & Pipeline Company Assignment Based on GST (Odoo 19)

## 📌 Overview
This custom Odoo 19 module (`sale_gst_company_assignment`) provides a dedicated control panel tool to match and reassign branch companies on Sale Orders and all related transaction pipeline records (SOL, deliveries, stock moves, move lines, invoices, and invoice lines) based on GST matching rules.

It uses the exact company matching logic from `warehouse_gst_company_assignment` (`gst_code_matching_com` on `res.company` and `gst_code` on `res.partner`).

---

## 🎯 Features

### 1. Dedicated Control Tool (`sale.company.reassignment.tool`)
- Menu: **Sales > Configuration > SO Company Reassignment by GST**.
- Fields:
  - **Source Company**: The company currently owning the Sale Orders.
  - **GSTIN Unit / Partner (`gstin_id`)**: Select the GSTIN partner/unit.
  - **GST Code**: Auto-resolved from `gstin_id.gst_code` (e.g. `DL`, `HR`, `MH`, etc.).
  - **Target / Destination Company**: Auto-resolved from the branch company hierarchy matching `res.company.gst_code_matching_com`.
  - **Model Target**: Choose a specific model to update or select All for complete pipeline processing.

### 2. Live Record Count Fetching ("Fetch Record Counts")
Before executing any update, clicking **Fetch Record Counts** runs fast direct SQL queries and updates the real-time metric cards for:
- 📦 **Sale Orders** (`sale.order`)
- 📄 **Sale Order Lines** (`sale.order.line`)
- 🚚 **Delivery Pickings** (`stock.picking`)
- 🔄 **Stock Moves & Move Lines** (`stock.move`, `stock.move.line`)
- 📑 **Invoices / Journal Entries** (`account.move`)
- 🧾 **Invoice Lines / Journal Items** (`account.move.line`)
- 🎯 **Total Count for the Selected Model**

### 3. Step-by-Step Individual Action Buttons & Pipeline Update
The dashboard includes dedicated buttons to update records one-by-one or all at once:
- **1. Update Sale Orders**: Updates `company_id` and marks `is_company_transferred = True` on matching `sale.order`.
- **2. Update Sale Order Lines**: Updates `sale.order.line`.
- **3. Update Delivery Pickings**: Updates `stock.picking`.
- **4. Update Stock Moves & Lines**: Updates `stock.move` and `stock.move.line`.
- **5. Update Invoices**: Updates `account.move`.
- **6. Update Invoice Lines**: Updates `account.move.line`.
- **⚡ Update Selected Model**: Updates the model selected in the dropdown.
- **🚀 Update Entire Pipeline**: Executes all updates in atomic sequence inside an isolated savepoint.

### 4. Historical Tracking Boolean (`is_company_transferred`)
The boolean field `is_company_transferred` (`True` when transferred) is added and automatically updated across all affected models:
- `sale.order`
- `sale.order.line`
- `stock.picking`
- `stock.move`
- `stock.move.line`
- `account.move`
- `account.move.line`

Filters for `is_company_transferred = True` are available in search views and list views.

### 5. Persistent Audit Logging (`sale.company.reassignment.log`)
Every execution automatically creates an immutable audit log record tracking:
- Reference (`SO-LOG/%Y%m%d-%H%M%S`)
- Execution Date and Executing User
- Source Company & Target Company
- GSTIN Partner & GST Code
- Action Type / Model Targeted
- Number of records updated
- Status (`success`, `nothing_to_update`, `failed`)
- Detailed summary text
- Accessible via the form's notebook tab and dedicated menu: **Sales > Configuration > SO Company Reassignment Logs**.

---

## 🚀 Installation & Usage

1. **Install Module**:
   Add `sale_gst_company_assignment` to your Odoo 19 addons and update your app list.
2. **Open the Tool**:
   Navigate to **Sales > Configuration > SO Company Reassignment by GST**.
3. **Select Source Company & GSTIN Partner**:
   Select your source company and the GSTIN unit partner. The GST code and target branch company will be automatically resolved.
4. **Fetch Counts**:
   Click **🔍 Fetch Record Counts** to inspect eligible records.
5. **Execute Update**:
   Click individual buttons to update one-by-one, or click **🚀 Update Entire Pipeline** to update everything at once.
6. **Inspect Audit Log**:
   Review the results in the **Audit Execution History** notebook tab or under **SO Company Reassignment Logs**.
