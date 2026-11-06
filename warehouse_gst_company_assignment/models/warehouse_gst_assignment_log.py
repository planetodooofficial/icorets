# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class WarehouseGstAssignmentLog(models.Model):
    _name = "warehouse.gst.assignment.log"
    _description = "Warehouse GST Company Assignment Log"
    _order = "execution_date desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
    )
    execution_date = fields.Datetime(
        string="Execution Date",
        default=fields.Datetime.now,
        readonly=True,
        index=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Executed By",
        default=lambda self: self.env.user,
        readonly=True,
    )
    source = fields.Selection(
        [
            ("single", "Warehouse Form (Single)"),
            ("wizard", "Mass Batch Wizard"),
        ],
        string="Trigger Source",
        default="wizard",
        readonly=True,
        required=True,
    )
    total_processed = fields.Integer(string="Total Warehouses Evaluated", readonly=True)
    total_success = fields.Integer(string="Successfully Updated", readonly=True)
    total_already_matched = fields.Integer(string="Already Matched", readonly=True)
    total_skipped = fields.Integer(string="Skipped (No GST Code)", readonly=True)
    total_failed = fields.Integer(string="Failed (Errors / Safety)", readonly=True)

    summary = fields.Text(string="Execution Summary", readonly=True)
    line_ids = fields.One2many(
        "warehouse.gst.assignment.log.line",
        "log_id",
        string="Itemized Results",
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == _("New"):
                vals["name"] = f"GST-LOG/{fields.Datetime.now().strftime('%Y%m%d-%H%M%S')}"
        return super().create(vals_list)


class WarehouseGstAssignmentLogLine(models.Model):
    _name = "warehouse.gst.assignment.log.line"
    _description = "Warehouse GST Company Assignment Log Line"
    _order = "id desc"

    log_id = fields.Many2one(
        "warehouse.gst.assignment.log",
        string="Assignment Log",
        ondelete="cascade",
        required=True,
        index=True,
    )
    execution_date = fields.Datetime(
        string="Execution Date",
        related="log_id.execution_date",
        store=True,
        readonly=True,
        index=True,
    )
    warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Warehouse",
        readonly=True,
        index=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Warehouse Contact",
        readonly=True,
    )
    gst_code = fields.Char(string="GST Code", readonly=True)
    src_company_id = fields.Many2one(
        "res.company",
        string="Previous Company",
        readonly=True,
    )
    dest_company_id = fields.Many2one(
        "res.company",
        string="Target / Assigned Company",
        readonly=True,
    )
    status = fields.Selection(
        [
            ("success", "Done (Updated)"),
            ("already_matched", "Already Matched"),
            ("skipped", "Skipped (No GST Code)"),
            ("failed", "Failed"),
        ],
        string="Status",
        required=True,
        readonly=True,
        index=True,
    )
    is_done = fields.Boolean(
        string="Is Done",
        compute="_compute_is_done",
        store=True,
        index=True,
        help="Indicates whether this warehouse company assignment was successfully done or already matched.",
    )
    message = fields.Text(string="Details / Reason / Error", readonly=True)
    history_summary = fields.Char(string="History Preserved", readonly=True)
    locations_count = fields.Integer(string="Locations", readonly=True)
    picking_types_count = fields.Integer(string="Operation Types", readonly=True)
    rules_count = fields.Integer(string="Stock Rules", readonly=True)
    orderpoints_count = fields.Integer(string="Reorder Rules", readonly=True)

    @api.depends("status")
    def _compute_is_done(self):
        for line in self:
            line.is_done = line.status in ("success", "already_matched")
