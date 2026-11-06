# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class WarehouseGstCompanyMatchWizard(models.TransientModel):
    _name = "warehouse.gst.company.match.wizard"
    _description = "Warehouse GST Company Match Wizard"

    warehouse_ids = fields.Many2many(
        "stock.warehouse",
        string="Warehouses to Process",
        required=True,
    )
    preserve_history = fields.Boolean(
        string="Preserve Historical Transactions",
        default=True,
        help="Safely preserve completed pickings, stock moves, and valuation layers as-is without rewriting them.",
    )
    state = fields.Selection([
        ("draft", "Draft"),
        ("done", "Completed"),
    ], default="draft", readonly=True)

    total_processed = fields.Integer(string="Total Warehouses Processed", readonly=True)
    total_success = fields.Integer(string="Successfully Updated", readonly=True)
    total_already_matched = fields.Integer(string="Already Matched", readonly=True)
    total_skipped = fields.Integer(string="Skipped Warehouses", readonly=True)
    total_failed = fields.Integer(string="Failed Warehouses", readonly=True)

    result_summary = fields.Text(string="Execution Summary", readonly=True)
    persistent_log_id = fields.Many2one(
        "warehouse.gst.assignment.log",
        string="Saved Audit Log",
        readonly=True,
    )
    line_ids = fields.One2many(
        "warehouse.gst.company.match.wizard.line",
        "wizard_id",
        string="Detailed Processing Results",
        readonly=True,
    )

    def action_reset(self):
        """Reset wizard to draft state for another run."""
        self.ensure_one()
        self = self.sudo()
        self.line_ids.unlink()
        self.write({
            "state": "draft",
            "total_processed": 0,
            "total_success": 0,
            "total_already_matched": 0,
            "total_skipped": 0,
            "total_failed": 0,
            "result_summary": False,
            "persistent_log_id": False,
        })
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }

    def action_view_persistent_log(self):
        """Open the persistent audit log created by this wizard run."""
        self.ensure_one()
        if not self.persistent_log_id:
            return
        return {
            "type": "ir.actions.act_window",
            "name": _("Audit Log: %s", self.persistent_log_id.name),
            "res_model": "warehouse.gst.assignment.log",
            "res_id": self.persistent_log_id.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_process(self):
        """Process warehouses in batch, directly assigning branch companies in database via direct SQL and logging results.
        Runs with superuser context to bypass multi-company record rule restrictions.
        """
        self.ensure_one()
        self = self.sudo()
        self.line_ids.unlink()

        total_processed = 0
        total_success = 0
        total_already_matched = 0
        total_skipped = 0
        total_failed = 0

        lines_vals = []
        log_entries = []

        for warehouse in self.warehouse_ids.sudo():
            total_processed += 1
            warehouse = warehouse.sudo()
            partner = warehouse.partner_id.sudo() if warehouse.partner_id else False
            code = warehouse._get_partner_gst_code()
            current_com = warehouse.company_id.sudo()
            destination = False

            if not code:
                total_skipped += 1
                msg = _("Warehouse partner '%(partner)s' does not have a GST code (partner_id.gst_code is empty).",
                        partner=partner.display_name if partner else _("None"))
                lines_vals.append({
                    "warehouse_id": warehouse.id,
                    "partner_id": partner.id if partner else False,
                    "gst_code": False,
                    "current_company_id": current_com.id,
                    "target_company_id": False,
                    "status": "skipped",
                    "message": msg,
                    "history_summary": _("Skipped - No GST code"),
                })
                log_entries.append(f"[SKIPPED] {warehouse.display_name}: {msg}")
                continue

            try:
                # 1. Resolve destination branch first
                destination, is_already_matched = warehouse._find_destination_branch_by_gst()
                destination = destination.sudo()

                if is_already_matched:
                    total_already_matched += 1
                    msg = _("Already assigned to destination branch '%(company)s' (GST Code: %(code)s). No change needed.",
                            company=current_com.display_name, code=code)
                    lines_vals.append({
                        "warehouse_id": warehouse.id,
                        "partner_id": partner.id if partner else False,
                        "gst_code": code,
                        "current_company_id": current_com.id,
                        "target_company_id": current_com.id,
                        "status": "already_matched",
                        "message": msg,
                        "history_summary": _("Already matched"),
                    })
                    log_entries.append(f"[ALREADY MATCHED] {warehouse.display_name}: {msg}")
                    continue

                # 2. Inspect exclusive configuration records and validate via direct SQL
                (
                    target_com,
                    already_matched_flag,
                    locations,
                    picking_types,
                    rules,
                    orderpoints,
                    history_summary,
                ) = warehouse._prepare_gst_company_match(allow_history=self.preserve_history)

                loc_count = len(locations)
                pt_count = len(picking_types)
                r_count = len(rules)
                op_count = len(orderpoints) if orderpoints else 0

                # Reassign warehouse directly in the database
                with self.env.cr.savepoint():
                    warehouse._reassign_warehouse_to_company(destination)

                total_success += 1
                msg = _(
                    "PERMANENTLY UPDATED: Changed company from '%(old_com)s' to '%(new_com)s' (GST Code: %(code)s). "
                    "Reassigned: %(loc)s locations, %(types)s operation types, "
                    "%(rules)s stock rules, %(op)s reordering rules.",
                    new_com=destination.display_name,
                    old_com=current_com.display_name,
                    code=code,
                    loc=loc_count,
                    types=pt_count,
                    rules=r_count,
                    op=op_count,
                )
                lines_vals.append({
                    "warehouse_id": warehouse.id,
                    "partner_id": partner.id if partner else False,
                    "gst_code": code,
                    "current_company_id": current_com.id,
                    "target_company_id": destination.id,
                    "status": "success",
                    "message": msg,
                    "locations_count": loc_count,
                    "picking_types_count": pt_count,
                    "rules_count": r_count,
                    "orderpoints_count": op_count,
                    "history_summary": history_summary,
                })
                log_entries.append(f"[SUCCESS - UPDATED] {warehouse.display_name}: {msg}")

            except Exception as exc:
                total_failed += 1
                error_msg = str(exc)
                lines_vals.append({
                    "warehouse_id": warehouse.id,
                    "partner_id": partner.id if partner else False,
                    "gst_code": code,
                    "current_company_id": current_com.id,
                    "target_company_id": destination.id if destination else False,
                    "status": "failed",
                    "message": error_msg,
                    "history_summary": _("Failed: %s") % error_msg,
                })
                log_entries.append(f"[FAILED] {warehouse.display_name}: {error_msg}")

        # Construct summary banner
        banner_header = [
            "=======================================================================",
            "MODE: LIVE EXECUTION",
            "✅ DATABASE PERMANENTLY UPDATED!",
            "Warehouse company ownership and configuration records were updated.",
            "=======================================================================",
        ]

        summary_lines = banner_header + [
            f"Total Warehouses Evaluated: {total_processed}",
            f"Ready to Update / Updated:  {total_success}",
            f"Already Matched:            {total_already_matched}",
            f"Skipped (No GST Code):      {total_skipped}",
            f"Failed:                     {total_failed}",
            "",
            "Detailed Processing Logs:",
        ]
        summary_lines.extend(log_entries)
        full_summary_text = "\n".join(summary_lines)

        # Create persistent audit log so tracking is never lost
        persistent_log = False
        try:
            persistent_log = self.env["warehouse.gst.assignment.log"].sudo().create({
                "source": "wizard",
                "total_processed": total_processed,
                "total_success": total_success,
                "total_already_matched": total_already_matched,
                "total_skipped": total_skipped,
                "total_failed": total_failed,
                "summary": full_summary_text,
                "line_ids": [
                    (0, 0, {
                        "warehouse_id": val["warehouse_id"],
                        "partner_id": val["partner_id"],
                        "gst_code": val["gst_code"],
                        "src_company_id": val["current_company_id"],
                        "dest_company_id": val["target_company_id"],
                        "status": val["status"],
                        "message": val["message"],
                        "history_summary": val.get("history_summary", ""),
                        "locations_count": val.get("locations_count", 0),
                        "picking_types_count": val.get("picking_types_count", 0),
                        "rules_count": val.get("rules_count", 0),
                        "orderpoints_count": val.get("orderpoints_count", 0),
                    })
                    for val in lines_vals
                ],
            })
        except Exception:
            persistent_log = False

        self.write({
            "state": "done",
            "total_processed": total_processed,
            "total_success": total_success,
            "total_already_matched": total_already_matched,
            "total_skipped": total_skipped,
            "total_failed": total_failed,
            "result_summary": full_summary_text,
            "persistent_log_id": persistent_log.id if persistent_log else False,
            "line_ids": [(0, 0, vals) for vals in lines_vals],
        })

        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }


