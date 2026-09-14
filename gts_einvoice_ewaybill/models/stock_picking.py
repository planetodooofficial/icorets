# -*- coding: utf-8 -*-
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # E-Waybill Fields
    l10n_in_ewaybill_service_id = fields.Many2one('po.ewaybill.service', string="Ewaybill Service", copy=False)
    l10n_in_ewaybill_transaction_ids = fields.One2many(
        "l10n.in.ewaybill.transaction", "picking_id", string="Ewaybill Transactions"
    )
    l10n_in_ewaybill_type_id = fields.Many2one("l10n.in.ewaybill.type", string="Document Type")
    l10n_in_distance = fields.Integer(string="Distance (Km)")
    l10n_in_mode = fields.Selection(
        [("1", "Road"), ("2", "Rail"), ("3", "Air"), ("4", "Ship")],
        string="Transportation Mode",
        default="1",
    )
    l10n_in_vehicle_no = fields.Char(string="Vehicle Number")
    l10n_in_vehicle_type = fields.Selection(
        [("R", "Regular"), ("O", "Over Dimensional Cargo")],
        string="Vehicle Type",
        default="R",
    )
    l10n_in_transporter_id = fields.Many2one("res.partner", string="Transporter")
    l10n_in_transporter_doc_no = fields.Char(string="Transporter Doc No")
    l10n_in_transporter_doc_date = fields.Date(string="Transporter Doc Date")
