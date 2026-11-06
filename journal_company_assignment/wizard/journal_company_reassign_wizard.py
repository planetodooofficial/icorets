# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class JournalCompanyReassignWizard(models.TransientModel):
    _name = "journal.company.reassign.wizard"
    _description = "Reassign Journal Entries & Linked Sale Orders to Branch Company"

    journal_id = fields.Many2one(
        "account.journal",
        string="Journal",
        required=True,
        readonly=True,
    )
    source_company_id = fields.Many2one(
        "res.company",
        string="From / Source Company",
        required=True,
        default=lambda self: self.env.company,
    )
    target_company_id = fields.Many2one(
        "res.company",
        string="To / Target Branch Company",
        required=True,
    )

    # Counts
    count_matching_entries = fields.Integer(
        string="Matching Journal Entries",
        readonly=True,
    )
    count_matching_lines = fields.Integer(
        string="Matching Journal Items",
        readonly=True,
    )
    count_linked_sos = fields.Integer(
        string="Linked Sale Orders",
        readonly=True,
    )
    count_linked_pickings = fields.Integer(
        string="Linked Delivery Pickings",
        readonly=True,
    )
    count_linked_stock_moves = fields.Integer(
        string="Linked Stock Moves",
        readonly=True,
    )
    count_linked_payments = fields.Integer(
        string="Linked Payments",
        readonly=True,
    )

    state = fields.Selection(
        [
            ("draft", "Criteria Setup"),
            ("fetched", "Records Fetched"),
            ("done", "Completed"),
        ],
        string="Status",
        default="draft",
        readonly=True,
    )

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
        ]
        for table in tables:
            cr.execute(f"""
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = '{table}' AND column_name = 'is_company_transferred';
            """)
            if not cr.fetchone():
                try:
                    cr.execute(f"ALTER TABLE {table} ADD COLUMN is_company_transferred BOOLEAN DEFAULT FALSE;")
                except Exception:
                    pass

    def _get_matching_move_ids(self):
        """Query matching journal entries based on criteria."""
        self.ensure_one()
        cr = self.env.cr
        cr.execute("""
            SELECT id FROM account_move 
            WHERE journal_id = %s AND company_id = %s;
        """, [self.journal_id.id, self.source_company_id.id])
        return [r[0] for r in cr.fetchall()]

    def _get_linked_so_and_related_records(self, move_ids):
        """Find Sale Orders and all their related operations linked to given journal entries."""
        if not move_ids:
            return {
                "so_ids": [],
                "sol_ids": [],
                "picking_ids": [],
                "stock_move_ids": [],
                "stock_move_line_ids": [],
                "extra_move_ids": [],
                "payment_ids": [],
                "payment_move_ids": [],
                "partial_reconcile_ids": [],
            }

        cr = self.env.cr
        move_tuple = tuple(move_ids)
        so_ids = []

        # 1. Via sale_order_line_invoice_rel
        cr.execute("""
            SELECT 1 FROM information_schema.tables WHERE table_name = 'sale_order_line_invoice_rel';
        """)
        if cr.fetchone():
            cr.execute("""
                SELECT DISTINCT sol.order_id 
                FROM sale_order_line_invoice_rel rel
                JOIN account_move_line aml ON rel.invoice_line_id = aml.id
                JOIN sale_order_line sol ON rel.order_line_id = sol.id
                WHERE aml.move_id IN %s;
            """, [move_tuple])
            for r in cr.fetchall():
                if r[0] and r[0] not in so_ids:
                    so_ids.append(r[0])

        # 2. Via account_move.invoice_origin
        cr.execute("""
            SELECT DISTINCT so.id 
            FROM sale_order so
            JOIN account_move am ON am.invoice_origin = so.name
            WHERE am.id IN %s;
        """, [move_tuple])
        for r in cr.fetchall():
            if r[0] and r[0] not in so_ids:
                so_ids.append(r[0])

        # 3. Via account_move.ref
        cr.execute("""
            SELECT DISTINCT so.id 
            FROM sale_order so
            JOIN account_move am ON am.ref = so.name
            WHERE am.id IN %s;
        """, [move_tuple])
        for r in cr.fetchall():
            if r[0] and r[0] not in so_ids:
                so_ids.append(r[0])

        # 4. Via stock moves linked to moves
        cr.execute("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'account_move' AND column_name = 'stock_move_id';
        """)
        if cr.fetchone():
            cr.execute("""
                SELECT DISTINCT sp.sale_id 
                FROM account_move am
                JOIN stock_move sm ON am.stock_move_id = sm.id
                JOIN stock_picking sp ON sm.picking_id = sp.id
                WHERE am.id IN %s AND sp.sale_id IS NOT NULL;
            """, [move_tuple])
            for r in cr.fetchall():
                if r[0] and r[0] not in so_ids:
                    so_ids.append(r[0])

        cr.execute("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'stock_move' AND column_name = 'account_move_id';
        """)
        if cr.fetchone():
            cr.execute("""
                SELECT DISTINCT sp.sale_id 
                FROM stock_move sm
                JOIN stock_picking sp ON sm.picking_id = sp.id
                WHERE sm.account_move_id IN %s AND sp.sale_id IS NOT NULL;
            """, [move_tuple])
            for r in cr.fetchall():
                if r[0] and r[0] not in so_ids:
                    so_ids.append(r[0])

        # If no Sale Orders linked, return empty related sets
        if not so_ids:
            return {
                "so_ids": [],
                "sol_ids": [],
                "picking_ids": [],
                "stock_move_ids": [],
                "stock_move_line_ids": [],
                "extra_move_ids": [],
                "payment_ids": [],
                "payment_move_ids": [],
                "partial_reconcile_ids": [],
            }

        so_tuple = tuple(so_ids)

        # 5. Sale Order Lines
        cr.execute("SELECT id FROM sale_order_line WHERE order_id IN %s;", [so_tuple])
        sol_ids = [r[0] for r in cr.fetchall()]
        sol_tuple = tuple(sol_ids) if sol_ids else (0,)

        # 6. Delivery Pickings
        picking_ids = []
        cr.execute("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'stock_picking' AND column_name = 'sale_id';
        """)
        if cr.fetchone():
            cr.execute("SELECT id FROM stock_picking WHERE sale_id IN %s;", [so_tuple])
            picking_ids = [r[0] for r in cr.fetchall()]

        if sol_ids:
            cr.execute("""
                SELECT DISTINCT picking_id FROM stock_move 
                WHERE sale_line_id IN %s AND picking_id IS NOT NULL;
            """, [sol_tuple])
            for r in cr.fetchall():
                if r[0] not in picking_ids:
                    picking_ids.append(r[0])
        picking_tuple = tuple(picking_ids) if picking_ids else (0,)

        # 7. Stock Moves & Move Lines
        stock_move_ids = []
        if picking_ids or sol_ids:
            cr.execute("""
                SELECT id FROM stock_move 
                WHERE picking_id IN %s OR sale_line_id IN %s;
            """, [picking_tuple, sol_tuple])
            stock_move_ids = [r[0] for r in cr.fetchall()]
        sm_tuple = tuple(stock_move_ids) if stock_move_ids else (0,)

        stock_move_line_ids = []
        if picking_ids or stock_move_ids:
            cr.execute("""
                SELECT id FROM stock_move_line 
                WHERE picking_id IN %s OR move_id IN %s;
            """, [picking_tuple, sm_tuple])
            stock_move_line_ids = [r[0] for r in cr.fetchall()]

        # 8. Extra related account_moves from these SOs (if any)
        extra_move_ids = []
        cr.execute("SELECT name FROM sale_order WHERE id IN %s;", [so_tuple])
        so_names = tuple(r[0] for r in cr.fetchall() if r[0])
        if so_names:
            cr.execute("SELECT id FROM account_move WHERE invoice_origin IN %s;", [so_names])
            for r in cr.fetchall():
                if r[0] not in move_ids and r[0] not in extra_move_ids:
                    extra_move_ids.append(r[0])

        all_move_ids = list(set(list(move_ids) + extra_move_ids))
        all_move_tuple = tuple(all_move_ids)

        # 9. Payment moves and reconciliations
        partial_reconcile_ids = []
        payment_move_ids = []
        payment_ids = []
        if all_move_ids:
            cr.execute("SELECT id FROM account_move_line WHERE move_id IN %s;", [all_move_tuple])
            all_aml_ids = [r[0] for r in cr.fetchall()]
            if all_aml_ids:
                aml_t = tuple(all_aml_ids)
                cr.execute("""
                    SELECT id, debit_move_id, credit_move_id 
                    FROM account_partial_reconcile 
                    WHERE debit_move_id IN %s OR credit_move_id IN %s;
                """, [aml_t, aml_t])
                recs = cr.fetchall()
                partial_reconcile_ids = [r[0] for r in recs]
                cp_aml_ids = set()
                aml_set = set(all_aml_ids)
                for r in recs:
                    if r[1] not in aml_set:
                        cp_aml_ids.add(r[1])
                    if r[2] not in aml_set:
                        cp_aml_ids.add(r[2])
                if cp_aml_ids:
                    cr.execute("SELECT DISTINCT move_id FROM account_move_line WHERE id IN %s;", [tuple(cp_aml_ids)])
                    payment_move_ids = [r[0] for r in cr.fetchall() if r[0] not in all_move_ids]

            # Payment records from payment moves
            if payment_move_ids:
                cr.execute("SELECT id FROM account_payment WHERE move_id IN %s;", [tuple(payment_move_ids)])
                payment_ids = [r[0] for r in cr.fetchall()]

        return {
            "so_ids": so_ids,
            "sol_ids": sol_ids,
            "picking_ids": picking_ids,
            "stock_move_ids": stock_move_ids,
            "stock_move_line_ids": stock_move_line_ids,
            "extra_move_ids": extra_move_ids,
            "payment_ids": payment_ids,
            "payment_move_ids": payment_move_ids,
            "partial_reconcile_ids": partial_reconcile_ids,
        }

    def action_fetch_records(self):
        """Step 1: Fetch and count matching journal entries, items, and linked Sale Orders & operations."""
        self.ensure_one()
        if not self.source_company_id:
            raise UserError(_("Please select a Source Company."))
        if not self.target_company_id:
            raise UserError(_("Please select a Target Company."))
        if self.source_company_id == self.target_company_id:
            raise UserError(_("Source Company and Target Company cannot be the same."))

        move_ids = self._get_matching_move_ids()
        c_entries = len(move_ids)
        c_lines = 0

        if move_ids:
            cr = self.env.cr
            cr.execute("SELECT count(id) FROM account_move_line WHERE move_id IN %s;", [tuple(move_ids)])
            res = cr.fetchone()
            c_lines = res[0] if res else 0

        # Scan for linked Sale Orders & related operations
        rel = self._get_linked_so_and_related_records(move_ids)

        self.write({
            "count_matching_entries": c_entries,
            "count_matching_lines": c_lines,
            "count_linked_sos": len(rel["so_ids"]),
            "count_linked_pickings": len(rel["picking_ids"]),
            "count_linked_stock_moves": len(rel["stock_move_ids"]),
            "count_linked_payments": len(rel["payment_ids"]),
            "state": "fetched",
        })

        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_reassign_company(self):
        """Step 2: Reassign company on all fetched journal entries, items, and linked Sale Orders & operations."""
        self.ensure_one()
        if not self.target_company_id:
            raise UserError(_("Please select a Target Company."))

        move_ids = self._get_matching_move_ids()
        if not move_ids:
            raise UserError(_("No matching journal entries found in this journal to transfer."))

        self._ensure_transferred_columns_exist()

        cr = self.env.cr
        dest_company_id = self.target_company_id.id
        rel = self._get_linked_so_and_related_records(move_ids)

        with cr.savepoint():
            # 1. Update all account.move (entries in this journal + extra SO invoices + payment moves)
            all_moves = list(set(list(move_ids) + rel["extra_move_ids"] + rel["payment_move_ids"]))
            if all_moves:
                all_move_tuple = tuple(all_moves)
                cr.execute("""
                    UPDATE account_move 
                    SET company_id = %s, is_company_transferred = TRUE 
                    WHERE id IN %s;
                """, [dest_company_id, all_move_tuple])

                cr.execute("""
                    UPDATE account_move_line 
                    SET company_id = %s, is_company_transferred = TRUE 
                    WHERE move_id IN %s;
                """, [dest_company_id, all_move_tuple])

            # 2. Update Sale Orders & Lines
            if rel["so_ids"]:
                cr.execute("""
                    UPDATE sale_order 
                    SET company_id = %s, is_company_transferred = TRUE 
                    WHERE id IN %s;
                """, [dest_company_id, tuple(rel["so_ids"])])

            if rel["sol_ids"]:
                cr.execute("""
                    UPDATE sale_order_line 
                    SET company_id = %s, is_company_transferred = TRUE 
                    WHERE id IN %s;
                """, [dest_company_id, tuple(rel["sol_ids"])])

            # 3. Update Delivery Pickings & Stock Moves
            if rel["picking_ids"]:
                cr.execute("""
                    UPDATE stock_picking 
                    SET company_id = %s, is_company_transferred = TRUE 
                    WHERE id IN %s;
                """, [dest_company_id, tuple(rel["picking_ids"])])

            if rel["stock_move_ids"]:
                cr.execute("""
                    UPDATE stock_move 
                    SET company_id = %s, is_company_transferred = TRUE 
                    WHERE id IN %s;
                """, [dest_company_id, tuple(rel["stock_move_ids"])])

            if rel["stock_move_line_ids"]:
                cr.execute("""
                    UPDATE stock_move_line 
                    SET company_id = %s, is_company_transferred = TRUE 
                    WHERE id IN %s;
                """, [dest_company_id, tuple(rel["stock_move_line_ids"])])

            # 4. Update Payments
            if rel["payment_ids"]:
                cr.execute("""
                    UPDATE account_payment 
                    SET company_id = %s, is_company_transferred = TRUE 
                    WHERE id IN %s;
                """, [dest_company_id, tuple(rel["payment_ids"])])

            # 5. Update Reconciliations
            if rel["partial_reconcile_ids"]:
                cr.execute("""
                    UPDATE account_partial_reconcile 
                    SET company_id = %s, is_company_transferred = TRUE 
                    WHERE id IN %s;
                """, [dest_company_id, tuple(rel["partial_reconcile_ids"])])

        self.env.invalidate_all()
        self.write({"state": "done"})

        msg_parts = [
            f"{len(move_ids)} Journal Entries",
        ]
        if rel["so_ids"]:
            msg_parts.append(f"{len(rel['so_ids'])} Sale Orders")
        if rel["picking_ids"]:
            msg_parts.append(f"{len(rel['picking_ids'])} Pickings")
        if rel["stock_move_ids"]:
            msg_parts.append(f"{len(rel['stock_move_ids'])} Stock Moves")
        if rel["payment_ids"]:
            msg_parts.append(f"{len(rel['payment_ids'])} Payments")

        msg = _(
            "Successfully reassigned %(details)s to company '%(com)s'.",
            details=", ".join(msg_parts),
            com=self.target_company_id.display_name,
        )

        # Create persistent audit log
        total_records_updated = (
            len(all_moves) + len(rel["so_ids"]) + len(rel["sol_ids"]) 
            + len(rel["picking_ids"]) + len(rel["stock_move_ids"]) 
            + len(rel["payment_ids"]) + len(rel["partial_reconcile_ids"])
        )
        self.env["journal.company.reassignment.log"].sudo().create({
            "journal_id": self.journal_id.id,
            "source_company_id": self.source_company_id.id,
            "target_company_id": dest_company_id,
            "action_type": "manual",
            "records_updated": total_records_updated,
            "status": "success",
            "summary": msg,
        })

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Reassignment Completed"),
                "message": msg,
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
