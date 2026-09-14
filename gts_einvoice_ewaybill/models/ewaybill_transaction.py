# -*- coding: utf-8 -*-
from odoo import fields, models


class EwaybillType(models.Model):
    _name = "l10n.in.ewaybill.type"
    _description = "eWaybill Document Type"

    name = fields.Char("Document Type")
    code = fields.Char("Code")
    allowed_in_supply_type = fields.Selection(
        [
            ("both", "Incoming and Outgoing"),
            ("O", "Outgoing"),
            ("I", "Incoming"),
        ],
        string="Allowed in supply type",
    )
    allowed_in_document = fields.Selection(
        [("invoice", "Invoice"), ("stock", "Stock")], string="Allowed in Document"
    )
    active = fields.Boolean("Active", default=True)


class EwaybillTransaction(models.Model):
    _name = "l10n.in.ewaybill.transaction"
    _description = "eWaybill Transaction"

    name = fields.Char(string="Ewaybill Number")
    ewaybill_date = fields.Date(string="Ewaybill Date")
    valid_upto = fields.Datetime(string="Valid Until")
    status = fields.Selection(
        [("active", "Active"), ("cancelled", "Cancelled")],
        string="Status",
        default="active",
    )
    move_id = fields.Many2one("account.move", string="Invoice")
    picking_id = fields.Many2one("stock.picking", string="Transfer")
    cancel_reason = fields.Selection(
        [
            ("1", "Duplicate"),
            ("2", "Data Entry Error"),
            ("3", "Order Cancelled"),
            ("4", "Others"),
        ],
        string="Cancel Reason",
    )
    cancel_remarks = fields.Char(string="Cancel Remarks")
