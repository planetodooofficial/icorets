# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PurchaseCompanyReassignmentLog(models.Model):
    _name = "purchase.company.reassignment.log"
    _description = "Purchase Order Company Reassignment Audit Log"
    _order = "execution_date desc, id desc"

    name = fields.Char(
        string="Log Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code("purchase.company.reassignment.log") or "PLOG-NEW",
    )
    tool_id = fields.Many2one(
        comodel_name="purchase.company.reassignment.tool",
        string="Reassignment Session",
        ondelete="cascade",
        index=True,
    )
    source_company_id = fields.Many2one(
        comodel_name="res.company",
        string="Source Company",
        readonly=True,
    )
    target_company_id = fields.Many2one(
        comodel_name="res.company",
        string="Target Company",
        readonly=True,
    )
    gstin_id = fields.Many2one(
        comodel_name="res.partner",
        string="GSTIN Partner",
        readonly=True,
    )
    gst_code = fields.Char(
        string="GST Code",
        readonly=True,
    )
    action_type = fields.Selection(
        selection=[
            ("all", "Entire Pipeline"),
            ("purchase_order", "Purchase Orders"),
            ("purchase_order_line", "Purchase Order Lines"),
            ("stock_picking", "Incoming Receipts"),
            ("stock_move", "Stock Moves & Lines"),
            ("account_move", "Vendor Bills"),
            ("account_move_line", "Bill Lines"),
            ("account_payment", "Payments & Bank Transactions"),
        ],
        string="Action Type",
        readonly=True,
        required=True,
        default="all",
    )
    records_updated = fields.Integer(
        string="Records Updated",
        readonly=True,
        default=0,
    )
    execution_date = fields.Datetime(
        string="Execution Timestamp",
        readonly=True,
        default=fields.Datetime.now,
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Executed By",
        readonly=True,
        default=lambda self: self.env.user,
    )
    status = fields.Selection(
        selection=[
            ("success", "Success"),
            ("nothing_to_update", "Nothing to Update"),
            ("failed", "Failed"),
        ],
        string="Status",
        readonly=True,
        default="success",
    )
    summary = fields.Text(
        string="Execution Summary",
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "PLOG-NEW":
                vals["name"] = self.env["ir.sequence"].next_by_code("purchase.company.reassignment.log") or f"PLOG-{fields.Datetime.now().strftime('%Y%m%d%H%M%S')}"
        return super().create(vals_list)
