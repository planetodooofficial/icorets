# -*- coding: utf-8 -*-
import re
from collections import defaultdict
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class JournalPickingMatchWizard(models.TransientModel):
    _name = "journal.picking.match.wizard"
    _description = "Reassign Journal Entries by Stock Picking Match"

    journal_id = fields.Many2one(
        "account.journal",
        string="Journal",
        required=True,
        readonly=True,
    )
    source_company_id = fields.Many2one(
        "res.company",
        string="Source Company (Optional)",
        required=False,
        help="Optional: Filter journal entries currently belonging to this company. Leave empty to scan all entries in this journal where company differs from picking.",
    )

    count_total_entries = fields.Integer(
        string="Total Journal Entries",
        readonly=True,
    )
    count_matched_entries = fields.Integer(
        string="Matched Journal Entries",
        readonly=True,
    )
    count_unmatched_entries = fields.Integer(
        string="Not Matched Records",
        readonly=True,
    )
    count_matched_lines = fields.Integer(
        string="Matched Journal Items",
        readonly=True,
    )
    match_summary = fields.Html(
        string="Match Breakdown & Preview",
        readonly=True,
    )
    match_type = fields.Selection(
        [
            ("picking", "Stock Picking Match (e.g. DEL/OUT/..., DEL/RET/...)"),
            ("bill", "Bill / Invoice / Credit & Debit Note Match (e.g. BLIPDL/2627/1174)"),
        ],
        string="Matching Mode",
        default="picking",
        required=True,
    )
    state = fields.Selection(
        [
            ("draft", "Setup Criteria"),
            ("fetched", "Matches Previewed"),
            ("done", "Completed"),
        ],
        string="Status",
        default="draft",
        readonly=True,
    )

    def _ensure_transferred_columns_exist(self):
        """Ensure is_company_transferred column exists on account_move and account_move_line."""
        cr = self.env.cr
        tables = [
            "account_move",
            "account_move_line",
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

    def _find_picking_matches(self):
        """Find matching account.move records in this journal where stock.picking has a company set."""
        self.ensure_one()
        cr = self.env.cr
        j_id = self.journal_id.id

        params_base = [j_id]
        company_filter = ""
        if self.source_company_id:
            company_filter = "AND am.company_id = %s"
            params_base.append(self.source_company_id.id)

        # Map move_id -> dict(picking_id, target_company_id, picking_name, entry_ref, current_company_id)
        matches = {}

        # 1. Primary Match: Extract picking number from account_move.ref using fast regex CTE
        # Examples handled:
        # - 'Revaluation of DEL/OUT/2627/1996109 (negative inventory)' -> extracted: 'DEL/OUT/2627/1996109'
        # - 'DEL/RET/2627/02909 - Skin Pants' -> extracted: 'DEL/RET/2627/02909'
        # - 'DEL/OUT/2627/199738' -> extracted: 'DEL/OUT/2627/199738'
        #
        # Performance note: We pre-extract the picking name in a subquery/CTE so PostgreSQL can 
        # use the primary B-tree index on `stock_picking(name)` instead of doing an unindexed
        # full table scan with Cartesian ILIKE '%...%' evaluation.
        cr.execute(f"""
            WITH journal_entries AS (
                SELECT 
                    am.id AS move_id,
                    am.ref AS entry_ref,
                    am.company_id AS current_company_id,
                    COALESCE(
                        NULLIF(TRIM(REGEXP_REPLACE(SPLIT_PART(SPLIT_PART(SPLIT_PART(am.ref, ' (', 1), ' - ', 1), ': ', 1), '^(Revaluation of |Reversal of )', '', 'i')), ''),
                        NULLIF(SUBSTRING(am.ref FROM '[A-Za-z0-9]+/[A-Za-z0-9/]+'), ''),
                        TRIM(am.ref)
                    ) AS extracted_picking_name
                FROM account_move am
                WHERE am.journal_id = %s {company_filter}
                  AND am.move_type = 'entry'
                  AND am.ref IS NOT NULL 
                  AND TRIM(am.ref) != ''
            )
            SELECT DISTINCT ON (je.move_id)
                je.move_id, 
                sp.id, 
                sp.company_id, 
                sp.name, 
                je.entry_ref, 
                je.current_company_id
            FROM journal_entries je
            JOIN stock_picking sp ON sp.name = je.extracted_picking_name
            WHERE sp.company_id IS NOT NULL 
              AND je.current_company_id != sp.company_id
            ORDER BY je.move_id, sp.id DESC;
        """, params_base)
        for r in cr.fetchall():
            matches[r[0]] = {
                "picking_id": r[1],
                "target_company_id": r[2],
                "picking_name": r[3],
                "entry_ref": r[4],
                "current_company_id": r[5],
            }

        # 2. Secondary check via stock_move if ref is populated and matches picking
        cr.execute("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'stock_move' AND column_name = 'account_move_id';
        """)
        has_acc_move_id = bool(cr.fetchone())
        if has_acc_move_id:
            cr.execute(f"""
                WITH journal_entries AS (
                    SELECT 
                        am.id AS move_id,
                        am.ref AS entry_ref,
                        am.company_id AS current_company_id,
                        COALESCE(
                            NULLIF(TRIM(REGEXP_REPLACE(SPLIT_PART(SPLIT_PART(SPLIT_PART(am.ref, ' (', 1), ' - ', 1), ': ', 1), '^(Revaluation of |Reversal of )', '', 'i')), ''),
                            NULLIF(SUBSTRING(am.ref FROM '[A-Za-z0-9]+/[A-Za-z0-9/]+'), ''),
                            TRIM(am.ref)
                        ) AS extracted_picking_name
                    FROM account_move am
                    WHERE am.journal_id = %s {company_filter}
                      AND am.move_type = 'entry'
                      AND am.ref IS NOT NULL
                      AND TRIM(am.ref) != ''
                )
                SELECT je.move_id, sp.id, sp.company_id, sp.name, je.entry_ref, je.current_company_id
                FROM journal_entries je
                JOIN stock_move sm ON sm.account_move_id = je.move_id
                JOIN stock_picking sp ON (sm.picking_id = sp.id AND sp.name = je.extracted_picking_name)
                WHERE sp.company_id IS NOT NULL 
                  AND je.current_company_id != sp.company_id;
            """, params_base)
            for r in cr.fetchall():
                if r[0] not in matches:
                    matches[r[0]] = {
                        "picking_id": r[1],
                        "target_company_id": r[2],
                        "picking_name": r[3],
                        "entry_ref": r[4],
                        "current_company_id": r[5],
                    }

        return matches

    def _find_bill_matches(self):
        """Find matching account.move records in this journal where reference matches a
        Vendor Bill, Customer Invoice, Credit Note, or Debit Note (account.move)."""
        self.ensure_one()
        cr = self.env.cr
        j_id = self.journal_id.id

        params_base = [j_id]
        company_filter = ""
        if self.source_company_id:
            company_filter = "AND am.company_id = %s"
            params_base.append(self.source_company_id.id)

        matches = {}

        # Performance optimized CTE: Separates matching by name and matching by ref
        # so PostgreSQL can use the primary B-tree indexes instead of a slow unindexed OR table scan.
        cr.execute(f"""
            WITH journal_entries AS (
                SELECT 
                    am.id AS move_id,
                    am.ref AS entry_ref,
                    am.company_id AS current_company_id,
                    COALESCE(
                        NULLIF(TRIM(REGEXP_REPLACE(SPLIT_PART(SPLIT_PART(SPLIT_PART(am.ref, ' (', 1), ' - ', 1), ': ', 1), '^(Revaluation of |Reversal of )', '', 'i')), ''),
                        NULLIF(SUBSTRING(am.ref FROM '[A-Za-z0-9]+/[A-Za-z0-9/]+'), ''),
                        TRIM(am.ref)
                    ) AS extracted_doc_name
                FROM account_move am
                WHERE am.journal_id = %s {company_filter}
                  AND am.move_type = 'entry'
                  AND am.ref IS NOT NULL 
                  AND TRIM(am.ref) != ''
            ),
            matched_by_name AS (
                SELECT DISTINCT ON (je.move_id)
                    je.move_id, 
                    inv.id AS bill_id, 
                    inv.company_id AS target_company_id, 
                    inv.name AS bill_name, 
                    inv.move_type AS doc_type,
                    je.entry_ref, 
                    je.current_company_id
                FROM journal_entries je
                JOIN account_move inv ON inv.name = je.extracted_doc_name
                WHERE inv.id != je.move_id
                  AND inv.move_type != 'entry'
                  AND inv.company_id IS NOT NULL 
                  AND je.current_company_id != inv.company_id
                ORDER BY je.move_id, inv.id DESC
            ),
            matched_by_ref AS (
                SELECT DISTINCT ON (je.move_id)
                    je.move_id, 
                    inv.id AS bill_id, 
                    inv.company_id AS target_company_id, 
                    inv.name AS bill_name, 
                    inv.move_type AS doc_type,
                    je.entry_ref, 
                    je.current_company_id
                FROM journal_entries je
                JOIN account_move inv ON (inv.ref = je.extracted_doc_name AND inv.ref IS NOT NULL AND inv.ref != '')
                WHERE inv.id != je.move_id
                  AND inv.move_type != 'entry'
                  AND inv.company_id IS NOT NULL 
                  AND je.current_company_id != inv.company_id
                  AND je.move_id NOT IN (SELECT move_id FROM matched_by_name)
                ORDER BY je.move_id, inv.id DESC
            )
            SELECT * FROM matched_by_name
            UNION ALL
            SELECT * FROM matched_by_ref;
        """, params_base)
        for r in cr.fetchall():
            matches[r[0]] = {
                "bill_id": r[1],
                "target_company_id": r[2],
                "bill_name": r[3],
                "doc_type": r[4],
                "entry_ref": r[5],
                "current_company_id": r[6],
            }

        return matches

    def action_fetch_matches(self):
        """Step 1: Scan journal entries matching picking numbers and generate preview summary."""
        self.ensure_one()
        cr = self.env.cr
        j_id = self.journal_id.id

        params_base = [j_id]
        company_filter = ""
        if self.source_company_id:
            company_filter = "AND am.company_id = %s"
            params_base.append(self.source_company_id.id)

        # 1. Total journal entries in this journal where move_type = 'entry'
        cr.execute(f"""
            SELECT count(id) FROM account_move am
            WHERE am.journal_id = %s {company_filter}
              AND am.move_type = 'entry';
        """, params_base)
        res_total = cr.fetchone()
        c_total = res_total[0] if res_total else 0

        # 2. Matched entries
        matches = self._find_picking_matches()
        move_ids = list(matches.keys())
        c_entries = len(move_ids)
        c_lines = 0
        c_unmatched = max(0, c_total - c_entries)

        # Group matches by target company for preview
        company_counts = defaultdict(list)
        sample_refs = defaultdict(list)
        for mid, data in matches.items():
            company_counts[data["target_company_id"]].append(data["picking_name"])
            if data.get("entry_ref"):
                sample_refs[data["target_company_id"]].append(data["entry_ref"])

        if move_ids:
            chunk_size = 2000
            for i in range(0, len(move_ids), chunk_size):
                chunk = tuple(move_ids[i:i + chunk_size])
                cr.execute("SELECT count(id) FROM account_move_line WHERE move_id IN %s;", [chunk])
                res = cr.fetchone()
                c_lines += res[0] if res else 0

        # Build matched rows
        html_rows = []
        for comp_id, pick_names in company_counts.items():
            company_rec = self.env["res.company"].browse(comp_id)
            comp_name = company_rec.display_name if company_rec.exists() else f"Company ID {comp_id}"
            sample_picks = ", ".join(sorted(set(pick_names))[:4])
            if len(set(pick_names)) > 4:
                sample_picks += f" ... (+{len(set(pick_names)) - 4} more)"

            s_refs = sample_refs.get(comp_id, [])
            sample_ref_str = ", ".join(sorted(set(s_refs))[:2])
            if len(set(s_refs)) > 2:
                sample_ref_str += f" ... (+{len(set(s_refs)) - 2} more)"

            html_rows.append(f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>{comp_name}</strong> (ID: {comp_id})</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center; color: #2e7d32;"><strong>{len(pick_names)}</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: #2e7d32;"><code>{sample_picks}</code></td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: #555; font-size: 11px;">{sample_ref_str}</td>
                </tr>
            """)

        # Build unmatched sample rows
        unmatched_rows = []
        if c_unmatched > 0:
            cr.execute(f"""
                SELECT am.id, am.name, am.ref, am.company_id
                FROM account_move am
                WHERE am.journal_id = %s {company_filter}
                  AND am.move_type = 'entry'
                ORDER BY am.id DESC LIMIT 50;
            """, params_base)
            matched_set = set(move_ids)
            unmatched_candidates = [r for r in cr.fetchall() if r[0] not in matched_set][:6]

            for r in unmatched_candidates:
                mname, mref, mcom = r[1] or "", r[2] or "", r[3]
                if not mref.strip():
                    reason = '<span style="background-color: #6c757d; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">Blank Reference</span>'
                else:
                    cand_name = re.sub(r'^(?:Revaluation of |Reversal of )\s*', '', mref, flags=re.I).split(" (")[0].split(" - ")[0].split(": ")[0].strip()
                    if not cand_name:
                        cand_name = mref.strip()
                    cr.execute("SELECT id, company_id FROM stock_picking WHERE name = %s LIMIT 1;", [cand_name])
                    p_row = cr.fetchone()
                    if not p_row:
                        reason = f'<span style="background-color: #fd7e14; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">Picking Not Found: {cand_name}</span>'
                    elif p_row[1] == mcom:
                        reason = '<span style="background-color: #0dcaf0; color: black; padding: 2px 6px; border-radius: 3px; font-size: 11px;">Already in Picking Company</span>'
                    else:
                        reason = '<span style="background-color: #6c757d; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">Excluded</span>'

                unmatched_rows.append(f"""
                    <tr>
                        <td style="padding: 6px; border: 1px solid #ddd;">{mname}</td>
                        <td style="padding: 6px; border: 1px solid #ddd; color: #555;">{mref or '<em>(blank)</em>'}</td>
                        <td style="padding: 6px; border: 1px solid #ddd;">{reason}</td>
                    </tr>
                """)

        summary_parts = [
            f"""
            <div class="alert alert-info" style="margin-bottom: 12px; font-size: 13px;">
                <strong>📊 Total Entries (move_type='entry'):</strong> {c_total} &nbsp;|&nbsp;
                <strong style="color: #2e7d32;">✅ Matched to Swap:</strong> {c_entries} entries ({c_lines} items) &nbsp;|&nbsp;
                <strong style="color: #d32f2f;">⚠️ Not Matched:</strong> {c_unmatched} records
            </div>
            """
        ]

        if html_rows:
            summary_parts.append(f"""
                <h6 style="color: #2e7d32; margin-top: 8px;"><strong>✅ Matched Records Breakdown (Ready to Swap):</strong></h6>
                <table class="table table-bordered table-sm" style="width: 100%; border-collapse: collapse; margin-bottom: 12px;">
                    <thead style="background-color: #e8f5e9;">
                        <tr>
                            <th style="padding: 8px; border: 1px solid #ddd;">Target Branch Company (from Picking)</th>
                            <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">Entries to Swap</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">Matched Stock Picking Number</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">Sample Entry Ref</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(html_rows)}
                    </tbody>
                </table>
            """)
        else:
            summary_parts.append("""
                <div class="alert alert-warning" style="margin-top: 10px;">
                    <strong>No journal entries found in this journal matching any Stock Picking numbers with different companies.</strong>
                </div>
            """)

        if unmatched_rows:
            summary_parts.append(f"""
                <h6 style="color: #6c757d; margin-top: 12px;"><strong>⚠️ Sample Not Matched Records ({c_unmatched} total):</strong></h6>
                <table class="table table-bordered table-sm" style="width: 100%; border-collapse: collapse; font-size: 12px;">
                    <thead style="background-color: #f8f9fa;">
                        <tr>
                            <th style="padding: 6px; border: 1px solid #ddd;">Entry Name</th>
                            <th style="padding: 6px; border: 1px solid #ddd;">Reference</th>
                            <th style="padding: 6px; border: 1px solid #ddd;">Reason Not Matched</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(unmatched_rows)}
                    </tbody>
                </table>
            """)

        summary_html = "".join(summary_parts)

        self.write({
            "count_total_entries": c_total,
            "count_matched_entries": c_entries,
            "count_unmatched_entries": c_unmatched,
            "count_matched_lines": c_lines,
            "match_summary": summary_html,
            "match_type": "picking",
            "state": "fetched",
        })

        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_reassign_by_picking(self):
        """Step 2: Swap company on matched journal entries and items to the company set on their matching stock picking."""
        self.ensure_one()
        matches = self._find_picking_matches()
        if not matches:
            raise UserError(_("No matching journal entries found to reassign."))

        self._ensure_transferred_columns_exist()

        cr = self.env.cr
        # Group move_ids by target_company_id
        company_moves = defaultdict(list)
        for mid, data in matches.items():
            company_moves[data["target_company_id"]].append(mid)

        total_entries = 0
        total_lines = 0

        with cr.savepoint():
            for target_company_id, move_ids in company_moves.items():
                chunk_size = 1000
                for i in range(0, len(move_ids), chunk_size):
                    chunk_mids = tuple(move_ids[i:i + chunk_size])

                    # 1. Update account.move: swap company_id to the picking's company_id
                    cr.execute("""
                        UPDATE account_move 
                        SET company_id = %s, is_company_transferred = TRUE 
                        WHERE id IN %s;
                    """, [target_company_id, chunk_mids])

                    # 2. Update account.move.line: swap company_id to the picking's company_id
                    cr.execute("""
                        UPDATE account_move_line 
                        SET company_id = %s, is_company_transferred = TRUE 
                        WHERE move_id IN %s;
                    """, [target_company_id, chunk_mids])

                    # 3. Update account.partial.reconcile where applicable
                    cr.execute("SELECT id FROM account_move_line WHERE move_id IN %s;", [chunk_mids])
                    aml_ids = [r[0] for r in cr.fetchall()]
                    if aml_ids:
                        aml_chunk_size = 1000
                        for j in range(0, len(aml_ids), aml_chunk_size):
                            aml_chunk = tuple(aml_ids[j:j + aml_chunk_size])
                            cr.execute("""
                                UPDATE account_partial_reconcile 
                                SET company_id = %s, is_company_transferred = TRUE 
                                WHERE debit_move_id IN %s OR credit_move_id IN %s;
                            """, [target_company_id, aml_chunk, aml_chunk])

                    total_entries += len(chunk_mids)
                    total_lines += len(aml_ids)

        self.env.invalidate_all()
        self.write({"state": "done"})

        msg = _(
            "Successfully swapped company on %(count)s Journal Entries (%(lines)s items) to their matching Stock Pickings' companies across %(comps)s branch(es).",
            count=total_entries,
            lines=total_lines,
            comps=len(company_moves),
        )

        # Create persistent audit logs for each target branch company
        for target_company_id, move_ids in company_moves.items():
            comp_rec = self.env["res.company"].browse(target_company_id)
            comp_name = comp_rec.display_name if comp_rec.exists() else f"Company ID {target_company_id}"
            src_name = self.source_company_id.display_name if self.source_company_id else _("Multiple / Original")
            self.env["journal.company.reassignment.log"].sudo().create({
                "journal_id": self.journal_id.id,
                "source_company_id": self.source_company_id.id if self.source_company_id else False,
                "target_company_id": target_company_id,
                "action_type": "picking_match",
                "records_updated": len(move_ids),
                "status": "success",
                "summary": _("Swapped company on %(count)s Journal Entries in journal '%(j)s' (from %(src)s) to branch '%(com)s' based on matched Stock Picking numbers.",
                             count=len(move_ids), j=self.journal_id.display_name, src=src_name, com=comp_name),
            })

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Picking Match Company Swap Completed"),
                "message": msg,
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def action_fetch_bill_matches(self):
        """Step 1 (Bill / Note): Scan journal entries matching Bill / Invoice / Credit & Debit Note numbers and generate preview summary."""
        self.ensure_one()
        cr = self.env.cr
        j_id = self.journal_id.id

        params_base = [j_id]
        company_filter = ""
        if self.source_company_id:
            company_filter = "AND am.company_id = %s"
            params_base.append(self.source_company_id.id)

        # 1. Total journal entries in this journal where move_type = 'entry'
        cr.execute(f"""
            SELECT count(id) FROM account_move am
            WHERE am.journal_id = %s {company_filter}
              AND am.move_type = 'entry';
        """, params_base)
        res_total = cr.fetchone()
        c_total = res_total[0] if res_total else 0

        # 2. Matched entries
        matches = self._find_bill_matches()
        move_ids = list(matches.keys())
        c_entries = len(move_ids)
        c_lines = 0
        c_unmatched = max(0, c_total - c_entries)

        # Helper for doc_type labels
        doc_type_names = {
            "in_invoice": "Vendor Bill",
            "out_invoice": "Customer Invoice",
            "in_refund": "Vendor Credit / Debit Note",
            "out_refund": "Customer Credit Note",
            "in_receipt": "Purchase Receipt",
            "out_receipt": "Sales Receipt",
        }

        # Group matches by target company for preview
        company_counts = defaultdict(list)
        company_doc_types = defaultdict(set)
        sample_refs = defaultdict(list)
        for mid, data in matches.items():
            company_counts[data["target_company_id"]].append(data["bill_name"])
            dtype_label = doc_type_names.get(data.get("doc_type"), "Bill / Invoice")
            company_doc_types[data["target_company_id"]].add(dtype_label)
            if data.get("entry_ref"):
                sample_refs[data["target_company_id"]].append(data["entry_ref"])

        if move_ids:
            chunk_size = 2000
            for i in range(0, len(move_ids), chunk_size):
                chunk = tuple(move_ids[i:i + chunk_size])
                cr.execute("SELECT count(id) FROM account_move_line WHERE move_id IN %s;", [chunk])
                res = cr.fetchone()
                c_lines += res[0] if res else 0

        # Build matched rows
        html_rows = []
        for comp_id, doc_names in company_counts.items():
            company_rec = self.env["res.company"].browse(comp_id)
            comp_name = company_rec.display_name if company_rec.exists() else f"Company ID {comp_id}"
            sample_docs = ", ".join(sorted(set(doc_names))[:4])
            if len(set(doc_names)) > 4:
                sample_docs += f" ... (+{len(set(doc_names)) - 4} more)"

            s_refs = sample_refs.get(comp_id, [])
            sample_ref_str = ", ".join(sorted(set(s_refs))[:2])
            if len(set(s_refs)) > 2:
                sample_ref_str += f" ... (+{len(set(s_refs)) - 2} more)"

            type_labels = ", ".join(sorted(company_doc_types.get(comp_id, [])))

            html_rows.append(f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>{comp_name}</strong> (ID: {comp_id})</td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center; color: #2e7d32;"><strong>{len(doc_names)}</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: #0d6efd;">{type_labels}</td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: #2e7d32;"><code>{sample_docs}</code></td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: #555; font-size: 11px;">{sample_ref_str}</td>
                </tr>
            """)

        # Build unmatched sample rows
        unmatched_rows = []
        if c_unmatched > 0:
            cr.execute(f"""
                SELECT am.id, am.name, am.ref, am.company_id
                FROM account_move am
                WHERE am.journal_id = %s {company_filter}
                  AND am.move_type = 'entry'
                ORDER BY am.id DESC LIMIT 50;
            """, params_base)
            matched_set = set(move_ids)
            unmatched_candidates = [r for r in cr.fetchall() if r[0] not in matched_set][:6]

            for r in unmatched_candidates:
                mname, mref, mcom = r[1] or "", r[2] or "", r[3]
                if not mref.strip():
                    reason = '<span style="background-color: #6c757d; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">Blank Reference</span>'
                else:
                    cand_name = re.sub(r'^(?:Revaluation of |Reversal of )\s*', '', mref, flags=re.I).split(" (")[0].split(" - ")[0].split(": ")[0].strip()
                    if not cand_name:
                        cand_name = mref.strip()
                    cr.execute("""
                        SELECT id, company_id, move_type FROM account_move 
                        WHERE (name = %s OR (ref IS NOT NULL AND TRIM(ref) != '' AND ref = %s))
                          AND move_type != 'entry' 
                        ORDER BY id DESC LIMIT 1;
                    """, [cand_name, cand_name])
                    b_row = cr.fetchone()
                    if not b_row:
                        reason = f'<span style="background-color: #fd7e14; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">Bill/Invoice Not Found: {cand_name}</span>'
                    elif b_row[1] == mcom:
                        reason = '<span style="background-color: #0dcaf0; color: black; padding: 2px 6px; border-radius: 3px; font-size: 11px;">Already in Document Company</span>'
                    else:
                        reason = '<span style="background-color: #6c757d; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">Excluded</span>'

                unmatched_rows.append(f"""
                    <tr>
                        <td style="padding: 6px; border: 1px solid #ddd;">{mname}</td>
                        <td style="padding: 6px; border: 1px solid #ddd; color: #555;">{mref or '<em>(blank)</em>'}</td>
                        <td style="padding: 6px; border: 1px solid #ddd;">{reason}</td>
                    </tr>
                """)

        summary_parts = [
            f"""
            <div class="alert alert-info" style="margin-bottom: 12px; font-size: 13px;">
                <strong>📊 Total Entries (move_type='entry'):</strong> {c_total} &nbsp;|&nbsp;
                <strong style="color: #2e7d32;">✅ Matched to Swap:</strong> {c_entries} entries ({c_lines} items) &nbsp;|&nbsp;
                <strong style="color: #d32f2f;">⚠️ Not Matched:</strong> {c_unmatched} records
            </div>
            """
        ]

        if html_rows:
            summary_parts.append(f"""
                <h6 style="color: #2e7d32; margin-top: 8px;"><strong>✅ Matched Records Breakdown (Ready to Swap):</strong></h6>
                <table class="table table-bordered table-sm" style="width: 100%; border-collapse: collapse; margin-bottom: 12px;">
                    <thead style="background-color: #e8f5e9;">
                        <tr>
                            <th style="padding: 8px; border: 1px solid #ddd;">Target Branch Company (from Bill/Note)</th>
                            <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">Entries to Swap</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">Document Type</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">Matched Document Number</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">Sample Entry Ref</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(html_rows)}
                    </tbody>
                </table>
            """)
        else:
            summary_parts.append("""
                <div class="alert alert-warning" style="margin-top: 10px;">
                    <strong>No journal entries found in this journal matching any Vendor Bills, Invoices, Credit Notes, or Debit Notes with different companies.</strong>
                </div>
            """)

        if unmatched_rows:
            summary_parts.append(f"""
                <h6 style="color: #6c757d; margin-top: 12px;"><strong>⚠️ Sample Not Matched Records ({c_unmatched} total):</strong></h6>
                <table class="table table-bordered table-sm" style="width: 100%; border-collapse: collapse; font-size: 12px;">
                    <thead style="background-color: #f8f9fa;">
                        <tr>
                            <th style="padding: 6px; border: 1px solid #ddd;">Entry Name</th>
                            <th style="padding: 6px; border: 1px solid #ddd;">Reference</th>
                            <th style="padding: 6px; border: 1px solid #ddd;">Reason Not Matched</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(unmatched_rows)}
                    </tbody>
                </table>
            """)

        summary_html = "".join(summary_parts)

        self.write({
            "count_total_entries": c_total,
            "count_matched_entries": c_entries,
            "count_unmatched_entries": c_unmatched,
            "count_matched_lines": c_lines,
            "match_summary": summary_html,
            "match_type": "bill",
            "state": "fetched",
        })

        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_reassign_by_bill(self):
        """Step 2 (Bill / Note): Swap company on matched journal entries and items to the company set on their matching Bill / Invoice / Note."""
        self.ensure_one()
        matches = self._find_bill_matches()
        if not matches:
            raise UserError(_("No matching journal entries found to reassign."))

        self._ensure_transferred_columns_exist()

        cr = self.env.cr
        # Group move_ids by target_company_id
        company_moves = defaultdict(list)
        for mid, data in matches.items():
            company_moves[data["target_company_id"]].append(mid)

        total_entries = 0
        total_lines = 0

        with cr.savepoint():
            for target_company_id, move_ids in company_moves.items():
                chunk_size = 1000
                for i in range(0, len(move_ids), chunk_size):
                    chunk_mids = tuple(move_ids[i:i + chunk_size])

                    # 1. Update account.move: swap company_id to the bill's company_id
                    cr.execute("""
                        UPDATE account_move 
                        SET company_id = %s, is_company_transferred = TRUE 
                        WHERE id IN %s;
                    """, [target_company_id, chunk_mids])

                    # 2. Update account.move.line: swap company_id to the bill's company_id
                    cr.execute("""
                        UPDATE account_move_line 
                        SET company_id = %s, is_company_transferred = TRUE 
                        WHERE move_id IN %s;
                    """, [target_company_id, chunk_mids])

                    # 3. Update account.partial.reconcile where applicable
                    cr.execute("SELECT id FROM account_move_line WHERE move_id IN %s;", [chunk_mids])
                    aml_ids = [r[0] for r in cr.fetchall()]
                    if aml_ids:
                        aml_chunk_size = 1000
                        for j in range(0, len(aml_ids), aml_chunk_size):
                            aml_chunk = tuple(aml_ids[j:j + aml_chunk_size])
                            cr.execute("""
                                UPDATE account_partial_reconcile 
                                SET company_id = %s, is_company_transferred = TRUE 
                                WHERE debit_move_id IN %s OR credit_move_id IN %s;
                            """, [target_company_id, aml_chunk, aml_chunk])

                    total_entries += len(chunk_mids)
                    total_lines += len(aml_ids)

        self.env.invalidate_all()
        self.write({"state": "done"})

        msg = _(
            "Successfully swapped company on %(count)s Journal Entries (%(lines)s items) to their matching Bills / Invoices / Notes' companies across %(comps)s branch(es).",
            count=total_entries,
            lines=total_lines,
            comps=len(company_moves),
        )

        # Create persistent audit logs for each target branch company
        for target_company_id, move_ids in company_moves.items():
            comp_rec = self.env["res.company"].browse(target_company_id)
            comp_name = comp_rec.display_name if comp_rec.exists() else f"Company ID {target_company_id}"
            src_name = self.source_company_id.display_name if self.source_company_id else _("Multiple / Original")
            self.env["journal.company.reassignment.log"].sudo().create({
                "journal_id": self.journal_id.id,
                "source_company_id": self.source_company_id.id if self.source_company_id else False,
                "target_company_id": target_company_id,
                "action_type": "bill_match",
                "records_updated": len(move_ids),
                "status": "success",
                "summary": _("Swapped company on %(count)s Journal Entries in journal '%(j)s' (from %(src)s) to branch '%(com)s' based on matched Bill / Invoice / Note numbers.",
                             count=len(move_ids), j=self.journal_id.display_name, src=src_name, com=comp_name),
            })

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Bill / Invoice Match Company Swap Completed"),
                "message": msg,
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

