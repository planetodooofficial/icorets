# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleCompanyReassignmentTool(models.Model):
    _name = "sale.company.reassignment.tool"
    _description = "Sale Order Company Reassignment Control Tool"
    _order = "id desc"

    name = fields.Char(
        string="Operation Title",
        default="SO Company Reassignment Dashboard",
        required=True,
    )
    source_company_id = fields.Many2one(
        "res.company",
        string="Current / Source Company",
        required=True,
        default=lambda self: self.env.company,
        help="The company that currently owns the Sale Orders and related records.",
    )
    gstin_id = fields.Many2one(
        "res.partner",
        string="GSTIN Unit / Partner",
        domain="[('is_gstin', '=', True)]",
        required=True,
        help="Select the GSTIN partner. Its GST code will match the destination branch company.",
    )
    gst_code = fields.Char(
        string="GST Code",
        compute="_compute_gst_code",
        store=True,
        readonly=False,
        help="GST matching code of the selected partner (e.g. DL, HR, MH, TN).",
    )
    target_company_id = fields.Many2one(
        "res.company",
        string="Target / Destination Company",
        compute="_compute_target_company_id",
        store=True,
        readonly=False,
        required=True,
        help="The target branch company resolved from the GST matching code under the company hierarchy.",
    )
    model_target = fields.Selection(
        [
            ("all", "All Related Models (Complete Pipeline)"),
            ("sale_order", "1. Sale Orders (sale.order)"),
            ("sale_order_line", "2. Sale Order Lines (sale.order.line)"),
            ("stock_picking", "3. Delivery Orders (stock.picking)"),
            ("stock_move", "4. Stock Moves & Lines (stock.move, stock.move.line)"),
            ("account_move", "5. Invoices & Journal Entries (account.move & Related Classes)"),
            ("account_move_line", "6. Invoice Lines & Items (account.move.line)"),
            ("account_payment", "7. Payments & Reconciliations (account.payment, partial reconcile)"),
        ],
        string="Target Model for Update",
        default="all",
        required=True,
        help="Choose a specific model to update individually or select All to update the full pipeline.",
    )

    @api.onchange("model_target")
    def _onchange_model_target(self):
        for rec in self:
            if rec.model_target == "all":
                rec.count_selected_model = (
                    rec.count_sale_orders + rec.count_sale_order_lines + rec.count_pickings
                    + rec.count_stock_moves + rec.count_move_lines + rec.count_invoices
                    + rec.count_invoice_lines + rec.count_payments + rec.count_payment_moves
                    + rec.count_payment_lines + rec.count_partial_reconciles
                    + rec.count_bank_statement_lines + rec.count_bank_statements
                )
            elif rec.model_target == "sale_order":
                rec.count_selected_model = rec.count_sale_orders
            elif rec.model_target == "sale_order_line":
                rec.count_selected_model = rec.count_sale_order_lines
            elif rec.model_target == "stock_picking":
                rec.count_selected_model = rec.count_pickings
            elif rec.model_target == "stock_move":
                rec.count_selected_model = rec.count_stock_moves + rec.count_move_lines
            elif rec.model_target == "account_move":
                rec.count_selected_model = rec.count_invoices
            elif rec.model_target == "account_move_line":
                rec.count_selected_model = rec.count_invoice_lines
            elif rec.model_target == "account_payment":
                rec.count_selected_model = (
                    rec.count_payments + rec.count_payment_moves + rec.count_payment_lines
                    + rec.count_partial_reconciles + rec.count_bank_statement_lines
                    + rec.count_bank_statements
                )

    # Record counts
    count_sale_orders = fields.Integer(string="Sale Orders", readonly=True)
    count_sale_order_lines = fields.Integer(string="Sale Order Lines", readonly=True)
    count_pickings = fields.Integer(string="Pickings / Deliveries", readonly=True)
    count_stock_moves = fields.Integer(string="Stock Moves", readonly=True)
    count_move_lines = fields.Integer(string="Stock Move Lines", readonly=True)
    count_invoices = fields.Integer(string="Invoices / Moves", readonly=True)
    count_invoice_lines = fields.Integer(string="Invoice Lines", readonly=True)
    count_payments = fields.Integer(string="Payments", readonly=True)
    count_payment_moves = fields.Integer(string="Payment Entries", readonly=True)
    count_payment_lines = fields.Integer(string="Payment Items", readonly=True)
    count_partial_reconciles = fields.Integer(string="Reconciliations", readonly=True)
    count_bank_statement_lines = fields.Integer(string="Bank Transactions", readonly=True)
    count_bank_statements = fields.Integer(string="Bank Statements", readonly=True)
    count_selected_model = fields.Integer(string="Count of Selected Model", readonly=True)

    last_fetch_date = fields.Datetime(string="Last Counted At", readonly=True)
    log_ids = fields.One2many(
        "sale.company.reassignment.log",
        "tool_id",
        string="Execution Logs",
        readonly=True,
    )

    @api.depends("gstin_id", "gstin_id.gst_code")
    def _compute_gst_code(self):
        for rec in self:
            if rec.gstin_id:
                code = getattr(rec.gstin_id, "gst_code", False) or ""
                rec.gst_code = code.strip().upper() if code else ""
            else:
                rec.gst_code = ""

    @api.depends("gst_code", "source_company_id")
    def _compute_target_company_id(self):
        for rec in self:
            if not rec.gst_code or not rec.source_company_id:
                rec.target_company_id = False
                continue
            code = rec.gst_code.strip().upper()
            root = rec.source_company_id.sudo().root_id or rec.source_company_id.sudo()
            while root.parent_id:
                root = root.parent_id.sudo()

            branches = self.env["res.company"].sudo().search([
                ("gst_code_matching_com", "=ilike", code),
                ("id", "child_of", root.id),
            ], limit=1)
            rec.target_company_id = branches.id if branches else False

    def _ensure_transferred_columns_exist(self):
        """Ensure is_company_transferred column exists on all relevant tables."""
        cr = self.env.cr
        tables = [
            "sale_order",
            "sale_order_line",
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
        for table in tables:
            try:
                cr.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS is_company_transferred BOOLEAN DEFAULT FALSE")
            except Exception:
                pass

    def _get_matching_so_ids(self):
        """Fetch sale.order IDs that match source_company_id and gstin_id / gst_code."""
        self.ensure_one()
        if not self.source_company_id:
            raise UserError(_("Please select a Source Company."))

        cr = self.env.cr
        src_id = self.source_company_id.id
        gstin_id = self.gstin_id.id if self.gstin_id else False
        code = (self.gst_code or "").strip().upper()

        # Check if gstin_id column exists on sale_order table
        cr.execute("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'sale_order' AND column_name = 'gstin_id';
        """)
        has_gstin_col = bool(cr.fetchone())

        if has_gstin_col and gstin_id:
            cr.execute("""
                SELECT id FROM sale_order 
                WHERE company_id = %s AND gstin_id = %s;
            """, [src_id, gstin_id])
            so_ids = [r[0] for r in cr.fetchall()]
        elif code:
            # Match by partner's gst_code
            cr.execute("""
                SELECT so.id FROM sale_order so
                JOIN res_partner rp ON so.partner_id = rp.id
                WHERE so.company_id = %s AND UPPER(TRIM(rp.gst_code)) = %s;
            """, [src_id, code])
            so_ids = [r[0] for r in cr.fetchall()]
        elif gstin_id:
            cr.execute("""
                SELECT id FROM sale_order 
                WHERE company_id = %s AND partner_id = %s;
            """, [src_id, gstin_id])
            so_ids = [r[0] for r in cr.fetchall()]
        else:
            so_ids = []

        return so_ids

    def _get_direct_matching_move_ids(self):
        """Query direct account.move IDs matching the source company and GSTIN condition."""
        self.ensure_one()
        if not self.source_company_id:
            return []

        cr = self.env.cr
        src_id = self.source_company_id.id
        gstin_id = self.gstin_id.id if self.gstin_id else False
        code = (self.gst_code or "").strip().upper()

        cr.execute("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'account_move' AND column_name = 'gstin_id';
        """)
        has_gstin_col = bool(cr.fetchone())

        cr.execute("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'res_partner' AND column_name = 'gst_code';
        """)
        has_partner_gst_code = bool(cr.fetchone())

        move_ids = []
        # 1. Direct match on account_move.gstin_id
        if has_gstin_col and gstin_id:
            cr.execute("""
                SELECT id FROM account_move 
                WHERE company_id = %s AND gstin_id = %s;
            """, [src_id, gstin_id])
            for r in cr.fetchall():
                if r[0] not in move_ids:
                    move_ids.append(r[0])

        # 2. Match by partner's gst_code or gstin partner's GST code
        if code:
            if has_gstin_col and has_partner_gst_code:
                cr.execute("""
                    SELECT am.id FROM account_move am
                    JOIN res_partner rp ON am.gstin_id = rp.id
                    WHERE am.company_id = %s AND UPPER(TRIM(rp.gst_code)) = %s;
                """, [src_id, code])
                for r in cr.fetchall():
                    if r[0] not in move_ids:
                        move_ids.append(r[0])

            if has_partner_gst_code:
                cr.execute("""
                    SELECT am.id FROM account_move am
                    JOIN res_partner rp ON am.partner_id = rp.id
                    WHERE am.company_id = %s AND UPPER(TRIM(rp.gst_code)) = %s;
                """, [src_id, code])
                for r in cr.fetchall():
                    if r[0] not in move_ids:
                        move_ids.append(r[0])
            else:
                cr.execute("""
                    SELECT am.id FROM account_move am
                    JOIN res_partner rp ON am.partner_id = rp.id
                    WHERE am.company_id = %s AND rp.vat LIKE %s;
                """, [src_id, f"{code}%"])
                for r in cr.fetchall():
                    if r[0] not in move_ids:
                        move_ids.append(r[0])
        elif gstin_id:
            cr.execute("""
                SELECT id FROM account_move 
                WHERE company_id = %s AND partner_id = %s;
            """, [src_id, gstin_id])
            for r in cr.fetchall():
                if r[0] not in move_ids:
                    move_ids.append(r[0])

        return move_ids

    def _get_related_record_ids(self, so_ids):
        """Query IDs of all records linked to given sale orders and direct matching account moves using fast SQL."""
        cr = self.env.cr

        so_ids = list(so_ids or [])
        so_tuple = tuple(so_ids) if so_ids else (0,)

        # 1. Sale Order Lines
        sol_ids = []
        if so_ids:
            cr.execute("SELECT id FROM sale_order_line WHERE order_id IN %s;", [so_tuple])
            sol_ids = [r[0] for r in cr.fetchall()]
        sol_tuple = tuple(sol_ids) if sol_ids else (0,)

        # 2. Stock Pickings (via sale_id or proc group)
        picking_ids = []
        if so_ids:
            cr.execute("""
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'stock_picking' AND column_name = 'sale_id';
            """)
            has_sale_id = bool(cr.fetchone())

            if has_sale_id:
                cr.execute("SELECT id FROM stock_picking WHERE sale_id IN %s;", [so_tuple])
                picking_ids = [r[0] for r in cr.fetchall()]
            else:
                cr.execute("SELECT DISTINCT picking_id FROM stock_move WHERE sale_line_id IN %s AND picking_id IS NOT NULL;", [sol_tuple])
                picking_ids = [r[0] for r in cr.fetchall()]
        picking_tuple = tuple(picking_ids) if picking_ids else (0,)

        # 3. Stock Moves
        move_ids = []
        if picking_ids or sol_ids:
            cr.execute("""
                SELECT id FROM stock_move 
                WHERE (picking_id IN %s) OR (sale_line_id IN %s);
            """, [picking_tuple, sol_tuple])
            move_ids = [r[0] for r in cr.fetchall()]
        move_tuple = tuple(move_ids) if move_ids else (0,)

        # 4. Stock Move Lines
        move_line_ids = []
        if picking_ids or move_ids:
            cr.execute("""
                SELECT id FROM stock_move_line 
                WHERE (picking_id IN %s) OR (move_id IN %s);
            """, [picking_tuple, move_tuple])
            move_line_ids = [r[0] for r in cr.fetchall()]

        # 5. Invoice Lines from SO Lines (via sale_order_line_invoice_rel)
        inv_ids = []
        inv_line_ids = []
        cr.execute("""
            SELECT 1 FROM information_schema.tables WHERE table_name = 'sale_order_line_invoice_rel';
        """)
        if cr.fetchone() and sol_ids:
            cr.execute("SELECT invoice_line_id FROM sale_order_line_invoice_rel WHERE order_line_id IN %s;", [sol_tuple])
            inv_line_rel_ids = [r[0] for r in cr.fetchall()]
            if inv_line_rel_ids:
                cr.execute("SELECT DISTINCT move_id FROM account_move_line WHERE id IN %s;", [tuple(inv_line_rel_ids)])
                inv_ids.extend([r[0] for r in cr.fetchall()])

        # Fallback: Invoices with invoice_origin in SO names
        if so_ids:
            cr.execute("SELECT name FROM sale_order WHERE id IN %s;", [so_tuple])
            so_names = tuple(r[0] for r in cr.fetchall() if r[0])
            if so_names:
                cr.execute("SELECT id FROM account_move WHERE invoice_origin IN %s;", [so_names])
                for r in cr.fetchall():
                    if r[0] not in inv_ids:
                        inv_ids.append(r[0])

                inv_t = tuple(inv_ids) if inv_ids else (0,)
                cr.execute("""
                    SELECT id FROM account_move 
                    WHERE (ref IN %s OR payment_reference IN %s) AND id NOT IN %s;
                """, [so_names, so_names, inv_t])
                for r in cr.fetchall():
                    if r[0] not in inv_ids:
                        inv_ids.append(r[0])

        # 6. DIRECT MATCHING ACCOUNT MOVES (Matching GSTIN / GST code in source company)
        direct_inv_ids = self._get_direct_matching_move_ids()
        for did in direct_inv_ids:
            if did not in inv_ids:
                inv_ids.append(did)

        # Include all reversals / credit notes linked to these invoices (reversed_entry_id)
        if inv_ids:
            cr.execute("""
                SELECT id FROM account_move WHERE reversed_entry_id IN %s;
            """, [tuple(inv_ids)])
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

        if inv_ids:
            cr.execute("SELECT id FROM account_move_line WHERE move_id IN %s;", [tuple(inv_ids)])
            inv_line_ids = [r[0] for r in cr.fetchall()]

        # 7. Payments, Payment Journal Entries, Payment Items, and Partial Reconciliations
        partial_reconcile_ids = []
        payment_ids = []
        payment_move_ids = []
        payment_move_line_ids = []

        if inv_ids:
            inv_tuple = tuple(inv_ids)
            # Find all journal lines for these invoices
            cr.execute("SELECT id FROM account_move_line WHERE move_id IN %s;", [inv_tuple])
            all_inv_aml_ids = [r[0] for r in cr.fetchall()]

            if all_inv_aml_ids:
                aml_tuple = tuple(all_inv_aml_ids)
                # Query account_partial_reconcile linked to any invoice lines
                cr.execute("""
                    SELECT id, debit_move_id, credit_move_id 
                    FROM account_partial_reconcile 
                    WHERE debit_move_id IN %s OR credit_move_id IN %s;
                """, [aml_tuple, aml_tuple])
                reconcile_rows = cr.fetchall()
                partial_reconcile_ids = [r[0] for r in reconcile_rows]

                # Identify counterpart lines (payment/counterpart journal items)
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

            # Also check matched_payment_ids relation table if present
            cr.execute("""
                SELECT 1 FROM information_schema.tables WHERE table_name = 'account_move__account_payment';
            """)
            if cr.fetchone():
                cr.execute("SELECT DISTINCT payment_id FROM account_move__account_payment WHERE invoice_id IN %s;", [inv_tuple])
                for r in cr.fetchall():
                    if r[0] and r[0] not in payment_ids:
                        payment_ids.append(r[0])

            # Also check origin_payment_id on invoices or payment moves
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

            # And if we found payment_ids, ensure their move_ids are captured
            if payment_ids:
                cr.execute("SELECT DISTINCT move_id FROM account_payment WHERE id IN %s AND move_id IS NOT NULL;", [tuple(payment_ids)])
                for r in cr.fetchall():
                    if r[0] and r[0] not in payment_move_ids and r[0] not in inv_ids:
                        payment_move_ids.append(r[0])

            # Fetch all move lines for payment moves
            if payment_move_ids:
                cr.execute("SELECT id FROM account_move_line WHERE move_id IN %s;", [tuple(payment_move_ids)])
                payment_move_line_ids = [r[0] for r in cr.fetchall()]

        # 8. Bank Statement Lines & Bank Statements
        st_line_ids = []
        statement_ids = []
        all_moves_for_bs = tuple(set(inv_ids + payment_move_ids)) if (inv_ids or payment_move_ids) else ()
        if all_moves_for_bs:
            # A. Check statement_line_id on moves
            cr.execute("""
                SELECT DISTINCT statement_line_id FROM account_move 
                WHERE id IN %s AND statement_line_id IS NOT NULL;
            """, [all_moves_for_bs])
            for r in cr.fetchall():
                if r[0] and r[0] not in st_line_ids:
                    st_line_ids.append(r[0])

            # B. Check account_bank_statement_line by move_id
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

            # C. Check statements linked to statement lines
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
            "so_ids": so_ids,
            "sol_ids": sol_ids,
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

    def action_fetch_records_count(self):
        """Fetch and populate record counts across all models based on current selections."""
        self.ensure_one()
        so_ids = self._get_matching_so_ids()
        records = self._get_related_record_ids(so_ids)

        c_so = len(records["so_ids"])
        c_sol = len(records["sol_ids"])
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

        selected_count = 0
        if self.model_target == "all":
            selected_count = (
                c_so + c_sol + c_pick + c_move + c_mline + c_inv + c_iline
                + c_pay + c_pmove + c_pline + c_rec + c_stline + c_stat
            )
        elif self.model_target == "sale_order":
            selected_count = c_so
        elif self.model_target == "sale_order_line":
            selected_count = c_sol
        elif self.model_target == "stock_picking":
            selected_count = c_pick
        elif self.model_target == "stock_move":
            selected_count = c_move + c_mline
        elif self.model_target == "account_move":
            selected_count = c_inv
        elif self.model_target == "account_move_line":
            selected_count = c_iline
        elif self.model_target == "account_payment":
            selected_count = c_pay + c_pmove + c_pline + c_rec + c_stline + c_stat

        self.write({
            "count_sale_orders": c_so,
            "count_sale_order_lines": c_sol,
            "count_pickings": c_pick,
            "count_stock_moves": c_move,
            "count_move_lines": c_mline,
            "count_invoices": c_inv,
            "count_invoice_lines": c_iline,
            "count_payments": c_pay,
            "count_payment_moves": c_pmove,
            "count_payment_lines": c_pline,
            "count_partial_reconciles": c_rec,
            "count_bank_statement_lines": c_stline,
            "count_bank_statements": c_stat,
            "count_selected_model": selected_count,
            "last_fetch_date": fields.Datetime.now(),
        })

        msg = _(
            "Found %(so)s SOs, %(sol)s Lines, %(pick)s Pickings, %(move)s Moves, "
            "%(inv)s Invoices, %(iline)s Invoice Lines, %(pay)s Payments, %(pmove)s Payment Moves, "
            "%(pline)s Payment Lines, %(rec)s Reconciliations, %(stline)s Bank Transactions, %(stat)s Statements.",
            so=c_so,
            sol=c_sol,
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
        """Create and associate a persistent execution log."""
        log = self.env["sale.company.reassignment.log"].sudo().create({
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

    # Individual Execution Buttons
    def action_update_sale_orders(self):
        """Update company_id on sale.order records."""
        self.ensure_one()
        if not self.target_company_id:
            raise UserError(_("Please configure or select a Target Company."))

        self._ensure_transferred_columns_exist()
        so_ids = self._get_matching_so_ids()
        if not so_ids:
            summary = _("No matching Sale Orders found to update.")
            self._create_log_entry("sale_order", 0, summary, "nothing_to_update")
            raise UserError(summary)

        cr = self.env.cr
        dest_id = self.target_company_id.id
        cr.execute("""
            UPDATE sale_order 
            SET company_id = %s, is_company_transferred = TRUE 
            WHERE id IN %s;
        """, [dest_id, tuple(so_ids)])
        count = len(so_ids)

        self.env.invalidate_all()
        summary = _("Updated %(count)s Sale Orders to company '%(com)s'.", count=count, com=self.target_company_id.display_name)
        self._create_log_entry("sale_order", count, summary, "success")
        self.action_fetch_records_count()
        return self._notify_result(_("Sale Orders Updated"), summary)

    def action_update_sale_order_lines(self):
        """Update company_id on sale.order.line records."""
        self.ensure_one()
        if not self.target_company_id:
            raise UserError(_("Please configure or select a Target Company."))

        self._ensure_transferred_columns_exist()
        so_ids = self._get_matching_so_ids()
        records = self._get_related_record_ids(so_ids)
        sol_ids = records["sol_ids"]
        if not sol_ids:
            summary = _("No matching Sale Order Lines found to update.")
            self._create_log_entry("sale_order_line", 0, summary, "nothing_to_update")
            raise UserError(summary)

        cr = self.env.cr
        dest_id = self.target_company_id.id
        cr.execute("""
            UPDATE sale_order_line 
            SET company_id = %s, is_company_transferred = TRUE 
            WHERE id IN %s;
        """, [dest_id, tuple(sol_ids)])
        count = len(sol_ids)

        self.env.invalidate_all()
        summary = _("Updated %(count)s Sale Order Lines to company '%(com)s'.", count=count, com=self.target_company_id.display_name)
        self._create_log_entry("sale_order_line", count, summary, "success")
        self.action_fetch_records_count()
        return self._notify_result(_("Sale Order Lines Updated"), summary)

    def action_update_pickings(self):
        """Update company_id on stock.picking records."""
        self.ensure_one()
        if not self.target_company_id:
            raise UserError(_("Please configure or select a Target Company."))

        self._ensure_transferred_columns_exist()
        so_ids = self._get_matching_so_ids()
        records = self._get_related_record_ids(so_ids)
        picking_ids = records["picking_ids"]
        if not picking_ids:
            summary = _("No matching Delivery Pickings found to update.")
            self._create_log_entry("stock_picking", 0, summary, "nothing_to_update")
            raise UserError(summary)

        cr = self.env.cr
        dest_id = self.target_company_id.id
        cr.execute("""
            UPDATE stock_picking 
            SET company_id = %s, is_company_transferred = TRUE 
            WHERE id IN %s;
        """, [dest_id, tuple(picking_ids)])
        count = len(picking_ids)

        self.env.invalidate_all()
        summary = _("Updated %(count)s Delivery Pickings to company '%(com)s'.", count=count, com=self.target_company_id.display_name)
        self._create_log_entry("stock_picking", count, summary, "success")
        self.action_fetch_records_count()
        return self._notify_result(_("Pickings Updated"), summary)

    def action_update_stock_moves(self):
        """Update company_id on stock.move and stock.move.line records."""
        self.ensure_one()
        if not self.target_company_id:
            raise UserError(_("Please configure or select a Target Company."))

        self._ensure_transferred_columns_exist()
        so_ids = self._get_matching_so_ids()
        records = self._get_related_record_ids(so_ids)
        move_ids = records["move_ids"]
        move_line_ids = records["move_line_ids"]
        if not move_ids and not move_line_ids:
            summary = _("No matching Stock Moves found to update.")
            self._create_log_entry("stock_move", 0, summary, "nothing_to_update")
            raise UserError(summary)

        cr = self.env.cr
        dest_id = self.target_company_id.id
        if move_ids:
            cr.execute("""
                UPDATE stock_move 
                SET company_id = %s, is_company_transferred = TRUE 
                WHERE id IN %s;
            """, [dest_id, tuple(move_ids)])
        if move_line_ids:
            cr.execute("""
                UPDATE stock_move_line 
                SET company_id = %s, is_company_transferred = TRUE 
                WHERE id IN %s;
            """, [dest_id, tuple(move_line_ids)])

        total_count = len(move_ids) + len(move_line_ids)
        self.env.invalidate_all()
        summary = _(
            "Updated %(m)s Stock Moves and %(ml)s Move Lines to company '%(com)s'.",
            m=len(move_ids),
            ml=len(move_line_ids),
            com=self.target_company_id.display_name,
        )
        self._create_log_entry("stock_move", total_count, summary, "success")
        self.action_fetch_records_count()
        return self._notify_result(_("Stock Moves Updated"), summary)

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

            # 1. Match by exact code or name in destination company
            if orig_j and orig_j.code and orig_j.code.strip().upper() in dest_by_code:
                target_j = dest_by_code[orig_j.code.strip().upper()]
            elif orig_j and orig_j.name and orig_j.name.strip().upper() in dest_by_name:
                target_j = dest_by_name[orig_j.name.strip().upper()]

            # 2. Match by journal type in destination company
            if not target_j:
                j_type = orig_j.type if orig_j else False
                if not j_type:
                    if move.move_type in ("out_invoice", "out_refund", "out_receipt"):
                        j_type = "sale"
                    elif move.move_type in ("in_invoice", "in_refund", "in_receipt"):
                        j_type = "purchase"
                    elif move.is_sale_document():
                        j_type = "sale"
                    elif move.is_purchase_document():
                        j_type = "purchase"
                    else:
                        j_type = "general"

                type_journals = dest_by_type.get(j_type) or []
                if type_journals:
                    target_j = type_journals[0]
                elif dest_journals:
                    target_j = dest_journals[0]

            mapping[move.id] = target_j.id if target_j else (orig_j.id if orig_j else False)

        return mapping

    def action_update_invoices(self):
        """Update company_id and journal_id on account.move records and all related classes (lines, reconciles, payments, statements)."""
        self.ensure_one()
        if not self.target_company_id:
            raise UserError(_("Please configure or select a Target Company."))

        self._ensure_transferred_columns_exist()
        so_ids = self._get_matching_so_ids()
        records = self._get_related_record_ids(so_ids)
        inv_ids = records["inv_ids"]
        if not inv_ids:
            summary = _("No matching Invoices / Account Moves found to update.")
            self._create_log_entry("account_move", 0, summary, "nothing_to_update")
            raise UserError(summary)

        cr = self.env.cr
        dest_id = self.target_company_id.id

        with cr.savepoint():
            # 1. Update Invoices & Lines
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

            # 2. Additional invoice lines if any
            if records["inv_line_ids"]:
                cr.execute("""
                    UPDATE account_move_line 
                    SET company_id = %s, is_company_transferred = TRUE 
                    WHERE id IN %s;
                """, [dest_id, tuple(records["inv_line_ids"])])

            # 3. Payment Moves & Lines
            pmove_map = {}
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

            # 4. Additional payment move lines if any
            if records["payment_move_line_ids"]:
                cr.execute("""
                    UPDATE account_move_line 
                    SET company_id = %s, is_company_transferred = TRUE 
                    WHERE id IN %s;
                """, [dest_id, tuple(records["payment_move_line_ids"])])

            # 5. Payments
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

            # 6. Partial Reconciles
            if records["partial_reconcile_ids"]:
                cr.execute("""
                    UPDATE account_partial_reconcile 
                    SET company_id = %s, is_company_transferred = TRUE 
                    WHERE id IN %s;
                """, [dest_id, tuple(records["partial_reconcile_ids"])])

            # 7. Bank Statement Lines
            if records["st_line_ids"]:
                bank_j = self.env["account.journal"].sudo().search([
                    ("company_id", "=", dest_id),
                    ("type", "in", ("bank", "cash")),
                ], limit=1)
                bank_jid = bank_j.id if bank_j else False
                if bank_jid:
                    cr.execute("""
                        UPDATE account_bank_statement_line 
                        SET company_id = %s, journal_id = %s, is_company_transferred = TRUE 
                        WHERE id IN %s;
                    """, [dest_id, bank_jid, tuple(records["st_line_ids"])])
                else:
                    cr.execute("""
                        UPDATE account_bank_statement_line 
                        SET company_id = %s, is_company_transferred = TRUE 
                        WHERE id IN %s;
                    """, [dest_id, tuple(records["st_line_ids"])])

            # 8. Bank Statements
            if records["statement_ids"]:
                bank_j = self.env["account.journal"].sudo().search([
                    ("company_id", "=", dest_id),
                    ("type", "in", ("bank", "cash")),
                ], limit=1)
                bank_jid = bank_j.id if bank_j else False
                if bank_jid:
                    cr.execute("""
                        UPDATE account_bank_statement 
                        SET company_id = %s, journal_id = %s, is_company_transferred = TRUE 
                        WHERE id IN %s;
                    """, [dest_id, bank_jid, tuple(records["statement_ids"])])
                else:
                    cr.execute("""
                        UPDATE account_bank_statement 
                        SET company_id = %s, is_company_transferred = TRUE 
                        WHERE id IN %s;
                    """, [dest_id, tuple(records["statement_ids"])])

        count_inv = len(records["inv_ids"])
        count_lines = len(records["inv_line_ids"])
        count_pay = len(records["payment_ids"])
        count_rec = len(records["partial_reconcile_ids"])
        count_stline = len(records["st_line_ids"])

        self.env.invalidate_all()
        summary = _(
            "Updated %(inv)s Account Moves, %(iline)s Lines, %(pay)s Payments, %(rec)s Reconciliations, %(st)s Bank Transactions to company '%(com)s'.",
            inv=count_inv,
            iline=count_lines,
            pay=count_pay,
            rec=count_rec,
            st=count_stline,
            com=self.target_company_id.display_name,
        )
        self._create_log_entry("account_move", count_inv, summary, "success")
        self.action_fetch_records_count()
        return self._notify_result(_("Account Moves & Related Classes Updated"), summary)

    def action_update_invoice_lines(self):
        """Update company_id on account.move.line records."""
        self.ensure_one()
        if not self.target_company_id:
            raise UserError(_("Please configure or select a Target Company."))

        self._ensure_transferred_columns_exist()
        so_ids = self._get_matching_so_ids()
        records = self._get_related_record_ids(so_ids)
        inv_line_ids = records["inv_line_ids"]
        if not inv_line_ids:
            summary = _("No matching Invoice Lines found to update.")
            self._create_log_entry("account_move_line", 0, summary, "nothing_to_update")
            raise UserError(summary)

        cr = self.env.cr
        dest_id = self.target_company_id.id
        cr.execute("""
            UPDATE account_move_line 
            SET company_id = %s, is_company_transferred = TRUE 
            WHERE id IN %s;
        """, [dest_id, tuple(inv_line_ids)])
        count = len(inv_line_ids)

        self.env.invalidate_all()
        summary = _("Updated %(count)s Invoice Lines/Journal Items to company '%(com)s'.", count=count, com=self.target_company_id.display_name)
        self._create_log_entry("account_move_line", count, summary, "success")
        self.action_fetch_records_count()
        return self._notify_result(_("Invoice Lines Updated"), summary)

    def action_update_payments_and_reconciles(self):
        """Update company_id and journal_id on account.payment, payment account.move, account.move.line, and account.partial.reconcile records."""
        self.ensure_one()
        if not self.target_company_id:
            raise UserError(_("Please configure or select a Target Company."))

        self._ensure_transferred_columns_exist()
        so_ids = self._get_matching_so_ids()
        records = self._get_related_record_ids(so_ids)
        pay_ids = records["payment_ids"]
        pmove_ids = records["payment_move_ids"]
        pline_ids = records["payment_move_line_ids"]
        rec_ids = records["partial_reconcile_ids"]
        st_line_ids = records["st_line_ids"]
        statement_ids = records["statement_ids"]

        if not pay_ids and not pmove_ids and not pline_ids and not rec_ids and not st_line_ids and not statement_ids:
            summary = _("No matching Payments, Payment Entries, Reconciliations or Bank Transactions found to update.")
            self._create_log_entry("account_payment", 0, summary, "nothing_to_update")
            raise UserError(summary)

        cr = self.env.cr
        dest_id = self.target_company_id.id
        pmove_map = self._get_target_journal_mapping(pmove_ids, dest_id)

        with cr.savepoint():
            for mid in pmove_ids:
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

            if pay_ids:
                payments = self.env["account.payment"].sudo().browse(pay_ids).exists()
                bank_j = self.env["account.journal"].sudo().search([
                    ("company_id", "=", dest_id),
                    ("type", "in", ("bank", "cash", "general")),
                ], limit=1)
                fallback_jid = bank_j.id if bank_j else False

                for pay in payments:
                    target_jid = False
                    if pay.move_id:
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

            if pline_ids:
                cr.execute("""
                    UPDATE account_move_line 
                    SET company_id = %s, is_company_transferred = TRUE 
                    WHERE id IN %s;
                """, [dest_id, tuple(pline_ids)])

            if rec_ids:
                cr.execute("""
                    UPDATE account_partial_reconcile 
                    SET company_id = %s, is_company_transferred = TRUE 
                    WHERE id IN %s;
                """, [dest_id, tuple(rec_ids)])

            # Bank Statement Lines
            if st_line_ids:
                bank_j = self.env["account.journal"].sudo().search([
                    ("company_id", "=", dest_id),
                    ("type", "=", "bank"),
                ], limit=1)
                target_bank_jid = bank_j.id if bank_j else False

                for stl_id in st_line_ids:
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

            # Bank Statements
            if statement_ids:
                bank_j = self.env["account.journal"].sudo().search([
                    ("company_id", "=", dest_id),
                    ("type", "=", "bank"),
                ], limit=1)
                target_bank_jid = bank_j.id if bank_j else False

                for st_id in statement_ids:
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

        total_count = (
            len(pay_ids)
            + len(pmove_ids)
            + len(pline_ids)
            + len(rec_ids)
            + len(st_line_ids)
            + len(statement_ids)
        )
        self.env.invalidate_all()
        summary = _(
            "Updated %(pay)s Payments, %(pmove)s Payment Moves, %(pline)s Payment Lines, "
            "%(rec)s Reconciliations, %(stline)s Bank Transactions, and %(stat)s Statements to company '%(com)s'.",
            pay=len(pay_ids),
            pmove=len(pmove_ids),
            pline=len(pline_ids),
            rec=len(rec_ids),
            stline=len(st_line_ids),
            stat=len(statement_ids),
            com=self.target_company_id.display_name,
        )
        self._create_log_entry("account_payment", total_count, summary, "success")
        self.action_fetch_records_count()
        return self._notify_result(_("Payments, Transactions & Reconciliations Updated"), summary)

    def action_update_selected_model(self):
        """Dispatches update based on selected model_target."""
        self.ensure_one()
        if self.model_target == "all":
            return self.action_update_all()
        elif self.model_target == "sale_order":
            return self.action_update_sale_orders()
        elif self.model_target == "sale_order_line":
            return self.action_update_sale_order_lines()
        elif self.model_target == "stock_picking":
            return self.action_update_pickings()
        elif self.model_target == "stock_move":
            return self.action_update_stock_moves()
        elif self.model_target == "account_move":
            return self.action_update_invoices()
        elif self.model_target == "account_move_line":
            return self.action_update_invoice_lines()
        elif self.model_target == "account_payment":
            return self.action_update_payments_and_reconciles()

    def action_update_all(self):
        """Update entire pipeline (SO, SOL, Pickings, Moves, Lines, Invoices, Payments, Reconciles) atomically."""
        self.ensure_one()
        if not self.target_company_id:
            raise UserError(_("Please configure or select a Target Company."))

        self._ensure_transferred_columns_exist()
        so_ids = self._get_matching_so_ids()
        records = self._get_related_record_ids(so_ids)

        total_records = (
            len(records["so_ids"]) + len(records["sol_ids"]) + len(records["picking_ids"])
            + len(records["move_ids"]) + len(records["move_line_ids"])
            + len(records["inv_ids"]) + len(records["inv_line_ids"])
            + len(records["payment_ids"]) + len(records["payment_move_ids"])
            + len(records["payment_move_line_ids"]) + len(records["partial_reconcile_ids"])
            + len(records["st_line_ids"]) + len(records["statement_ids"])
        )

        if total_records == 0:
            summary = _("No matching records found across any pipeline model to update.")
            self._create_log_entry("all", 0, summary, "nothing_to_update")
            raise UserError(summary)

        cr = self.env.cr
        dest_id = self.target_company_id.id

        with cr.savepoint():
            # 1. Sale Orders
            if records["so_ids"]:
                cr.execute("""
                    UPDATE sale_order 
                    SET company_id = %s, is_company_transferred = TRUE 
                    WHERE id IN %s;
                """, [dest_id, tuple(records["so_ids"])])

            # 2. Sale Order Lines
            if records["sol_ids"]:
                cr.execute("""
                    UPDATE sale_order_line 
                    SET company_id = %s, is_company_transferred = TRUE 
                    WHERE id IN %s;
                """, [dest_id, tuple(records["sol_ids"])])

            # 3. Pickings
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

            # 6. Invoices & Lines
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

            # 7. Additional invoice lines if any
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
            len(records["so_ids"])
            + len(records["sol_ids"])
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
            "COMPLETED PIPELINE REASSIGNMENT to '%(com)s': %(so)s SOs, %(sol)s Lines, "
            "%(pick)s Pickings, %(move)s Moves, %(inv)s Invoices, %(iline)s Invoice Lines, "
            "%(pay)s Payments, %(pmove)s Payment Moves, %(pline)s Payment Lines, "
            "%(stline)s Bank Statement Lines, %(stat)s Bank Statements, %(rec)s Reconciliations.",
            com=self.target_company_id.display_name,
            so=len(records["so_ids"]),
            sol=len(records["sol_ids"]),
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
        return self._notify_result(_("Pipeline Company Reassigned"), summary)

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
