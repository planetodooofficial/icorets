from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = "stock.move"

    missing_valuation = fields.Boolean(string="Missing Valuation", default=False)