class WarehouseGstCompanyMatchWizardLine(models.TransientModel):
    _name = "warehouse.gst.company.match.wizard.line"
    _description = "Warehouse GST Company Match Line"

    wizard_id = fields.Many2one(
        "warehouse.gst.company.match.wizard",
        string="Wizard",
        ondelete="cascade",
    )
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse", readonly=True)
    partner_id = fields.Many2one("res.partner", string="Contact", readonly=True)
    gst_code = fields.Char(string="GST Code", readonly=True)
    current_company_id = fields.Many2one("res.company", string="Current Company", readonly=True)
    target_company_id = fields.Many2one("res.company", string="Target Company", readonly=True)
    status = fields.Selection([
        ("success", "Done (Updated)"),
        ("already_matched", "Already Matched"),
        ("skipped", "Skipped (No GST Code)"),
        ("failed", "Failed"),
    ], string="Status", readonly=True)
    is_done = fields.Boolean(
        string="Is Done",
        compute="_compute_is_done",
        help="Indicates whether this warehouse assignment was successfully completed or already matched.",
    )
    message = fields.Text(string="Details / Reason", readonly=True)
    history_summary = fields.Char(string="History Preserved", readonly=True)
    locations_count = fields.Integer(string="Locations", readonly=True)
    picking_types_count = fields.Integer(string="Op Types", readonly=True)
    rules_count = fields.Integer(string="Stock Rules", readonly=True)
    orderpoints_count = fields.Integer(string="Reorder Rules", readonly=True)

    @api.depends("status")
    def _compute_is_done(self):
        for line in self:
            line.is_done = line.status in ("success", "already_matched")
