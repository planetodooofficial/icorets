# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class SaleCompanyReassignmentLog(models.Model):
    _name = "sale.company.reassignment.log"
    _description = "Sale Order Company Reassignment Audit Log"
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
    tool_id = fields.Many2one(
        "sale.company.reassignment.tool",
        string="Reassignment Tool",
        ondelete="cascade",
        readonly=True,
        index=True,
    )
    source_company_id = fields.Many2one(
        "res.company",
        string="Source Company",
        readonly=True,
    )
    target_company_id = fields.Many2one(
        "res.company",
        string="Target / Assigned Company",
        readonly=True,
    )
    gstin_id = fields.Many2one(
        "res.partner",
        string="GSTIN Unit",
        readonly=True,
    )
    gst_code = fields.Char(
        string="GST Code",
        readonly=True,
    )
    action_type = fields.Selection(
        [
            ("all", "All Models (Complete Pipeline)"),
            ("sale_order", "Sale Orders"),
            ("sale_order_line", "Sale Order Lines"),
            ("stock_picking", "Delivery Pickings"),
            ("stock_picking_by_type", "Stock Pickings by Operation Type"),
            ("stock_move", "Stock Moves & Lines"),
            ("account_move", "Invoices & Entries"),
            ("account_move_line", "Invoice Lines & Items"),
            ("account_payment", "Payments & Reconciliations"),
        ],
        string="Target Action / Model",
        readonly=True,
    )
    records_updated = fields.Integer(
        string="Records Updated",
        readonly=True,
    )
    status = fields.Selection(
        [
            ("success", "Success"),
            ("nothing_to_update", "Nothing to Update"),
            ("failed", "Failed / Error"),
        ],
        string="Status",
        default="success",
        readonly=True,
        index=True,
    )
    summary = fields.Text(
        string="Execution Summary",
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == _("New"):
                vals["name"] = f"SO-LOG/{fields.Datetime.now().strftime('%Y%m%d-%H%M%S')}"
        return super().create(vals_list)
