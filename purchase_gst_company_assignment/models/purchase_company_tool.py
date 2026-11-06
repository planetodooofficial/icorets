# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseCompanyReassignmentTool(models.Model):
    _name = "purchase.company.reassignment.tool"
    _description = "Purchase Order Company Reassignment Control Tool"
    _order = "id desc"

    name = fields.Char(
        string="Session Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("purchase.company.reassignment.tool") or "PO-COMP-NEW",
    )

    source_company_id = fields.Many2one(
        comodel_name="res.company",
        string="Source Company",
        required=True,
        default=lambda self: self.env.company,
        help="Select the company currently owning the Purchase Orders and linked records.",
    )

    gstin_id = fields.Many2one(
        comodel_name="res.partner",
        string="Vendor GSTIN / Partner",
        domain="[('is_gstin', '=', True)]",
        required=True,
        help="Select the vendor/partner whose GSTIN code determines the destination branch company.",
    )

    gst_code = fields.Char(
        string="Matched GST Code",
        compute="_compute_gst_code",
        store=True,
        readonly=False,
        help="2-digit GST State Code (e.g., 27 for Maharashtra, 07 for Delhi).",
    )

    target_company_id = fields.Many2one(
        comodel_name="res.company",
        string="Resolved Target Company",
        compute="_compute_target_company_id",
        store=True,
        readonly=False,
        help="Destination branch company resolved from the GST code under the company hierarchy.",
    )

    last_fetch_date = fields.Datetime(
        string="Last Checked On",
        readonly=True,
    )

    # Record Counters for Reporting
    count_purchase_orders = fields.Integer(string="Purchase Orders Count", readonly=True, default=0)
    count_purchase_order_lines = fields.Integer(string="PO Lines Count", readonly=True, default=0)
    count_pickings = fields.Integer(string="Receipts Count", readonly=True, default=0)
    count_stock_moves = fields.Integer(string="Stock Moves Count", readonly=True, default=0)
    count_stock_move_lines = fields.Integer(string="Stock Move Lines Count", readonly=True, default=0)
    count_invoices = fields.Integer(string="Vendor Bills Count", readonly=True, default=0)
    count_invoice_lines = fields.Integer(string="Bill Lines Count", readonly=True, default=0)
    count_payments = fields.Integer(string="Payments Count", readonly=True, default=0)
    count_payment_moves = fields.Integer(string="Payment Moves Count", readonly=True, default=0)
    count_payment_lines = fields.Integer(string="Payment Move Lines Count", readonly=True, default=0)
    count_partial_reconciles = fields.Integer(string="Reconciliations Count", readonly=True, default=0)
    count_bank_statement_lines = fields.Integer(string="Bank Statement Lines Count", readonly=True, default=0)
    count_bank_statements = fields.Integer(string="Bank Statements Count", readonly=True, default=0)

    # Execution Logs Relation
    log_ids = fields.One2many(
        comodel_name="purchase.company.reassignment.log",
        inverse_name="tool_id",
        string="Execution History",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "PO-COMP-NEW":
                vals["name"] = self.env["ir.sequence"].next_by_code("purchase.company.reassignment.tool") or f"PO-COMP-{fields.Datetime.now().strftime('%Y%m%d%H%M%S')}"
        return super().create(vals_list)

    @api.depends("gstin_id")
    def _compute_gst_code(self):
        for rec in self:
            code = False
            if rec.gstin_id:
                if hasattr(rec.gstin_id, "gst_code") and rec.gstin_id.gst_code:
                    code = str(rec.gstin_id.gst_code).strip()
                elif rec.gstin_id.vat and len(rec.gstin_id.vat) >= 2:
                    code = str(rec.gstin_id.vat[:2]).strip()
            rec.gst_code = code

    @api.depends("gst_code", "source_company_id")
    def _compute_target_company_id(self):
        Company = self.env["res.company"].sudo()
        for rec in self:
            target = False
            if rec.gst_code:
                # 1. Look for branch with matching gst_code_matching_com
                domain = [("gst_code_matching_com", "=", rec.gst_code)]
                if rec.source_company_id:
                    domain_child = domain + [("parent_id", "=", rec.source_company_id.id)]
                    target = Company.search(domain_child, limit=1)
                    if not target and rec.source_company_id.parent_id:
                        domain_sibling = domain + [("parent_id", "=", rec.source_company_id.parent_id.id)]
                        target = Company.search(domain_sibling, limit=1)

                if not target:
                    target = Company.search(domain, limit=1)

                # 2. Fallback: match by company vat starting with gst_code
                if not target:
                    vat_domain = [("vat", "=ilike", f"{rec.gst_code}%")]
                    if rec.source_company_id:
                        target = Company.search(vat_domain + [("parent_id", "=", rec.source_company_id.id)], limit=1)
                    if not target:
                        target = Company.search(vat_domain, limit=1)

            rec.target_company_id = target

    @api.onchange("gstin_id")
    def _onchange_gstin_id(self):
        if self.gstin_id:
            self._compute_gst_code()
            self._compute_target_company_id()

    def _ensure_transferred_columns_exist(self):
        """Ensure is_company_transferred column exists on all relevant tables."""
        cr = self.env.cr
        tables = [
            "purchase_order",
            "purchase_order_line",
            "stock_picking",
            "stock_move",
            "stock_move_line",
            "account_move",
            "account_move_line",
            "account_payment",
            "account_partial_reconcile",
            "account_bank_statement_line",
            "account_bank_statement",
        ]
        for tbl in tables:
            cr.execute("""
                SELECT 1 FROM information_schema.tables WHERE table_name = %s;
            """, [tbl])
            if cr.fetchone():
                cr.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = %s AND column_name = 'is_company_transferred';
                """, [tbl])
                if not cr.fetchone():
                    cr.execute(f'ALTER TABLE "{tbl}" ADD COLUMN "is_company_transferred" BOOLEAN DEFAULT FALSE;')
                    cr.execute(f'CREATE INDEX IF NOT EXISTS "{tbl}_is_company_transferred_idx" ON "{tbl}" ("is_company_transferred");')

    def _get_matching_po_ids(self):
        """Fetch purchase.order IDs that match source_company_id and gstin_id / gst_code."""
        self.ensure_one()
        if not self.source_company_id:
            return []

        cr = self.env.cr
        src_id = self.source_company_id.id
        gstin_id = self.gstin_id.id if self.gstin_id else False
        code = self.gst_code.strip() if self.gst_code else False

        # 1. Check if gstin_id column exists on purchase_order table
        cr.execute("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'purchase_order' AND column_name = 'gstin_id';
        """)
        has_gstin_col = bool(cr.fetchone())

        po_ids = []
        if has_gstin_col and gstin_id:
            cr.execute("""
                SELECT id FROM purchase_order 
                WHERE company_id = %s AND gstin_id = %s;
            """, [src_id, gstin_id])
            po_ids = [r[0] for r in cr.fetchall()]

        # 2. If no POs found via gstin_id or gstin_id column not set, search by vendor / partner GST
        if not po_ids and code:
            cr.execute("""
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'res_partner' AND column_name = 'gst_code';
            """)
            has_gst_code_col = bool(cr.fetchone())

            if has_gst_code_col:
                cr.execute("""
                    SELECT po.id FROM purchase_order po
                    JOIN res_partner rp ON po.partner_id = rp.id
                    WHERE po.company_id = %s AND (UPPER(TRIM(rp.gst_code)) = %s OR rp.vat LIKE %s);
                """, [src_id, code, f"{code}%"])
            else:
                cr.execute("""
                    SELECT po.id FROM purchase_order po
                    JOIN res_partner rp ON po.partner_id = rp.id
                    WHERE po.company_id = %s AND rp.vat LIKE %s;
                """, [src_id, f"{code}%"])
            po_ids = [r[0] for r in cr.fetchall()]

        # 3. Fallback: match by direct partner_id = gstin_id
        if not po_ids and gstin_id:
            cr.execute("""
                SELECT id FROM purchase_order 
                WHERE company_id = %s AND partner_id = %s;
            """, [src_id, gstin_id])
            po_ids = [r[0] for r in cr.fetchall()]

        return po_ids

    def _get_related_record_ids(self, po_ids):
        """Traverse the entire Purchase pipeline and return record IDs across all models."""
        self.ensure_one()
        cr = self.env.cr

        if not po_ids:
            return {
                "po_ids": [],
                "pol_ids": [],
                "picking_ids": [],
                "move_ids": [],
                "move_line_ids": [],
                "inv_ids": [],
                "inv_line_ids": [],
                "payment_ids": [],
                "payment_move_ids": [],
                "payment_move_line_ids": [],
                "partial_reconcile_ids": [],
                "st_line_ids": [],
                "statement_ids": [],
            }

        po_tuple = tuple(po_ids)

        # 1. Purchase Order Lines
        cr.execute("SELECT id FROM purchase_order_line WHERE order_id IN %s;", [po_tuple])
        pol_ids = [r[0] for r in cr.fetchall()]
        pol_tuple = tuple(pol_ids) if pol_ids else (0,)

        # 2. Incoming Pickings / Receipts
        picking_ids = []
        cr.execute("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'stock_picking' AND column_name = 'purchase_id';
        """)
        has_purchase_id = bool(cr.fetchone())

        if has_purchase_id:
            cr.execute("SELECT id FROM stock_picking WHERE purchase_id IN %s;", [po_tuple])
            for r in cr.fetchall():
                if r[0] not in picking_ids:
                    picking_ids.append(r[0])

        # Also find via stock_move linked to purchase_line_id
        if pol_ids:
            cr.execute("""
                SELECT DISTINCT picking_id FROM stock_move 
                WHERE purchase_line_id IN %s AND picking_id IS NOT NULL;
            """, [pol_tuple])
            for r in cr.fetchall():
                if r[0] not in picking_ids:
                    picking_ids.append(r[0])

        picking_tuple = tuple(picking_ids) if picking_ids else (0,)

        # 3. Stock Moves
        cr.execute("""
            SELECT id FROM stock_move 
            WHERE (picking_id IN %s) OR (purchase_line_id IN %s);
        """, [picking_tuple, pol_tuple])
        move_ids = [r[0] for r in cr.fetchall()]
        move_tuple = tuple(move_ids) if move_ids else (0,)

        # 4. Stock Move Lines
        cr.execute("""
            SELECT id FROM stock_move_line 
            WHERE (picking_id IN %s) OR (move_id IN %s);
        """, [picking_tuple, move_tuple])
        move_line_ids = [r[0] for r in cr.fetchall()]

        # 5. Vendor Bill Lines
        inv_line_ids = []
        cr.execute("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'account_move_line' AND column_name = 'purchase_line_id';
        """)
        if cr.fetchone() and pol_ids:
            cr.execute("SELECT id FROM account_move_line WHERE purchase_line_id IN %s;", [pol_tuple])
            inv_line_ids = [r[0] for r in cr.fetchall()]

        # 6. Vendor Bills / Account Moves
        inv_ids = []
        if inv_line_ids:
            cr.execute("SELECT DISTINCT move_id FROM account_move_line WHERE id IN %s;", [tuple(inv_line_ids)])
            inv_ids = [r[0] for r in cr.fetchall()]

        # Fallback: Bills with invoice_origin matching PO names
        cr.execute("SELECT name FROM purchase_order WHERE id IN %s;", [po_tuple])
        po_names = tuple(r[0] for r in cr.fetchall() if r[0])
        if po_names:
            cr.execute("SELECT id FROM account_move WHERE invoice_origin IN %s;", [po_names])
            for r in cr.fetchall():
                if r[0] not in inv_ids:
                    inv_ids.append(r[0])

            # Reference / Payment Reference search
            inv_t = tuple(inv_ids) if inv_ids else (0,)
            cr.execute("""
                SELECT id FROM account_move 
                WHERE (ref IN %s OR payment_reference IN %s) AND id NOT IN %s;
            """, [po_names, po_names, inv_t])
            for r in cr.fetchall():
                if r[0] not in inv_ids:
                    inv_ids.append(r[0])

        # Include reversals / credit notes linked to these bills
        if inv_ids:
            cr.execute("SELECT id FROM account_move WHERE reversed_entry_id IN %s;", [tuple(inv_ids)])
            for r in cr.fetchall():
                if r[0] not in inv_ids:
                    inv_ids.append(r[0])

            cr.execute("""
                SELECT reversed_entry_id FROM account_move 
                WHERE id IN %s AND reversed_entry_id IS NOT NULL;
            """, [tuple(inv_ids)])
            for r in cr.fetchall():
                if r[0] not in inv_ids:
                    inv_ids.append(r[0])

            # Capture all lines for these vendor bills
            cr.execute("SELECT id FROM account_move_line WHERE move_id IN %s;", [tuple(inv_ids)])
            inv_line_ids = [r[0] for r in cr.fetchall()]

        # 7. Payments, Payment Moves, Lines, and Reconciliations
        partial_reconcile_ids = []
        payment_ids = []
        payment_move_ids = []
        payment_move_line_ids = []

        if inv_ids:
            inv_tuple = tuple(inv_ids)
            cr.execute("SELECT id FROM account_move_line WHERE move_id IN %s;", [inv_tuple])
            all_inv_aml_ids = [r[0] for r in cr.fetchall()]

            if all_inv_aml_ids:
                aml_tuple = tuple(all_inv_aml_ids)
                cr.execute("""
                    SELECT id, debit_move_id, credit_move_id 
                    FROM account_partial_reconcile 
                    WHERE debit_move_id IN %s OR credit_move_id IN %s;
                """, [aml_tuple, aml_tuple])
                reconcile_rows = cr.fetchall()
                partial_reconcile_ids = [r[0] for r in reconcile_rows]

                # Identify counterpart lines
                counterpart_aml_ids = set()
                all_inv_aml_set = set(all_inv_aml_ids)
                for r in reconcile_rows:
                    deb_id, cred_id = r[1], r[2]
                    if deb_id not in all_inv_aml_set:
                        counterpart_aml_ids.add(deb_id)
                    if cred_id not in all_inv_aml_set:
                        counterpart_aml_ids.add(cred_id)

                if counterpart_aml_ids:
                    cp_tuple = tuple(counterpart_aml_ids)
                    cr.execute("SELECT DISTINCT move_id FROM account_move_line WHERE id IN %s;", [cp_tuple])
                    payment_move_ids = [r[0] for r in cr.fetchall() if r[0] not in inv_ids]

            # Check relation table account_move__account_payment
            cr.execute("""
                SELECT 1 FROM information_schema.tables WHERE table_name = 'account_move__account_payment';
            """)
            if cr.fetchone():
                cr.execute("SELECT DISTINCT payment_id FROM account_move__account_payment WHERE invoice_id IN %s;", [inv_tuple])
                for r in cr.fetchall():
                    if r[0] and r[0] not in payment_ids:
                        payment_ids.append(r[0])

            # Check origin_payment_id on bills or payment moves
            cr.execute("""
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'account_move' AND column_name = 'origin_payment_id';
            """)
            if cr.fetchone():
                all_moves_to_check = tuple(inv_ids + payment_move_ids)
                cr.execute("SELECT DISTINCT origin_payment_id FROM account_move WHERE id IN %s AND origin_payment_id IS NOT NULL;", [all_moves_to_check])
                for r in cr.fetchall():
                    if r[0] and r[0] not in payment_ids:
                        payment_ids.append(r[0])

            # Find payments from payment_moves via account_payment.move_id
            if payment_move_ids:
                cr.execute("SELECT id FROM account_payment WHERE move_id IN %s;", [tuple(payment_move_ids)])
                for r in cr.fetchall():
                    if r[0] and r[0] not in payment_ids:
                        payment_ids.append(r[0])

            if payment_ids:
                cr.execute("SELECT DISTINCT move_id FROM account_payment WHERE id IN %s AND move_id IS NOT NULL;", [tuple(payment_ids)])
                for r in cr.fetchall():
                    if r[0] and r[0] not in payment_move_ids and r[0] not in inv_ids:
                        payment_move_ids.append(r[0])

            if payment_move_ids:
                cr.execute("SELECT id FROM account_move_line WHERE move_id IN %s;", [tuple(payment_move_ids)])
                payment_move_line_ids = [r[0] for r in cr.fetchall()]

        # 8. Bank Statement Lines & Bank Statements
        st_line_ids = []
        statement_ids = []
        all_moves_for_bs = tuple(set(inv_ids + payment_move_ids)) if (inv_ids or payment_move_ids) else ()
        if all_moves_for_bs:
            cr.execute("""
                SELECT DISTINCT statement_line_id FROM account_move 
                WHERE id IN %s AND statement_line_id IS NOT NULL;
            """, [all_moves_for_bs])
            for r in cr.fetchall():
                if r[0] and r[0] not in st_line_ids:
                    st_line_ids.append(r[0])

            cr.execute("""
                SELECT 1 FROM information_schema.tables WHERE table_name = 'account_bank_statement_line';
            """)
            if cr.fetchone():
                cr.execute("""
                    SELECT id FROM account_bank_statement_line WHERE move_id IN %s;
                """, [all_moves_for_bs])
                for r in cr.fetchall():
                    if r[0] not in st_line_ids:
                        st_line_ids.append(r[0])

            if st_line_ids:
                cr.execute("""
                    SELECT DISTINCT statement_id FROM account_bank_statement_line 
                    WHERE id IN %s AND statement_id IS NOT NULL;
                """, [tuple(st_line_ids)])
                statement_ids = [r[0] for r in cr.fetchall() if r[0]]

        # Guarantee every ID actually exists in the database table
        if inv_ids:
            cr.execute("SELECT id FROM account_move WHERE id IN %s;", [tuple(inv_ids)])
            inv_ids = [r[0] for r in cr.fetchall()]
        if payment_move_ids:
            cr.execute("SELECT id FROM account_move WHERE id IN %s;", [tuple(payment_move_ids)])
            payment_move_ids = [r[0] for r in cr.fetchall()]
        if payment_ids:
            cr.execute("SELECT id FROM account_payment WHERE id IN %s;", [tuple(payment_ids)])
            payment_ids = [r[0] for r in cr.fetchall()]
        if st_line_ids:
            cr.execute("SELECT id FROM account_bank_statement_line WHERE id IN %s;", [tuple(st_line_ids)])
            st_line_ids = [r[0] for r in cr.fetchall()]
        if statement_ids:
            cr.execute("SELECT id FROM account_bank_statement WHERE id IN %s;", [tuple(statement_ids)])
            statement_ids = [r[0] for r in cr.fetchall()]

        return {
            "po_ids": po_ids,
            "pol_ids": pol_ids,
            "picking_ids": picking_ids,
            "move_ids": move_ids,
            "move_line_ids": move_line_ids,
            "inv_ids": inv_ids,
            "inv_line_ids": inv_line_ids,
            "payment_ids": payment_ids,
            "payment_move_ids": payment_move_ids,
            "payment_move_line_ids": payment_move_line_ids,
            "partial_reconcile_ids": partial_reconcile_ids,
            "st_line_ids": st_line_ids,
            "statement_ids": statement_ids,
        }

    def _get_target_journal_mapping(self, move_ids, dest_company_id):
        """Map each move_id to an equivalent journal_id in dest_company_id."""
        if not move_ids:
            return {}
        moves = self.env["account.move"].sudo().browse(move_ids).exists()
        AccountJournal = self.env["account.journal"].sudo()

        dest_journals = AccountJournal.search([("company_id", "=", dest_company_id)])
        dest_by_type = {}
        dest_by_code = {}
        dest_by_name = {}
        for j in dest_journals:
            dest_by_type.setdefault(j.type, []).append(j)
            if j.code:
                dest_by_code[j.code.strip().upper()] = j
            if j.name:
                dest_by_name[j.name.strip().upper()] = j

        mapping = {}
        for move in moves:
            orig_j = move.journal_id
            target_j = False

            # 1. Match by code or name
            if orig_j and orig_j.code and orig_j.code.strip().upper() in dest_by_code:
                target_j = dest_by_code[orig_j.code.strip().upper()]
            elif orig_j and orig_j.name and orig_j.name.strip().upper() in dest_by_name:
                target_j = dest_by_name[orig_j.name.strip().upper()]

            # 2. Match by type
            if not target_j:
                j_type = orig_j.type if orig_j else False
                if not j_type:
                    if move.move_type in ("in_invoice", "in_refund", "in_receipt"):
                        j_type = "purchase"
                    elif move.move_type in ("out_invoice", "out_refund", "out_receipt"):
                        j_type = "sale"
                    elif move.is_purchase_document():
                        j_type = "purchase"
                    elif move.is_sale_document():
                        j_type = "sale"
                    else:
                        j_type = "general"

                type_journals = dest_by_type.get(j_type) or []
                if type_journals:
                    target_j = type_journals[0]

            if target_j:
                mapping[move.id] = target_j.id
        return mapping

    def action_fetch_records_count(self):
        """Fetch and count matching records across all models, displaying a toast notification."""
        self.ensure_one()
        po_ids = self._get_matching_po_ids()
        records = self._get_related_record_ids(po_ids)

        c_po = len(records["po_ids"])
        c_pol = len(records["pol_ids"])
        c_pick = len(records["picking_ids"])
        c_move = len(records["move_ids"])
        c_mline = len(records["move_line_ids"])
        c_inv = len(records["inv_ids"])
        c_iline = len(records["inv_line_ids"])
        c_pay = len(records["payment_ids"])
        c_pmove = len(records["payment_move_ids"])
        c_pline = len(records["payment_move_line_ids"])
        c_rec = len(records["partial_reconcile_ids"])
        c_stline = len(records["st_line_ids"])
        c_stat = len(records["statement_ids"])

        self.write({
            "count_purchase_orders": c_po,
            "count_purchase_order_lines": c_pol,
            "count_pickings": c_pick,
            "count_stock_moves": c_move,
            "count_stock_move_lines": c_mline,
            "count_invoices": c_inv,
            "count_invoice_lines": c_iline,
            "count_payments": c_pay,
            "count_payment_moves": c_pmove,
            "count_payment_lines": c_pline,
            "count_partial_reconciles": c_rec,
            "count_bank_statement_lines": c_stline,
            "count_bank_statements": c_stat,
            "last_fetch_date": fields.Datetime.now(),
        })

        msg = _(
            "Found: %(po)s POs, %(pol)s Lines, %(pick)s Receipts, %(move)s Moves, "
            "%(inv)s Bills, %(iline)s Bill Lines, %(pay)s Payments, %(pmove)s Payment Moves, %(pline)s Payment Lines, "
            "%(rec)s Reconciles, %(stline)s Bank Transactions, and %(stat)s Statements.",
            po=c_po,
            pol=c_pol,
            pick=c_pick,
            move=c_move + c_mline,
            inv=c_inv,
            iline=c_iline,
            pay=c_pay,
            pmove=c_pmove,
            pline=c_pline,
            rec=c_rec,
            stline=c_stline,
            stat=c_stat,
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Record Counts Fetched"),
                "message": msg,
                "type": "info",
                "sticky": False,
            },
        }

    def _create_log_entry(self, action_type, count, summary, status="success"):
        """Create and associate an audit execution log."""
        log = self.env["purchase.company.reassignment.log"].sudo().create({
            "tool_id": self.id,
            "source_company_id": self.source_company_id.id,
            "target_company_id": self.target_company_id.id,
            "gstin_id": self.gstin_id.id if self.gstin_id else False,
            "gst_code": self.gst_code,
            "action_type": action_type,
            "records_updated": count,
            "status": status,
            "summary": summary,
        })
        return log

    def action_update_all(self):
        """Update entire purchase pipeline atomically in one transaction."""
        self.ensure_one()
        if not self.target_company_id:
            raise UserError(_("Please configure or select a Target Company."))

        self._ensure_transferred_columns_exist()
        po_ids = self._get_matching_po_ids()
        records = self._get_related_record_ids(po_ids)

        if not records["po_ids"]:
            summary = _("No matching Purchase Orders found to update.")
            self._create_log_entry("all", 0, summary, "nothing_to_update")
            raise UserError(summary)

        cr = self.env.cr
        dest_id = self.target_company_id.id

        with cr.savepoint():
            # 1. Purchase Orders
            if records["po_ids"]:
                cr.execute("""
                    UPDATE purchase_order 
                    SET company_id = %s, is_company_transferred = TRUE 
                    WHERE id IN %s;
                """, [dest_id, tuple(records["po_ids"])])

            # 2. Purchase Order Lines
            if records["pol_ids"]:
                cr.execute("""
                    UPDATE purchase_order_line 
                    SET company_id = %s, is_company_transferred = TRUE 
                    WHERE id IN %s;
                """, [dest_id, tuple(records["pol_ids"])])

            # 3. Incoming Receipts / Pickings
            if records["picking_ids"]:
                cr.execute("""
                    UPDATE stock_picking 
                    SET company_id = %s, is_company_transferred = TRUE 
                    WHERE id IN %s;
                """, [dest_id, tuple(records["picking_ids"])])

            # 4. Stock Moves
            if records["move_ids"]:
                cr.execute("""
                    UPDATE stock_move 
                    SET company_id = %s, is_company_transferred = TRUE 
                    WHERE id IN %s;
                """, [dest_id, tuple(records["move_ids"])])

            # 5. Stock Move Lines
            if records["move_line_ids"]:
                cr.execute("""
                    UPDATE stock_move_line 
                    SET company_id = %s, is_company_transferred = TRUE 
                    WHERE id IN %s;
                """, [dest_id, tuple(records["move_line_ids"])])

            # 6. Vendor Bills & Lines
            if records["inv_ids"]:
                inv_map = self._get_target_journal_mapping(records["inv_ids"], dest_id)
                for mid in records["inv_ids"]:
                    jid = inv_map.get(mid)
                    if jid:
                        cr.execute("""
                            UPDATE account_move 
                            SET company_id = %s, journal_id = %s, is_company_transferred = TRUE 
                            WHERE id = %s;
                        """, [dest_id, jid, mid])
                        cr.execute("""
                            UPDATE account_move_line 
                            SET company_id = %s, journal_id = %s, is_company_transferred = TRUE 
                            WHERE move_id = %s;
                        """, [dest_id, jid, mid])
                    else:
                        cr.execute("""
                            UPDATE account_move 
                            SET company_id = %s, is_company_transferred = TRUE 
                            WHERE id = %s;
                        """, [dest_id, mid])
                        cr.execute("""
                            UPDATE account_move_line 
                            SET company_id = %s, is_company_transferred = TRUE 
                            WHERE move_id = %s;
                        """, [dest_id, mid])

            # 7. Additional bill lines if any
            if records["inv_line_ids"]:
                cr.execute("""
                    UPDATE account_move_line 
                    SET company_id = %s, is_company_transferred = TRUE 
                    WHERE id IN %s;
                """, [dest_id, tuple(records["inv_line_ids"])])

            # 8. Payment Moves & Lines
            if records["payment_move_ids"]:
                pmove_map = self._get_target_journal_mapping(records["payment_move_ids"], dest_id)
                for mid in records["payment_move_ids"]:
                    jid = pmove_map.get(mid)
                    if jid:
                        cr.execute("""
                            UPDATE account_move 
                            SET company_id = %s, journal_id = %s, is_company_transferred = TRUE 
                            WHERE id = %s;
                        """, [dest_id, jid, mid])
                        cr.execute("""
                            UPDATE account_move_line 
                            SET company_id = %s, journal_id = %s, is_company_transferred = TRUE 
                            WHERE move_id = %s;
                        """, [dest_id, jid, mid])
                    else:
                        cr.execute("""
                            UPDATE account_move 
                            SET company_id = %s, is_company_transferred = TRUE 
                            WHERE id = %s;
                        """, [dest_id, mid])
                        cr.execute("""
                            UPDATE account_move_line 
                            SET company_id = %s, is_company_transferred = TRUE 
                            WHERE move_id = %s;
                        """, [dest_id, mid])

            # 9. Additional payment move lines if any
            if records["payment_move_line_ids"]:
                cr.execute("""
                    UPDATE account_move_line 
                    SET company_id = %s, is_company_transferred = TRUE 
                    WHERE id IN %s;
                """, [dest_id, tuple(records["payment_move_line_ids"])])

            # 10. Payments
            if records["payment_ids"]:
                payments = self.env["account.payment"].sudo().browse(records["payment_ids"]).exists()
                bank_j = self.env["account.journal"].sudo().search([
                    ("company_id", "=", dest_id),
                    ("type", "in", ("bank", "cash", "general")),
                ], limit=1)
                fallback_jid = bank_j.id if bank_j else False

                for pay in payments:
                    target_jid = False
                    if pay.move_id and pay.move_id.id in records["payment_move_ids"]:
                        target_jid = pmove_map.get(pay.move_id.id)
                    if not target_jid:
                        target_jid = fallback_jid

                    if target_jid:
                        cr.execute("""
                            UPDATE account_payment 
                            SET company_id = %s, journal_id = %s, is_company_transferred = TRUE 
                            WHERE id = %s;
                        """, [dest_id, target_jid, pay.id])
                    else:
                        cr.execute("""
                            UPDATE account_payment 
                            SET company_id = %s, is_company_transferred = TRUE 
                            WHERE id = %s;
                        """, [dest_id, pay.id])

            # 11. Partial Reconciles
            if records["partial_reconcile_ids"]:
                cr.execute("""
                    UPDATE account_partial_reconcile 
                    SET company_id = %s, is_company_transferred = TRUE 
                    WHERE id IN %s;
                """, [dest_id, tuple(records["partial_reconcile_ids"])])

            # 12. Bank Statement Lines
            if records["st_line_ids"]:
                bank_j = self.env["account.journal"].sudo().search([
                    ("company_id", "=", dest_id),
                    ("type", "in", ("bank", "cash")),
                ], limit=1)
                target_bank_jid = bank_j.id if bank_j else False

                for stl_id in records["st_line_ids"]:
                    if target_bank_jid:
                        cr.execute("""
                            UPDATE account_bank_statement_line 
                            SET company_id = %s, journal_id = %s, is_company_transferred = TRUE 
                            WHERE id = %s;
                        """, [dest_id, target_bank_jid, stl_id])
                    else:
                        cr.execute("""
                            UPDATE account_bank_statement_line 
                            SET company_id = %s, is_company_transferred = TRUE 
                            WHERE id = %s;
                        """, [dest_id, stl_id])

            # 13. Bank Statements
            if records["statement_ids"]:
                bank_j = self.env["account.journal"].sudo().search([
                    ("company_id", "=", dest_id),
                    ("type", "in", ("bank", "cash")),
                ], limit=1)
                target_bank_jid = bank_j.id if bank_j else False

                for st_id in records["statement_ids"]:
                    if target_bank_jid:
                        cr.execute("""
                            UPDATE account_bank_statement 
                            SET company_id = %s, journal_id = %s, is_company_transferred = TRUE 
                            WHERE id = %s;
                        """, [dest_id, target_bank_jid, st_id])
                    else:
                        cr.execute("""
                            UPDATE account_bank_statement 
                            SET company_id = %s, is_company_transferred = TRUE 
                            WHERE id = %s;
                        """, [dest_id, st_id])

        total_updated = (
            len(records["po_ids"])
            + len(records["pol_ids"])
            + len(records["picking_ids"])
            + len(records["move_ids"])
            + len(records["move_line_ids"])
            + len(records["inv_ids"])
            + len(records["inv_line_ids"])
            + len(records["payment_ids"])
            + len(records["payment_move_ids"])
            + len(records["payment_move_line_ids"])
            + len(records["partial_reconcile_ids"])
            + len(records["st_line_ids"])
            + len(records["statement_ids"])
        )

        self.env.invalidate_all()
        summary = _(
            "COMPLETED PURCHASE PIPELINE REASSIGNMENT to '%(com)s': %(po)s POs, %(pol)s Lines, "
            "%(pick)s Receipts, %(move)s Moves, %(inv)s Bills, %(iline)s Bill Lines, "
            "%(pay)s Payments, %(pmove)s Payment Moves, %(pline)s Payment Lines, "
            "%(stline)s Bank Transactions, %(stat)s Statements, %(rec)s Reconciliations.",
            com=self.target_company_id.display_name,
            po=len(records["po_ids"]),
            pol=len(records["pol_ids"]),
            pick=len(records["picking_ids"]),
            move=len(records["move_ids"]) + len(records["move_line_ids"]),
            inv=len(records["inv_ids"]),
            iline=len(records["inv_line_ids"]),
            pay=len(records["payment_ids"]),
            pmove=len(records["payment_move_ids"]),
            pline=len(records["payment_move_line_ids"]),
            stline=len(records["st_line_ids"]),
            stat=len(records["statement_ids"]),
            rec=len(records["partial_reconcile_ids"]),
        )
        self._create_log_entry("all", total_updated, summary, "success")
        self.action_fetch_records_count()
        return self._notify_result(_("Purchase Pipeline Company Reassigned"), summary)

    def _notify_result(self, title, message):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": title,
                "message": message,
                "type": "success",
                "sticky": False,
            },
        }
